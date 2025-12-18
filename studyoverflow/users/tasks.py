from typing import Optional

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.utils import timezone
from users.services.infrastructure import (
    delete_old_avatar_names,
    generate_avatar_small,
    get_online_user_ids,
)

from studyoverflow.celery import app


@app.task
def generate_and_save_avatars_small(user_pk):
    User = get_user_model()  # noqa: N806

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        # Логирование
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
    User = get_user_model()  # noqa: N806

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        # Логирование
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
    Проверяет все ключи online_users:
    """
    User = get_user_model()  # noqa: N806

    user_ids = get_online_user_ids()

    users = list(User.objects.filter(pk__in=user_ids))

    now = timezone.now()

    for user in users:
        user.last_seen = now

    User.objects.bulk_update(users, ["last_seen"])
