from __future__ import annotations

import logging
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from django.db import models
    from posts.models import Comment, Post
    from users.models import User


logger = logging.getLogger(__name__)


def log_post_event(event_type: str, post: Post, user: User, source: str = "web") -> None:
    """
    Логирует различные события поста. Указывает источник: 'web' или 'api'.

    :param event_type: тип события (создание, обновление, удаление)
    :param post: объект поста
    :param user: объект пользователя
    :param source: источник события ('web' для Django views, 'api' для DRF)
    """
    # Возможные сообщения в зависимости от типа события
    event_messages = {
        "post_create": f"Пост создан: {post.title} (id: {post.pk}).",
        "post_update": f"Пост отредактирован: {post.title} (id: {post.pk}).",
        "post_delete": f"Пост удален: {post.title} (id: {post.pk}).",
    }

    user_id = user.pk if user and user.is_authenticated else None

    # Основные данные лога
    extra_data = {
        "post_id": post.pk,
        "source": source,
        "event_type": event_type,
    }

    # Роль пользователя в действии в зависимости от типа события
    if event_type == "post_create":
        extra_data["author_id"] = user_id
    elif event_type == "post_update":
        extra_data["editor_id"] = user_id
    elif event_type == "post_delete":
        extra_data["deleter_id"] = user_id

    logger.info(event_messages.get(event_type, "Событие поста"), extra=extra_data)


def log_comment_event(event_type: str, comment: Comment, user: User, source: str = "web") -> None:
    """
    Логирует различные события комментария. Указывает источник: 'web' или 'api'.

    :param event_type: тип события (создание, обновление, удаление)
    :param comment: объект комментария
    :param user: объект пользователя
    :param source: источник события ('web' для Django views, 'api' для DRF)
    """
    event_messages = {
        "comment_create": f"Создан комментарий (id: {comment.pk}) "
        f"пользователем {user.username} к посту (id: {comment.post_id}).",
        "comment_update": f"Комментарий обновлен (id: {comment.pk}) "
        f"пользователем {user.username} к посту (id: {comment.post_id}).",
        "comment_delete": f"Комментарий удален (id: {comment.pk}) "
        f"пользователем {user.username} к посту (id: {comment.post_id}).",
    }

    user_id = user.pk if user and user.is_authenticated else None

    extra_data = {
        "comment_id": comment.pk,
        "post_id": comment.post_id,
        "user_id": user_id,
        "event_type": event_type,
        "source": source,
    }

    logger.info(event_messages.get(event_type, "Событие комментария"), extra=extra_data)


def log_like_event(event_type: str, obj: models.Model, user: User, source: str) -> None:
    """
    Логирует события лайков (добавление / удаление). Указывает источник: 'web' или 'api'.

    :param event_type: тип события (создание, удаление)
    :param obj: объект, к которому относится лайк
    :param user: объект пользователя
    :param source: источник события ('web' для Django views, 'api' для DRF)
    """
    model_name = obj._meta.verbose_name.lower()
    model_type = obj._meta.model_name

    event_messages = {
        "like_add": f"Лайк добавлен к {model_name}у (id: {obj.pk}) пользователем {user.username}.",
        "like_remove": f"Лайк удален у {model_name}а (id: {obj.pk}) пользователем {user.username}.",
    }

    extra_data = {
        "object_id": obj.pk,
        "object_type": model_type,
        "user_id": user.pk,
        "event_type": event_type,
        "source": source,
    }

    logger.info(event_messages.get(event_type, "Событие лайка"), extra=extra_data)
