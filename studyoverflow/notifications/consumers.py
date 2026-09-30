"""
WebSocket-консьюмеры.
"""

import json

from channels.generic.websocket import AsyncWebsocketConsumer

from users.services.online import async_set_user_online


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

        # При использовании синхронной функции set_user_online нужно оборачивает ее в sync_to_async.
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

        Клиент может присылать heartbeat, чтобы сказать, что он онлайн.
        """
        if text_data:
            data = json.loads(text_data)

            if data.get("type") == "heartbeat":
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
