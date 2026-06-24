"""
Celery-задачи для фоновой асинхронной обработки данных постов.
"""

from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import Coalesce
from posts.models import Comment, Like, Post


@shared_task
def sync_post_counters():
    """
    Пересчитывает и синхронизирует поля-счётчики для постов через единый SQL-запрос.

    Обновляет:
    - количество комментариев (comments_count),
    - количество лайков (likes_count).
    """
    post_content_type = ContentType.objects.get_for_model(Post)

    # Подзапрос для подсчета числа комментариев поста,
    # пустой .order_by() очищает сортировку, чтобы лишние поля не попали в GROUP BY
    comments_subquery = (
        Comment.objects.filter(post_id=OuterRef("pk"))
        .order_by()
        .values("post_id")
        .annotate(count=Count("pk"))
        .values("count")
    )

    # Подзапрос для подсчета числа лайков поста,
    # пустой .order_by() очищает сортировку, чтобы лишние поля не попали в GROUP BY
    likes_subquery = (
        Like.objects.filter(content_type=post_content_type, object_id=OuterRef("pk"))
        .order_by()
        .values("object_id")
        .annotate(count=Count("pk"))
        .values("count")
    )

    # Единый UPDATE запрос к БД
    Post.objects.update(
        comments_count=Coalesce(Subquery(comments_subquery), 0),
        likes_count=Coalesce(Subquery(likes_subquery), 0),
    )


@shared_task
def sync_comment_counters():
    """
    Пересчитывает поле-счетчик лайков для комментариев через единый SQL-запрос.
    """
    comment_content_type = ContentType.objects.get_for_model(Comment)

    # Подзапрос для подсчета числа лайков комментария,
    # пустой .order_by() очищает сортировку, чтобы лишние поля не попали в GROUP BY
    likes_subquery = (
        Like.objects.filter(content_type=comment_content_type, object_id=OuterRef("pk"))
        .order_by()
        .values("object_id")
        .annotate(count=Count("pk"))
        .values("count")
    )

    # Единый UPDATE запрос к БД
    Comment.objects.update(likes_count=Coalesce(Subquery(likes_subquery), 0))
