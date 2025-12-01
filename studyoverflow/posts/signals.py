from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from posts.models import Comment, Like, Post
from users.services.infrastructure import update_user_counter_field


@receiver(post_save, sender=Post)
def increase_author_posts_count(sender, instance, created, **kwargs):
    if created:
        update_user_counter_field(instance.author_id, "posts_count", 1)


@receiver(post_delete, sender=Post)
def decrease_author_posts_count(sender, instance, **kwargs):
    update_user_counter_field(instance.author_id, "posts_count", -1)


@receiver(post_save, sender=Comment)
def increase_author_comments_count(sender, instance, created, **kwargs):
    if created:
        update_user_counter_field(instance.author_id, "comments_count", 1)


@receiver(post_delete, sender=Comment)
def decrease_author_comments_count(sender, instance, **kwargs):
    update_user_counter_field(instance.author_id, "comments_count", -1)


@receiver(post_save, sender=Like)
def increase_author_likes_count(sender, instance, created, **kwargs):
    if created and instance.content_object:
        update_user_counter_field(instance.content_object.author_id, "reputation", 1)


@receiver(pre_delete, sender=Like)
def decrease_author_likes_count(sender, instance, **kwargs):
    if instance.content_object:
        update_user_counter_field(instance.content_object.author_id, "reputation", -1)
