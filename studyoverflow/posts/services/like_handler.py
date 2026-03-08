from __future__ import annotations

from typing import TYPE_CHECKING

from .loggers import log_like_event


if TYPE_CHECKING:
    from posts.models import Comment, Post
    from users.models import User


def perform_toggle_like(user: User, obj: Post | Comment, source: str) -> tuple[bool, int]:
    """
    Бизнес-логика переключения лайка.

    Возвращает (состояние_лайка: bool, общее количество: int).
    """
    like, created = obj.likes.get_or_create(user=user)

    if not created:
        like.delete()
        event_type = "like_remove"
    else:
        event_type = "like_add"

    # Логирование действия
    log_like_event(event_type=event_type, obj=obj, user=user, source=source)

    return created, obj.likes.count()
