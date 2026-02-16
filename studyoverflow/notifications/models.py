from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


User = get_user_model()


class NotificationType(models.TextChoices):
    """
    Перечисление типов уведомлений.
    """

    LIKE_POST = "like_post", "Лайк поста"
    LIKE_COMMENT = "like_comment", "Лайк комментария"
    POST = "post_created", "Пост создан"
    COMMENT = "comment_post", "Комментарий к посту"
    REPLY = "reply_comment", "Ответ на комментарий"
    REGISTER = "user_register", "Регистрация пользователя"


class Notification(models.Model):
    """
    Модель уведомлений на различные события.

    Поля:
    - user (ForeignKey): Получатель уведомления.
    - actor (ForeignKey): Инициатор события (тот, кто совершил действие).
    - notification_type (CharField): Тип уведомления (LIKE_POST, COMMENT и т.д.).
    - content_type (ForeignKey): Ссылка на модель связанного объекта (Post, Comment и т.д.).
    - object_id (PositiveIntegerField): ID записи в связанной модели.
    - content_object (GenericForeignKey): Экземпляр связанного объекта.
    - message (CharField): Текстовое сообщение уведомления.
    - is_read (BooleanField): Флаг прочтения уведомления пользователем.
    - time_create (DateTimeField): Дата и время автоматической генерации записи.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Пользователь",
        help_text="Пользователь, которому адресовано уведомление",
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="actor_notifications",
        verbose_name="Инициатор",
        help_text="Пользователь, который совершил действие",
    )

    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        verbose_name="Тип",
        help_text="Тип уведомления",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Тип связанного объекта",
    )
    object_id = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="ID связанного объекта"
    )
    content_object = GenericForeignKey("content_type", "object_id")

    message = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Сообщение",
        help_text="Текстовое описание уведомления",
    )

    is_read = models.BooleanField(default=False, verbose_name="Статус")
    time_create = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-time_create"]
        indexes = [
            # Индекс для непрочитанных уведомлений пользователя:
            #   Notification.objects.filter(user=user, is_read=False)
            #       WHERE user_id = ? AND is_read = False
            models.Index(fields=["user", "is_read"]),
            # Индекс для получения всех уведомлений пользователя с сортировкой по дате создания:
            #   Notification.objects.filter(user=user).order_by('-time_create')
            #       WHERE user_id = ?
            #       ORDER BY time_create DESC
            models.Index(fields=["user", "-time_create"]),
        ]

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return f"{self.user} <- {self.actor}: {self.get_notification_type_display()}"
