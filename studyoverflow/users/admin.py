from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.safestring import mark_safe
from users.models import User


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

    def get_actions(self, request):
        """
        Ограничивает доступ к действиям с пользователями
        в зависимости от роли персонала в админ-панели.
        """
        actions = super().get_actions(request)

        if not self._can_block_users(request.user):
            actions.pop("block_users", None)
            actions.pop("unblock_users", None)

        return actions

    @admin.action(description="Заблокировать выбранных пользователей")
    def block_users(self, request, queryset):
        """
        Блокирует выбранных пользователей.
        """
        count = queryset.update(is_blocked=True, blocked_at=timezone.now(), blocked_by=request.user)
        self.message_user(request, f"Заблокировано {count} пользователей.")

    @admin.action(description="Разблокировать выбранных пользователей")
    def unblock_users(self, request, queryset):
        """
        Разблокирует выбранных пользователей.
        """
        count = queryset.update(is_blocked=False, blocked_at=None, blocked_by=None)
        self.message_user(request, f"Разблокировано {count} пользователей.")

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
        UserModel = get_user_model()  # noqa: N806
        return user.role in {UserModel.Role.ADMIN, UserModel.Role.MODERATOR}
