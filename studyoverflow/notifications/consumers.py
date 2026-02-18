"""
WebSocket-консьюмеры.
"""

import json

from channels.generic.websocket import AsyncWebsocketConsumer
from users.services import set_user_online


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Консьюмер для асинхронной доставки уведомлений и отслеживания онлайн-статуса.
    """

    async def connect(self):
        """
        Регистрирует канал в группе пользователя и обновляет статус онлайн.
        """
        if not self.scope["user"].is_authenticated:
            return await self.close()

        self.group_name = f"user_{self.scope['user'].id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        set_user_online(self.scope["user"].id)

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
                set_user_online(self.scope["user"].id)

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
                }
            )
        )
