from django.db.models import F
from django.db.models.functions import Greatest
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver

from posts.models import Comment, Like, LowercaseTag, Post
from posts.services import delete_cache_post_detail, delete_cache_tags_list
from users.services import update_user_counter_field


@receiver(post_save, sender=Post)
def increase_author_posts_count(sender, instance, created, raw, **kwargs):
    """
    Обработчик сигнала, срабатывающий после сохранения поста.

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
    Обработчик сигнала, срабатывающий после удаления поста.

    Уменьшает счетчик постов автора на 1.
    """
    update_user_counter_field(instance.author_id, "posts_count", -1)


@receiver(post_save, sender=Comment)
def increase_author_comments_count(sender, instance, created, raw, **kwargs):
    """
    Обработчик сигнала, срабатывающий после сохранения комментария.

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
    Обработчик сигнала, срабатывающий после удаления комментария.

    Уменьшает счетчик комментариев автора на 1.
    """
    update_user_counter_field(instance.author_id, "comments_count", -1)


@receiver(post_save, sender=Like)
def increase_author_likes_count(sender, instance, created, raw, **kwargs):
    """
    Обработчик сигнала, срабатывающий после сохранения лайка.

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
    Обработчик сигнала, срабатывающий перед удалением лайка.

    Уменьшает репутацию автора объекта (Post или Comment) на 1.
    """
    if instance.content_object:
        update_user_counter_field(instance.content_object.author_id, "reputation", -1)


@receiver(post_save, sender=Like)
def increase_content_object_likes_count(sender, instance, created, raw, **kwargs):
    """
    Обработчик сигнала, срабатывающий после создания лайка.

    Увеличивает счетчик лайков связанного объекта (Post или Comment) на 1.
    """
    if raw:
        return

    if created:
        like = instance

        if like.object_id:
            model = like.content_type.model_class()

            if not hasattr(model, "likes_count"):
                return

            model.objects.filter(pk=like.object_id).update(likes_count=F("likes_count") + 1)


@receiver(pre_delete, sender=Like)
def decrease_content_object_likes_count(sender, instance, **kwargs):
    """
    Обработчик сигнала, срабатывающий перед удалением лайка.

    Уменьшает счетчик лайков связанного объекта (Post или Comment) на 1.
    """
    like = instance

    if like.object_id:
        model = like.content_type.model_class()

        if not hasattr(model, "likes_count"):
            return

        model.objects.filter(pk=like.object_id).update(
            likes_count=Greatest(F("likes_count") - 1, 0)
        )


@receiver(post_save, sender=Comment)
def increase_post_comments_count(sender, instance, created, raw, **kwargs):
    """
    Обработчик сигнала, срабатывающий после создания комментария.

    Увеличивает счетчик комментариев связанного поста на 1.
    """
    if raw:
        return

    if created:
        comment = instance

        Post.objects.filter(pk=comment.post_id).update(comments_count=F("comments_count") + 1)


@receiver(pre_delete, sender=Comment)
def decrease_post_comments_count(sender, instance, **kwargs):
    """
    Обработчик сигнала, срабатывающий перед удалением комментария.

    Уменьшает счетчик комментариев связанного поста на 1.
    """
    comment = instance

    Post.objects.filter(pk=comment.post_id).update(
        comments_count=Greatest(F("comments_count") - 1, 0)
    )


@receiver([post_save, post_delete], sender=Post)
def invalidate_post_cache_on_save_or_delete(sender, instance, created=False, **kwargs):
    """
    Удаляет кеш поста при изменении или удалении поста.
    """
    if created:
        return

    delete_cache_post_detail(instance.pk)


@receiver([post_save, post_delete], sender=LowercaseTag)
def invalidate_tags_cache_on_save_or_delete(sender, **kwargs):
    """
    Удаляет кеш списка тегов при создании, изменении или удалении тега.
    """
    delete_cache_tags_list()
