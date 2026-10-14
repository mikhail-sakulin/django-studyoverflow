"""
WebSocket-консьюмеры.
"""

import json
import logging
from importlib import import_module

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth import SESSION_KEY

from users.services.online import async_set_user_online


logger = logging.getLogger(__name__)


# - import_module("...") - стандартная функция Python, которая по строке с путем
#   импортирует модуль и возвращает его;
# - settings.SESSION_ENGINE - строка с путем к модулю, по умолчанию
#   "django.contrib.sessions.backends.db";
# - .SessionStore - класс из полученного модуля.
#
# Класс для работы с хранилищем сессий, которое выбрано в настройках. По умолчанию БД, в
# проекте не переопределялся.
SessionStore = import_module(settings.SESSION_ENGINE).SessionStore

# Код закрытия WebSocket из-за завершения сессии. Выбирается из диапазона 4000-4999,
# который могут использовать приложения для своих нужд. При этом 1000 - стандартный код
# закрытия WebSocket.
WS_CLOSE_SESSION_ENDED = 4401


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Консьюмер для асинхронной доставки уведомлений и отслеживания онлайн-статуса.
    """

    async def connect(self):
        """
        Регистрирует канал в группе пользователя и обновляет статус онлайн.
        """
        if not self.scope["user"].is_authenticated:
            await self.close()
            return

        self.group_name = f"user_{self.scope['user'].pk}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # При использовании синхронной функции set_user_online нужно оборачивать ее в sync_to_async.
        #
        # set_user_online не работает с Django ORM, поэтому вызовы можно выполнять не в одном
        # потоке, как было бы при thread_sensitive=True по умолчанию, а в разных потоках из пула.
        # await sync_to_async(set_user_online, thread_sensitive=False)(self.scope["user"].pk)

        await async_set_user_online(self.scope["user"].pk)

    async def disconnect(self, code):
        """
        Отключает текущий канал от группы рассылки,
        прекращая получение уведомлений для данной сессии.
        """
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def receive(self, text_data=None, bytes_data=None):
        """
        Получение сообщений от клиента по WebSocket.

        Клиент может присылать heartbeat, чтобы сказать, что он онлайн. Heartbeat принимается
        только если сессия пользователя все еще существует. Если пользователь вышел из
        аккаунта в другой вкладке браузера, то соединение закрывается.
        """
        if text_data:
            # Невалидное сообщение от клиента обрабатывается, чтобы клиент не был отключен из-за
            # ошибки обработки сообщения, и логируется.
            try:
                data = json.loads(text_data)
            except json.JSONDecodeError:
                logger.warning(
                    "Невалидный JSON в WebSocket-сообщении.",
                    extra={
                        "user_id": self.scope["user"].pk,
                        "event_type": "ws_invalid_json",
                        "payload_preview": text_data[:100],
                    },
                )
                return

            if not isinstance(data, dict):
                logger.warning(
                    "WebSocket-сообщение не является JSON-объектом.",
                    extra={
                        "user_id": self.scope["user"].pk,
                        "event_type": "ws_invalid_payload",
                        "payload_type": type(data).__name__,
                    },
                )
                return

            if data.get("type") == "heartbeat":
                # Проверка активной сессии
                if not await self._session_is_alive():
                    # Если сессия неактивна, то соединение закрывается с собственным кодом
                    await self.close(code=WS_CLOSE_SESSION_ENDED)
                    return

                await async_set_user_online(self.scope["user"].pk)

    async def notify(self, event):
        """
        Отправляет обновленные данные о счетчике уведомлений клиенту
        при получении события из группы.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "unread_notifications_count": event.get("unread_notifications_count", 0),
                    "update_list": event.get("update_list", True),
                    "reason": event.get("reason", "update"),
                }
            )
        )

    # Декоратор database_sync_to_async работает по аналогии с функцией sync_to_async. Он запускает
    # выполнение метода в отдельном потоке, так как синхронный вызов ORM из асинхронного кода
    # запрещен. В потоке, где выполняется синхронный вызов ORM, не должно быть event loop, иначе
    # вызовется исключение SynchronousOnlyOperation самим Django. Чтение сессии из БД является
    # синхронной операцией с Django ORM. Декоратор дополнительно очищает старые или сломанные
    # соединения с БД при окончании работы обернутого метода.
    #
    # По умолчанию thread_sensitive=True - используется один и тот же поток для выполнения
    # обернутого метода, не плодится много потоков и не исчерпывается пул соединений с БД,
    # который один на процесс, поток может использовать только одно соединение одновременно,
    # после чего оно возвращается в пул.
    @database_sync_to_async
    def _session_is_alive(self) -> bool:
        """
        Проверяет, что сессия все еще существует и в ней залогинен тот же пользователь,
        что и при подключении.

        scope["session"] не используется, так как значение закешировано при connect.
        Нельзя брать _auth_user_id из закешированного объекта:
            self.scope["session"].get(SESSION_KEY) == str(self.scope["user"].pk)
        """
        # Из scope["session"] используется только ключ сессии, который уникален
        # для каждой новой сессии и не меняется в течение соединения.
        session_key = self.scope["session"].session_key

        if not session_key:
            return False

        # Данные сессии читаются заново из БД по ключу сессии, достается _auth_user_id и
        # сравнивается с pk пользователя из scope.
        # SESSION_KEY - константа Django, равная "_auth_user_id".
        return SessionStore(session_key).get(SESSION_KEY) == str(self.scope["user"].pk)
