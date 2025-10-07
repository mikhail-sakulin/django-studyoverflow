from django.contrib.auth.models import AbstractUser
from django.db import models
from users.services.infrastructure import avatar_upload_to


class User(AbstractUser):
    avatar = models.ImageField(
        upload_to=avatar_upload_to,
        blank=True,
        default="avatars/default_avatar.jpg",
        verbose_name="Аватар",
    )
    bio = models.TextField(blank=True, verbose_name="Информация о пользователе")
    reputation = models.IntegerField(blank=True, default=0, verbose_name="Репутация")

    date_birth = models.DateTimeField(blank=True, null=True, verbose_name="Дата рождения")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    time_update = models.DateTimeField(auto_now=True, verbose_name="Время изменения")

    def __str__(self):
        return self.username

    class Meta:
        ordering = ["username"]
