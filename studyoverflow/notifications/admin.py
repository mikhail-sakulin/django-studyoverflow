from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.text import Truncator
from notifications.models import Notification
from users.models import User


class IsReadFilter(admin.SimpleListFilter):
    """
    Кастомный фильтр для фильтрации уведомлений по статусу прочтения (Да/Нет).
    """

    title = "Прочитано пользователем"
    parameter_name = "is_read_status"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(is_read=True)

        elif self.value() == "no":
            return queryset.filter(is_read=False)

        return queryset


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Конфигурация отображения и управления уведомлениями в админ-панели.
    """

    list_display = (
        "id",
        "user",
        "actor",
        "notification_type",
        "is_read_status",
        "time_create",
    )
    list_display_links = ("id", "user", "actor", "notification_type")
    list_filter = ["notification_type", IsReadFilter]
    search_fields = [
        "user__username",
        "actor__username",
    ]
    ordering = ["-time_create", "-id"]
    list_per_page = 15
    actions = ["make_is_read", "make_is_unread"]
    fields = [
        "id",
        "user",
        "actor",
        "notification_type",
        "content_type",
        "object_id",
        "short_content_object",
        "is_read",
        "time_create",
    ]
    readonly_fields = [
        "id",
        "user",
        "actor",
        "notification_type",
        "content_type",
        "object_id",
        "short_content_object",
        "time_create",
    ]

    def get_actions(self, request):
        """Ограничивает доступ к действиям на основе ролей пользователя."""
        actions = super().get_actions(request)

        if not self._can_do_actions(request.user):
            actions.pop("make_is_read", None)
            actions.pop("make_is_unread", None)

        return actions

    @admin.action(description="Отметить прочитанными")
    def make_is_read(self, request, queryset):
        """Устанавливает статус 'прочитано' для выбранных уведомлений."""
        count = queryset.update(is_read=True)
        self.message_user(request, f"{count} уведомлений отмечены прочитанными.")

    @admin.action(description="Отметить непрочитанными")
    def make_is_unread(self, request, queryset):
        """Снимает статус 'прочитано' для выбранных уведомлений."""
        count = queryset.update(is_read=False)
        self.message_user(request, f"{count} уведомлений отмечены непрочитанными.")

    @admin.display(description="Объект уведомления")
    def short_content_object(self, notification: Notification):
        """Возвращает укороченное строковое представление связанного объекта."""
        if not notification.content_object:
            return "—"
        return Truncator(str(notification.content_object)).chars(40, truncate="…")

    @admin.display(description="Прочитано пользователем", boolean=True)
    def is_read_status(self, notification: Notification):
        """
        Отображает статус прочтения в виде True/False в списке.

        Используется для переопределения description поля is_read.
        """
        return notification.is_read

    def _can_do_actions(self, user: User):
        """Проверяет наличие прав администратора или модератора для выполнения действий."""
        UserModel = get_user_model()  # noqa: N806
        return user.role in {UserModel.Role.ADMIN, UserModel.Role.MODERATOR}
