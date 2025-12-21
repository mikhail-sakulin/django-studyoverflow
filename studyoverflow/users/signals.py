from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from users.services.infrastructure import get_user_avatar_paths_list
from users.tasks import delete_files_from_storage_task


User = get_user_model()


@receiver(post_delete, sender=User)
def notification_count_when_notification_deleted(sender, instance, **kwargs):
    paths_to_delete = get_user_avatar_paths_list(instance)

    if paths_to_delete:
        transaction.on_commit(lambda: delete_files_from_storage_task.delay(paths_to_delete))
