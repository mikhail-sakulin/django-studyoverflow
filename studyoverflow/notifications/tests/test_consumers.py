import asyncio
from types import SimpleNamespace

import pytest
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser

from notifications.routing import websocket_urlpatterns


@pytest.fixture
def communicator_factory():
    """
    Фабрика для создания WebsocketCommunicator с переданным пользователем.

    WebsocketCommunicator - инструмент тестирования, предоставляемый библиотекой Channels,
    виртуальный WebSocket-клиент, аналог client для django views.
    """

    def _factory(user):
        # communicator - экземпляр WebsocketCommunicator с настройкой подключения
        communicator = WebsocketCommunicator(
            # Маршрутизатор приложения (список путей)
            URLRouter(websocket_urlpatterns),
            # конкретный путь, к которому виртуальный клиент будет подключаться
            "/ws/notifications/",
        )
        communicator.scope["user"] = user
        return communicator

    return _factory


@pytest.mark.asyncio
class TestNotificationConsumer:
    """Тестирование NotificationConsumer."""

    async def test_unauthenticated_connection_rejected(self, communicator_factory):
        """Анонимный пользователь не может подключиться."""
        communicator = communicator_factory(AnonymousUser())

        # connected, subprotocol; subprotocol - подпротокол, который запрашивает WebSocket-клиент,
        # используется редко
        connected, _ = await communicator.connect()

        assert connected is False

    async def test_authenticated_connection_success(self, mocker, communicator_factory):
        """Авторизованный пользователь успешно устанавливает WebSocket подключение."""
        mock_set_online = mocker.patch("notifications.consumers.set_user_online")

        user = SimpleNamespace(pk=1, is_authenticated=True)
        communicator = communicator_factory(user)

        connected, _ = await communicator.connect()

        assert connected is True
        mock_set_online.assert_called_once_with(1)

        await communicator.disconnect()

    async def test_receive_heartbeat_updates_online(self, mocker, communicator_factory):
        """Heartbeat обновляет онлайн-статус пользователя."""
        mock_set_online = mocker.patch("notifications.consumers.set_user_online")

        user = SimpleNamespace(pk=1, is_authenticated=True)
        communicator = communicator_factory(user)

        connected, _ = await communicator.connect()
        assert connected is True

        mock_set_online.reset_mock()

        # .send_json_to - сериализует python-словарь в json-строку перед отправкой сообщения от
        # клиента на сервер;
        # "type": "heartbeat" - отправляемые данные, по которым сервер в .receive методе
        # выберет действие
        await communicator.send_json_to(
            {
                "type": "heartbeat",
            }
        )

        # Передается управление (чуть больше 0) в event loop,
        # чтобы таска консьюмера проснулась и выполнилась в цикле с максимальным ожиданием
        # не более 1 секунды, иначе вызывается исключение во время тестирования.
        for _ in range(200):
            if mock_set_online.called:
                break
            await asyncio.sleep(0.005)
        else:
            pytest.fail("set_user_online не был вызван")

        mock_set_online.assert_called_once_with(1)

        await communicator.disconnect()

    async def test_notify_event_sent_to_client(self, communicator_factory):
        """Событие notify отправляется клиенту."""
        user = SimpleNamespace(pk=1, is_authenticated=True)

        communicator = communicator_factory(user)

        connected, _ = await communicator.connect()
        assert connected is True

        channel_layer = get_channel_layer()

        # Отправка сообщения в группу, сервер (таска) реагирует на сообщение, так как подписан
        # на группу, и в методе .notify отправляет клиенту данные
        await channel_layer.group_send(
            f"user_{user.pk}",
            {
                "type": "notify",
                "unread_notifications_count": 5,
                "update_list": False,
            },
        )

        # Клиент принимает то, что сервер отправил
        response = await communicator.receive_json_from()

        # Проверка данных, полученных клиентом
        assert response == {
            "unread_notifications_count": 5,
            "update_list": False,
        }

        await communicator.disconnect()

    async def test_notify_default_values(self, communicator_factory):
        """Используются значения по умолчанию, если они отсутствуют в событии notify."""
        user = SimpleNamespace(pk=1, is_authenticated=True)

        communicator = communicator_factory(user)

        connected, _ = await communicator.connect()
        assert connected is True

        channel_layer = get_channel_layer()

        await channel_layer.group_send(
            f"user_{user.pk}",
            {
                "type": "notify",
            },
        )

        response = await communicator.receive_json_from()

        assert response == {
            "unread_notifications_count": 0,
            "update_list": True,
        }

        await communicator.disconnect()
