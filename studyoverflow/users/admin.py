from django.contrib import admin
from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    readonly_fields = (
        "groups",
        "user_permissions",
        "last_login",
        "date_joined",
        "is_staff",
        "is_superuser",
    )
