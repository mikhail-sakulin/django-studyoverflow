from __future__ import annotations

from typing import TYPE_CHECKING

import factory
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from notifications.models import Notification, NotificationType
from posts.models import Comment, Like, Post


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


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post
        skip_postgeneration_save = True

    author = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Тестовый заголовок поста {n}")
    # factory.Faker с provider="text" заполняет content текстом длиной до 500 символов
    content = factory.Faker(provider="text", max_nb_chars=500)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """
        Позволяет передавать теги при создании.
        """
        if not create:
            return

        tags = extracted or ["some_tag_1", "some_tag_2"]

        for tag in tags:
            self.tags.add(tag)


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment
        skip_postgeneration_save = True

    post = factory.SubFactory(PostFactory)
    author = factory.SubFactory(UserFactory)

    # По умолчанию комментарий родительский
    parent_comment = None
    reply_to = None

    content = factory.Faker(provider="text", max_nb_chars=300)


class NotificationPostCreateFactory(factory.django.DjangoModelFactory):
    """
    Factory уведомлений для автора на создание его поста.
    """

    class Meta:
        model = Notification
        skip_postgeneration_save = True

    # Получатель уведомления - автор поста
    user = factory.SubFactory(UserFactory)

    # Инициатор уведомления - сам автор, так как он создал свой пост
    actor = factory.SelfAttribute("user")

    # Объект, к которому относится уведомление - созданный пост
    content_object = factory.SubFactory(
        PostFactory,
        # ..actor - actor из внешней фабрики
        author=factory.SelfAttribute("..actor"),
    )

    # @factory.lazy_attribute - поскольку атрибут content_type зависит от
    # атрибута content_object, он вычисляется динамически как зависимый
    # после атрибута content_object, отрабатывает до создания объекта, а
    # @factory.post_generation - отрабатывает после создания объекта
    @factory.lazy_attribute
    def content_type(obj):
        # obj - не экземпляр Notification, а внутренний класс FactoryBoy с атрибутами для будущего
        # создания экземпляра Notification, поэтому пишется obj, а не self
        return ContentType.objects.get_for_model(obj.content_object)

    @factory.lazy_attribute
    def object_id(obj):
        return obj.content_object.pk  # type: ignore[attr-defined]

    notification_type = NotificationType.POST

    # Автоматически создается случайно предложение.
    message = factory.Faker("sentence")

    is_read = False


class LikeFactory(factory.django.DjangoModelFactory):
    """
    Универсальная Factory для модели Like.

    По умолчанию создаёт лайк для Post, но content_object можно
    переопределить, например задать объект Comment.
    """

    class Meta:
        model = Like
        skip_postgeneration_save = True

    user = factory.SubFactory(UserFactory)

    content_object = factory.SubFactory(PostFactory)

    # @factory.lazy_attribute - поскольку атрибут content_type зависит от
    # атрибута content_object, он вычисляется динамически как зависимый
    # после атрибута content_object, отрабатывает до создания объекта, а
    # @factory.post_generation - отрабатывает после создания объекта
    @factory.lazy_attribute
    def content_type(obj):
        # obj - не экземпляр Like, а внутренний класс FactoryBoy с атрибутами для будущего
        # создания экземпляра Like, поэтому пишется obj, а не self
        return ContentType.objects.get_for_model(obj.content_object)

    @factory.lazy_attribute
    def object_id(obj):
        return obj.content_object.pk  # type: ignore[attr-defined]
