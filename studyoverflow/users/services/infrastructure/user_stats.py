from django.contrib.auth import get_user_model
from django.db.models import Count, F
from django.db.models.functions import Greatest


def update_user_counter_field(author_id: int, counter_field: str, value_change: int):
    author_model = get_user_model()

    if not hasattr(author_model, counter_field):
        raise ValueError(f"User has no field {counter_field}")

    author_model.objects.filter(pk=author_id).update(
        **{counter_field: Greatest(F(counter_field) + value_change, 0)}
    )


def get_counts_map(model, group_field):
    """
    Функция для подсчета объектов (posts/comments)
    """
    return {
        row[group_field]: row["count"]
        for row in model.objects.values(group_field).annotate(count=Count("id"))
        if row[group_field] is not None
    }


def get_reputation_map(Post, Comment):  # noqa: N803
    """
    Функция для агрегации лайков из разных моделей.
    """
    reputation_map = {}

    post_likes_stats = Post.objects.values("author_id").annotate(total_likes=Count("likes"))

    for row in post_likes_stats:
        if row["author_id"]:
            reputation_map[row["author_id"]] = row["total_likes"]

    comment_likes_stats = Comment.objects.values("author_id").annotate(total_likes=Count("likes"))

    for row in comment_likes_stats:
        user_id = row["author_id"]
        if row["author_id"]:
            reputation_map[user_id] = reputation_map.get(user_id, 0) + row["total_likes"]

    return reputation_map
