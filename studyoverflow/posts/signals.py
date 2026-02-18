from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from posts.models import Comment, Like, Post
from users.services import update_user_counter_field


@receiver(post_save, sender=Post)
def increase_author_posts_count(sender, instance, created, raw, **kwargs):
    """
    Сигнал, срабатывающий после сохранения поста.

    Увеличивает счетчик постов автора на 1 при создании нового поста.
    Не выполняется для "raw" операций (например, при загрузке fixtures).
    """
    if raw:
        return

    if created:
        update_user_counter_field(instance.author_id, "posts_count", 1)


@receiver(post_delete, sender=Post)
def decrease_author_posts_count(sender, instance, **kwargs):
    """
    Сигнал, срабатывающий после удаления поста.

    Уменьшает счетчик постов автора на 1.
    """
    update_user_counter_field(instance.author_id, "posts_count", -1)


@receiver(post_save, sender=Comment)
def increase_author_comments_count(sender, instance, created, raw, **kwargs):
    """
    Сигнал, срабатывающий после сохранения комментария.

    Увеличивает счетчик комментариев автора на 1 при создании нового комментария.
    Не выполняется для "raw" операций (например, при загрузке fixtures).
    """
    if raw:
        return

    if created:
        update_user_counter_field(instance.author_id, "comments_count", 1)


@receiver(post_delete, sender=Comment)
def decrease_author_comments_count(sender, instance, **kwargs):
    """
    Сигнал, срабатывающий после удаления комментария.

    Уменьшает счетчик комментариев автора на 1.
    """
    update_user_counter_field(instance.author_id, "comments_count", -1)


@receiver(post_save, sender=Like)
def increase_author_likes_count(sender, instance, created, raw, **kwargs):
    """
    Сигнал, срабатывающий после сохранения лайка.

    Увеличивает репутацию автора объекта (Post или Comment) на 1.
    Не выполняется для "raw" операций (например, при загрузке fixtures).
    """
    if raw:
        return

    if created and instance.content_object:
        update_user_counter_field(instance.content_object.author_id, "reputation", 1)


@receiver(pre_delete, sender=Like)
def decrease_author_likes_count(sender, instance, **kwargs):
    """
    Сигнал, срабатывающий перед удалением лайка.

    Уменьшает репутацию автора объекта (Post или Comment) на 1.
    """
    if instance.content_object:
        update_user_counter_field(instance.content_object.author_id, "reputation", -1)
