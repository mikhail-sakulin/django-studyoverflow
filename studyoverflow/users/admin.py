from typing import TYPE_CHECKING

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe

from users.services.moderation import block_user_service, unblock_user_service


if TYPE_CHECKING:
    from users.models import User
else:
    User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Конфигурация отображения и управления пользователями в админ-панели.
    """

    list_display = (
        "id",
        "username",
        "email",
        "user_avatar",
        "role",
        "is_social",
        "is_blocked",
        "reputation",
        "posts_count",
        "comments_count",
        "date_joined",
        "last_seen",
    )
    list_display_links = ("id", "username", "email")
    list_filter = ["role", "is_social", "is_blocked"]
    search_fields = [
        "username",
        "email",
    ]
    ordering = ["-id", "username"]
    list_per_page = 15
    actions = ["block_users", "unblock_users"]
    fields = (
        "id",
        "username",
        "email",
        "role",
        "groups",
        "is_staff",
        "is_superuser",
        "first_name",
        "last_name",
        "user_avatar",
        "avatar",
        "avatar_small_size1",
        "avatar_small_size2",
        "avatar_small_size3",
        "bio",
        "reputation",
        "posts_count",
        "comments_count",
        "is_social",
        "is_blocked",
        "blocked_at",
        "blocked_by",
        "date_birth",
        "date_joined",
        "last_seen",
    )
    readonly_fields = (
        "id",
        "groups",
        "is_staff",
        "is_superuser",
        "user_avatar",
        "avatar_small_size1",
        "avatar_small_size2",
        "avatar_small_size3",
        "posts_count",
        "comments_count",
        "is_social",
        "date_joined",
        "last_seen",
    )

    def message_user(
        self, request, message, level=messages.INFO, extra_tags="", fail_silently=False
    ):
        """
        Показывает сообщение пользователю в админке.

        Работает как стандартный ModelAdmin.message_user, но для сообщений уровня ERROR добавляет
        тег "error". Задается, потому что MESSAGE_TAGS в settings.py переопределяет тег ERROR на
        "danger", а в админке нет стилей для такого класса, ошибки отображались бы зелёными.
        """
        if level == messages.ERROR:
            extra_tags = f"{extra_tags} error".strip()
        super().message_user(request, message, level, extra_tags, fail_silently)

    @admin.action(description="Заблокировать выбранных пользователей", permissions=["block"])
    def block_users(self, request, queryset):
        """Блокирует выбранных пользователей через сервис."""
        self._apply_block_service(request, queryset, block_user_service, "Заблокировано")

    @admin.action(description="Разблокировать выбранных пользователей", permissions=["block"])
    def unblock_users(self, request, queryset):
        """Разблокирует выбранных пользователей через сервис."""
        self._apply_block_service(request, queryset, unblock_user_service, "Разблокировано")

    def has_block_permission(self, request) -> bool:
        """Проверка прав для @admin.action, нужен для permissions=["block"]."""
        return self._can_block_users(request.user)

    @admin.display(description="Аватар (изображение)", ordering="username")
    def user_avatar(self, user: User):
        """
        Отображает миниатюру аватара пользователя в списке.
        """
        if user.avatar:
            return mark_safe(f"<img src='{user.avatar.url}' width=50>")
        else:
            return "Без изображения"

    def _can_block_users(self, user: User):
        """
        Проверяет, имеет ли текущий пользователь право блокировать аккаунты.
        """
        return user.role in {User.Role.ADMIN, User.Role.MODERATOR}

    def _apply_block_service(self, request, queryset, service, done_label: str) -> None:
        """
        Применяет сервис блокировки/разблокировки к каждому выбранному пользователю при
        @admin.action block_users и unblock_users.

        Вызов сервиса выполняется для каждого пользователя отдельно, чтобы проверка
        иерархии ролей (can_moderate), сохранение через save() и логирование
        отрабатывали так же, как и вне админки. Ошибки по отдельным пользователям
        не прерывают обработку остальных.
        """
        done = 0

        for target in queryset:
            try:
                # source="admin" попадает в лог
                changed, message = service(request.user, target, source="admin")
            except PermissionDenied as e:
                self.message_user(request, f"{target.username}: {e}", level=messages.ERROR)
                continue

            if changed:
                done += 1
            else:
                # Если сервис вернул False, значит пользователь уже в нужном состоянии
                self.message_user(request, message, level=messages.WARNING)

        if done:
            self.message_user(request, f"{done_label} пользователей: {done}.")
