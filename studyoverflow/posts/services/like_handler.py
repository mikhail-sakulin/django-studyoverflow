from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction
from django.db.models import QuerySet

from .loggers import log_like_event


if TYPE_CHECKING:
    from posts.models import Comment, Post
    from users.models import User


def perform_toggle_like(
    user: User, queryset: QuerySet[Post | Comment], pk: int | str, source: str
) -> tuple[Post | Comment, bool]:
    """
    Бизнес-логика переключения лайка.

    Возвращает (лайкнутый объект: Post | Comment, флаг создания лайка: bool).
    """
    with transaction.atomic():
        # .select_for_update может вызываться только внутри транзакции, иначе вызовется
        # исключение.
        #
        # PostgreSQL запрещает SELECT ... FOR UPDATE вместе с GROUP BY, в queryset
        # не должно быть группировки.
        #
        # Блокировка лайкнутого объекта предотвращает ситуацию, когда объект будет
        # внезапно удален параллельной транзакцией и лайк будет создан для несуществующего
        # объекта, так как используется связь GenericForeignKey. Также блокировка позволяет
        # избежать гонок при переключении лайка параллельными транзакциями.
        #
        # Аргумент "of" указывает, записи из каких таблиц нужно заблокировать,
        # self - таблицу текущей модели, при необходимости можно указывать другие
        # связанные модели, например author (of=('self', 'author')).
        obj = queryset.select_for_update(of=("self",)).get(pk=pk)

        like, created = obj.likes.get_or_create(user=user)

        if not created:
            like.delete()
            event_type = "like_remove"
        else:
            event_type = "like_add"

        # Обновление счетчика лайков объекта из БД после отработки сигнала на увеличение счетчика
        obj.refresh_from_db(fields=["likes_count"])

    # Логирование действия
    log_like_event(event_type=event_type, obj=obj, user=user, source=source)

    return obj, created
