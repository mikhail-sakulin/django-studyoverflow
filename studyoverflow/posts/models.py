from typing import Final
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from notifications.models import Notification
from posts.services.domain import generate_slug, normalize_tag_name
from taggit.managers import TaggableManager
from taggit.models import GenericTaggedItemBase, TagBase


MAX_TITLE_SLUG_LENGTH_POST: Final = 255  # максимальная длина заголовка и slug поста
MAX_NAME_LENGTH_TAG: Final = 50  # максимальная длина имени тега


class LowercaseTag(TagBase):
    """
    Пользовательская модель тега (наследование от taggit.TagBase).

    Атрибуты:
        name (CharField): Имя тега.

    Методы:
        - save(*args, **kwargs):
            - преобразует имя тега в нижний регистр перед сохранением с удалением лишних пробелов,
        - get_absolute_url(): Возвращает уникальный URL для тега на основе name.
    """

    name = models.CharField(max_length=MAX_NAME_LENGTH_TAG, unique=True, verbose_name="Тег")

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def save(self, *args, **kwargs):
        self.name = normalize_tag_name(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Возвращает уникальный URL для тега на основе name.
        """
        return f"{reverse('posts:list')}?{urlencode({'tags': self.name})}"


class TaggedPost(GenericTaggedItemBase):
    """
    Пользовательская промежуточная модель для связи
    постов (Post) с тегами (LowercaseTag).
    """

    tag = models.ForeignKey(LowercaseTag, related_name="posts", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.object_id} - {self.tag.name}"


class Post(models.Model):
    """
    Модель поста приложения posts.

    Атрибуты:
        author (User): Автор поста.
        title (CharField): Заголовок поста.
        slug (SlugField): Человекопонятная часть уникального URL-идентификатора /pk/slug/.
        content (TextField): Текст поста.
        tag (TaggableManager): Теги поста.
        time_create (DateTimeField): Время создания поста.
        time_update (DateTimeField): Время последнего обновления поста.

    Вычисляемые свойства:
        is_edited (bool): Определяет, был ли пост отредактирован.
            Считается True, если разница между временем обновления и временем создания
            более 5 секунд.

    Методы:
        save(*args, **kwargs): Переопределяет стандартный метод сохранения объекта в БД для
            генерации slug.
        get_absolute_url(): Возвращает уникальный URL для поста на основе pk и slug.
    """

    author = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="posts", verbose_name="Автор"
    )
    title = models.CharField(max_length=MAX_TITLE_SLUG_LENGTH_POST, verbose_name="Заголовок")
    slug = models.SlugField(max_length=MAX_TITLE_SLUG_LENGTH_POST, verbose_name="Slug")
    content = models.TextField(blank=True, verbose_name="Содержимое поста")
    tags = TaggableManager(through=TaggedPost, verbose_name="Теги")
    likes = GenericRelation(
        "Like", content_type_field="content_type", object_id_field="object_id", verbose_name="Лайк"
    )
    notifications = GenericRelation(
        Notification,
        content_type_field="content_type",
        object_id_field="object_id",
        verbose_name="Уведомления",
    )
    time_create = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    time_update = models.DateTimeField(auto_now=True, verbose_name="Время изменения")

    def __str__(self):
        return self.title

    @property
    def is_edited(self):
        """
        Вычисляемое свойство. Определяет факт редактирования поста.
        """
        return (self.time_update - self.time_create).total_seconds() > 5

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        ordering = ["-time_create"]
        indexes = [models.Index(fields=["-time_create"])]
        permissions = [("moderate_post", "Can moderate posts")]

    def save(self, *args, **kwargs):
        """
        Переопределение метода save.

        Сохраняет объект в БД с автоматической генерацией slug.

        Slug генерируется на основе title с обрезкой в случае превышения максимальной длины.

        Slug генерируется только 1 раз в момент создания поста.
        """

        if not self.slug:
            self.slug = generate_slug(self.title, MAX_TITLE_SLUG_LENGTH_POST)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Возвращает уникальный URL для поста на основе pk и slug.
        """
        return reverse("posts:detail", kwargs={"pk": self.pk, "slug": self.slug})


class CommentQuerySet(models.QuerySet):
    def roots(self):
        return self.filter(parent_comment__isnull=True)

    def children(self):
        return self.filter(parent_comment__isnull=False)


class Comment(models.Model):
    objects = CommentQuerySet.as_manager()

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments", verbose_name="Пост"
    )
    author = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="comments", verbose_name="Автор"
    )
    parent_comment = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_comments",
        verbose_name="Родительский комментарий",
    )
    reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name="Ответ на комментарий",
    )
    content = models.TextField(max_length=5000, verbose_name="Текст комментария")
    likes = GenericRelation(
        "Like", content_type_field="content_type", object_id_field="object_id", verbose_name="Лайк"
    )
    notifications = GenericRelation(
        Notification,
        content_type_field="content_type",
        object_id_field="object_id",
        verbose_name="Уведомления",
    )
    time_create = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    time_update = models.DateTimeField(auto_now=True, verbose_name="Время изменения")

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ["-time_create"]
        permissions = [("moderate_comment", "Can moderate comments")]

    def clean(self):
        errors = {}

        post = getattr(self, "post", None)

        if not self.content or not self.content.strip():
            errors["content"] = "Комментарий не может быть пустым."

        if self.parent_comment:
            if self.parent_comment == self:
                errors["parent_comment"] = "Комментарий не может быть родителем сам себе."
            elif post and self.parent_comment.post != post:
                errors["parent_comment"] = "Родительский комментарий не принадлежит этому посту."

        if self.reply_to:
            if (
                self.parent_comment
                and self.reply_to.parent_comment
                and self.reply_to.parent_comment != self.parent_comment
            ):
                errors["reply_to"] = "Неверный комментарий для ответа."

            elif self.reply_to == self:
                errors["reply_to"] = "Комментарий не может отвечать сам себе."

            elif post and self.reply_to.post != post:
                errors["reply_to"] = "Комментарий для ответа не принадлежит этому посту."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.author}: {self.content[:30]}"

    @property
    def has_parent_comment(self):
        return self.parent_comment is not None

    @property
    def is_edited(self):
        """
        Вычисляемое свойство. Определяет факт редактирования комментария.
        """
        return (self.time_update - self.time_create).total_seconds() > 5

    def get_absolute_url(self):
        return f"{self.post.get_absolute_url()}#comment-card-{self.pk}"


class LikeManager(models.Manager):
    def is_liked(self, user, obj):
        ct = ContentType.objects.get_for_model(obj)
        return self.filter(content_type=ct, object_id=obj.pk, user=user).exists()


class Like(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name="Пользователь",
    )

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, verbose_name="Тип объекта"
    )
    object_id = models.PositiveIntegerField(verbose_name="ID объекта")
    content_object = GenericForeignKey("content_type", "object_id")

    notifications = GenericRelation(
        Notification,
        content_type_field="content_type",
        object_id_field="object_id",
        verbose_name="Уведомления",
    )

    time_create = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")

    objects = LikeManager()

    class Meta:
        unique_together = ("user", "content_type", "object_id")
        ordering = ["-time_create"]
        verbose_name = "Лайк"
        verbose_name_plural = "Лайки"

    def __str__(self):
        return f"Like by {self.user} on {self.content_object}"

    def get_absolute_url(self):
        return self.content_object.get_absolute_url()
