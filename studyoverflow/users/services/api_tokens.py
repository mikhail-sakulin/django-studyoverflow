from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)


if TYPE_CHECKING:
    from users.models import User


def revoke_user_api_tokens(user: User) -> None:
    """Отзывает все DRF-токены и refresh JWT-токены пользователя."""
    # Удаление всех DRF-токенов
    Token.objects.filter(user=user).delete()

    # Все refresh JWT-токены вносятся в Blacklist.
    outstanding = OutstandingToken.objects.filter(user=user)
    # При .bulk_create сигналы не вызываются, при необходимости вызова сигналов нужно использовать
    #
    # for token in outstanding:
    #     BlacklistedToken.objects.get_or_create(token=token)
    #
    # Но это создает N запросов к БД вместо одного. При большом числе токенов нужно вызывать
    # кастомный сигнал вручную после .bulk_create при необходимости.
    BlacklistedToken.objects.bulk_create(
        [BlacklistedToken(token=t) for t in outstanding],
        # Указывает БД игнорировать ошибки уникальности (уже заблокированные токены пропускаются),
        # в PostgreSQL INSERT ... ON CONFLICT DO NOTHING.
        ignore_conflicts=True,
    )
