"""
Celery-задачи для фоновой асинхронной обработки данных пользователей.
"""

import logging
from typing import Optional

import requests
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from users.services.infrastructure import (
    delete_old_avatar_names,
    generate_avatar_small,
    get_cached_online_user_ids,
    get_counts_map,
    get_reputation_map,
)

from studyoverflow.celery import app


logger = logging.getLogger(__name__)


@app.task
def generate_and_save_avatars_small(user_pk):
    """
    Генерирует уменьшенные версии аватара пользователя.

    Создаёт набор уменьшенных изображений на основе аватара
    пользователя и сохраняет их в соответствующие поля модели.

    Используется после изменения аватара или регистрации пользователя.
    """
    User = get_user_model()  # noqa: N806

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.warning(
            f"Пользователь с pk={user_pk} не найден, avatar_small не будет сгенерирован.",
            extra={
                "user_pk": user_pk,
                "event_type": "generate_avatar_small_user_not_found",
            },
        )
        return

    update_fields_list = []

    for size_type, avatar_small in enumerate(user.get_small_avatar_fields(), start=1):
        avatar_small_name = generate_avatar_small(user, size_type=size_type)

        if avatar_small_name:
            setattr(user, avatar_small, avatar_small_name)
            update_fields_list.append(avatar_small)

    user.save(update_fields=update_fields_list)


@app.task
def delete_old_avatars_from_s3_storage(user_pk, avatar_names_for_delete: Optional[list] = None):
    """
    Удаляет устаревшие файлы аватаров пользователя из хранилища.

    Если передан список `avatar_names_for_delete`, удаляет только указанные
    файлы.

    Если список не передан, автоматически определяет устаревшие файлы,
    сравнивая текущее состояние модели пользователя с содержимым в хранилище.
    """
    User = get_user_model()  # noqa: N806

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.warning(
            f"Пользователь с pk={user_pk} не найден, avatar_small не будет сгенерирован.",
            extra={
                "user_pk": user_pk,
                "event_type": "generate_avatar_small_user_not_found",
            },
        )
        return

    if avatar_names_for_delete:
        files = [name for name in avatar_names_for_delete if name]
        if files:
            delete_old_avatar_names(files)
        return

    prefix_for_avatars = f"avatars/{user.pk}"

    _, files_in_avatars_dir = default_storage.listdir(prefix_for_avatars)

    avatars_names_list = [
        user.avatar.name,
    ]

    for avatar_small in user.get_small_avatar_fields():
        avatar_small_field = getattr(user, avatar_small)

        avatars_names_list.append(avatar_small_field.name)

    files_for_delete = [
        f"{prefix_for_avatars}/{file}"
        for file in files_in_avatars_dir
        if f"{prefix_for_avatars}/{file}" not in avatars_names_list
    ]

    delete_old_avatar_names(files_for_delete)


@app.task
def sync_online_users_to_db():
    """
    Записывает online-статус пользователей в БД (last_seen) из кеша.

    Получает список онлайн-пользователей из Redis и обновляет поле `last_seen` в БД.
    """
    User = get_user_model()  # noqa: N806

    user_ids = get_cached_online_user_ids()

    users = list(User.objects.filter(pk__in=user_ids))

    now = timezone.now()

    for user in users:
        user.last_seen = now

    User.objects.bulk_update(users, ["last_seen"])


@app.task
def sync_user_activity_counters(batch_size: int = 1000):
    """
    Пересчитывает и синхронизирует поля-счётчики пользователей.

    Обновляет:
    - количество постов (posts_count);
    - количество комментариев (comments_count);
    - репутацию (reputation).
    """
    # ленивый импорт
    from posts.models import Comment, Post

    User = get_user_model()  # noqa: N806

    posts_map = get_counts_map(Post, "author_id")
    comments_map = get_counts_map(Comment, "author_id")
    reputation_map = get_reputation_map(Post, Comment)

    users_to_update = []

    users_queryset = User.objects.only("id", "posts_count", "comments_count", "reputation")

    # Обновление батчами для оптимизации нагрузки на БД.
    for user in users_queryset.iterator(chunk_size=batch_size):
        new_posts_count = posts_map.get(user.id, 0)
        new_comments_count = comments_map.get(user.id, 0)
        new_reputation = reputation_map.get(user.id, 0)

        if (
            user.posts_count != new_posts_count
            or user.comments_count != new_comments_count
            or user.reputation != new_reputation
        ):

            user.posts_count = new_posts_count
            user.comments_count = new_comments_count
            user.reputation = new_reputation
            users_to_update.append(user)

        if len(users_to_update) >= batch_size:
            User.objects.bulk_update(
                users_to_update, ["posts_count", "comments_count", "reputation"]
            )
            users_to_update.clear()

    if users_to_update:
        User.objects.bulk_update(users_to_update, ["posts_count", "comments_count", "reputation"])


@app.task
def download_and_set_avatar(user_id: int, avatar_url: str):
    """
    Загружает аватар пользователя по переданному URL и сохраняет его в хранилище.

    Используется при регистрации через социальные сети.

    Выполняет:
    - загрузку файла;
    - валидацию;
    - сохранение файла в хранилище.
    """
    User = get_user_model()  # noqa: N806

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning(
            f"Пользователь с pk={user_id} не найден, avatar_small не будет сгенерирован.",
            extra={
                "user_pk": user_id,
                "event_type": "generate_avatar_small_user_not_found",
            },
        )
        return

    default_avatar = user._meta.get_field("avatar").get_default()
    if user.avatar and user.avatar.name != default_avatar:
        return

    try:
        response = requests.get(
            avatar_url,
            timeout=5,
        )
        response.raise_for_status()

        content = response.content

        file_to_save = ContentFile(content)
        file_to_save.name = "social_avatar.jpg"

        for validator in user._meta.get_field("avatar").validators:
            validator(file_to_save)

        user.avatar.save(
            file_to_save.name,
            file_to_save,
            save=True,
        )

    except ValidationError as e:
        logger.warning(
            f"Файл аватара для пользователя {user.username} не прошел валидацию.",
            extra={
                "user_id": user.pk,
                "username": user.username,
                "avatar_url": avatar_url,
                "error": str(e),
                "event_type": "download_and_set_avatar_validation_error",
            },
        )
        return

    except Exception as e:
        logger.error(
            f"Неожиданная ошибка при установке avatar пользователя {user.username}.",
            extra={
                "user_id": user.id,
                "username": user.username,
                "avatar_url": avatar_url,
                "error": str(e),
                "event_type": "download_and_set_avatar_unexpected_error",
            },
        )
        return


@app.task
def delete_files_from_storage_task(file_paths: list[str]):
    """
    Универсальная задача для удаления списка файлов из хранилища.

    Используется для асинхронной очистки файлов из хранилища, в том числе аватаров,
    после удаления пользователя или обновления изображений.
    """
    if file_paths:
        delete_old_avatar_names(file_paths)
