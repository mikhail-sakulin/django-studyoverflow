from typing import Optional

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from users.services.infrastructure import (
    delete_old_avatar_names,
    generate_avatar_small,
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

    # Создание avatar_small и получение имен файлов
    avatar_small_size1_name = generate_avatar_small(user, size_type=1)
    avatar_small_size2_name = generate_avatar_small(user, size_type=2)
    avatar_small_size3_name = generate_avatar_small(user, size_type=3)

    update_fields_list = []

    # Если avatar_small_name == False, значит avatar_small не создается
    if avatar_small_size1_name:
        user.avatar_small_size1.name = avatar_small_size1_name
        update_fields_list.append("avatar_small_size1")

    if avatar_small_size2_name:
        user.avatar_small_size2.name = avatar_small_size2_name
        update_fields_list.append("avatar_small_size2")

    if avatar_small_size3_name:
        user.avatar_small_size3.name = avatar_small_size3_name
        update_fields_list.append("avatar_small_size3")

    user.save(skip_celery_task=True, update_fields=update_fields_list)


@app.task
def delete_old_avatars_from_s3_storage(user_pk, old_avatar_names: Optional[list] = None):
    User = get_user_model()  # noqa: N806

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        # Логирование
        return

    if old_avatar_names is not None:
        files = [name for name in old_avatar_names if name]
        if files:
            delete_old_avatar_names(files)
        return

    prefix_for_avatars = f"avatars/{user.pk}"

    _, files_in_avatars_dir = default_storage.listdir(prefix_for_avatars)

    avatars_names_list = [
        user.avatar.name,
        user.avatar_small_size1.name,
        user.avatar_small_size2.name,
        user.avatar_small_size3.name,
    ]

    files_for_delete = [
        f"{prefix_for_avatars}/{file}"
        for file in files_in_avatars_dir
        if f"{prefix_for_avatars}/{file}" not in avatars_names_list
    ]

    delete_old_avatar_names(files_for_delete)
