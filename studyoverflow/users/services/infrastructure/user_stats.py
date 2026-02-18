from django.contrib.auth import get_user_model
from django.db.models import Count, F
from django.db.models.functions import Greatest


def update_user_counter_field(author_id: int, counter_field: str, value_change: int):
    """
    Обновляет числовое поле счетчика у пользователя (например, posts_count или comments_count).

    Логика:
    - Проверяет, существует ли указанное поле у модели User.
    - Выполняет атомарное обновление через F() выражение.
    - Значение поля не может стать меньше 0 (используется Greatest).
    """
    user_model = get_user_model()

    if not hasattr(user_model, counter_field):
        raise ValueError(f"User has no field {counter_field}")

    user_model.objects.filter(pk=author_id).update(
        **{counter_field: Greatest(F(counter_field) + value_change, 0)}
    )


def get_counts_map(model, group_field):
    """
    Функция для подсчета объектов (posts/comments), сгруппированных по указанному полю (author_id).

    Используется для подсчета количества постов или комментариев пользователя.
    """
    return {
        row[group_field]: row["count"]
        for row in model.objects.values(group_field).annotate(count=Count("id"))
        if row[group_field] is not None
    }


def get_reputation_map(Post, Comment):  # noqa: N803
    """
    Создает словарь репутации пользователей на основе количества лайков их постов и комментариев.

    Логика:
    - Считает лайки к постам по каждому автору.
    - Считает лайки к комментариям по каждому автору.
    - Суммирует лайки из постов и комментариев для одного пользователя.
    - Возвращает словарь вида {user_id: total_likes}.
    """
    reputation_map = {}

    # Например <QuerySet [{'author_id': 1, 'total_likes': 10}, {'author_id': 2, 'total_likes': 5}]>
    post_likes_stats = Post.objects.values("author_id").annotate(total_likes=Count("likes"))

    # Добавление лайков за посты в словарь reputation_map
    for row in post_likes_stats:
        if row["author_id"]:
            reputation_map[row["author_id"]] = row["total_likes"]

    # Например <QuerySet [{'author_id': 3, 'total_likes': 15}, {'author_id': 4, 'total_likes': 20}]>
    comment_likes_stats = Comment.objects.values("author_id").annotate(total_likes=Count("likes"))

    # Добавление лайков за комментарии в словарь reputation_map
    for row in comment_likes_stats:
        user_id = row["author_id"]
        if row["author_id"]:
            reputation_map[user_id] = reputation_map.get(user_id, 0) + row["total_likes"]

    return reputation_map
