from __future__ import annotations

from typing import TYPE_CHECKING

import factory
from django.contrib.auth import get_user_model


if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


User = get_user_model()


# factory.Factory создает python объект, но не сохраняет его в БД, а
# factory.django.DjangoModelFactory создает и сохраняет объект
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        # Не вызывать автоматический .save() после вызова post_generation методов после
        # первого .save() (после создания объекта), а вызывать только методы (сохранение вручную).
        skip_postgeneration_save = True

    # Sequence - генератор уникальных значений (0, 1, 2, ...),
    # то есть user0, user1, user2 ...
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")

    # UserFactory создает и сохраняет объект в БД,
    # используя указанные в Factory значения полей или их переопределенные значения,
    # затем вызываются post_generation методы, в частности set_password(...),
    # затем вызывается .save(update_fields=["password"])
    # с указанием сохранить только пароль (его хеш).
    #
    # Пароль нельзя задать как обычное поле (иначе в БД будет значение без хеша)
    # перед созданием пользователя, поскольку нужно вызывать метод .set_password(password)
    # при создании, а factory не умеет этого делать,
    # метод вызывается после создания объекта, когда есть self.
    @factory.post_generation
    def password(self: AbstractUser, create: bool, extracted: str | None, **kwargs) -> None:
        password = extracted or "StrongPassword123"

        self.set_password(password)

        if create:
            self.save(update_fields=["password"])
