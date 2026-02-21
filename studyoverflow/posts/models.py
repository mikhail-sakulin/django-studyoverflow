from typing import Final
from urllib.parse import urlencode

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db import models
from django.urls import reverse
from django.utils.text import Truncator
from notifications.models import Notification
from posts.services import (
    PostTitleValidator,
    generate_slug,
    normalize_tag_name,
    render_markdown_safe,
)
from taggit.managers import TaggableManager
from taggit.models import GenericTaggedItemBase, TagBase

from studyoverflow import settings


class LowercaseTag(TagBase):
    """
    Кастомная модель тега (наследование от taggit.models.TagBase).

    Поля (без учета наследования):
    - name (CharField): Имя тега.
    """

    MAX_NAME_LENGTH_TAG: Final = 50  # максимальная длина имени тега

    name = models.CharField(
        max_length=MAX_NAME_LENGTH_TAG,
        validators=[MaxLengthValidator(MAX_NAME_LENGTH_TAG)],
        unique=True,
        verbose_name="Тег",
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def save(self, *args, **kwargs):
        """Приводит имя тега к нормализованному виду."""
        self.name = normalize_tag_name(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Возвращает уникальный URL для тега на основе name.
        Формирует URL-адрес страницы со списком постов, отфильтрованных по заданному тегу.
        """
        return f"{reverse('posts:list')}?{urlencode({'tags': self.name})}"


class TaggedPost(GenericTaggedItemBase):
    """
    Кастомная промежуточная модель для связи постов (Post) с тегами (LowercaseTag).
    Наследование от taggit.models.GenericTaggedItemBase.
    """

    tag = models.ForeignKey(LowercaseTag, related_name="tagged_posts", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Тег поста"
        verbose_name_plural = "Теги постов"

        # Уникальность связи и индекс для фильтрации постов по тегам:
        #   WHERE tag_id = ? AND content_type_id = ?
        # (через join'ы Post, TaggedPost, LowercaseTag)
        unique_together = ("tag", "content_type", "object_id")

        indexes = [
            # Индекс используется при получении тегов поста:
            #   WHERE object_id = ? AND content_type_id = ?
            # (через join'ы Post, TaggedPost, LowercaseTag)
            models.Index(fields=["object_id", "content_type_id"]),
        ]

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return f"{self.object_id} - {self.tag.name}"


class Post(models.Model):
    """
    Модель поста.

    Поля:
    - author (ForeignKey): Автор поста (пользователь).
    - title (CharField): Заголовок поста.
    - slug (SlugField): Человекочитаемый идентификатор для URL на основе заголовка.
    - content (TextField): Исходный текст в формате Markdown.
    - rendered_content (TextField): Сгенерированный HTML-код из Markdown (для кеширования).
    - tags (TaggableManager): Менеджер тегов, работающий через TaggedPost.
    - likes (GenericRelation): Связь с моделью лайков (Like).
    - notifications (GenericRelation): Связь с моделью уведомлений (Notification).
    - time_create (DateTimeField): Дата и время создания.
    - time_update (DateTimeField): Дата и время последнего изменения.
    """

    MAX_TITLE_SLUG_LENGTH_POST: Final = 255  # максимальная длина заголовка и slug поста
    MAX_CONTENT_LENGTH: Final = 15000  # максимальная длина содержимого поста

    title_validator = PostTitleValidator(min_len=10, max_len=MAX_TITLE_SLUG_LENGTH_POST)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор",
    )
    title = models.CharField(
        max_length=MAX_TITLE_SLUG_LENGTH_POST,
        validators=[title_validator],
        verbose_name="Заголовок",
    )
    slug = models.SlugField(max_length=MAX_TITLE_SLUG_LENGTH_POST, verbose_name="Slug")

    content = models.TextField(
        blank=True,
        max_length=MAX_CONTENT_LENGTH,
        validators=[MaxLengthValidator(MAX_CONTENT_LENGTH)],
        verbose_name="Содержимое поста",
    )
    rendered_content = models.TextField(
        blank=True,
        verbose_name="Отрендеренное содержимое (HTML из Markdown)",
    )

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

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        ordering = ["-time_create"]
        permissions = [("moderate_post", "Can moderate posts")]
        indexes = [
            # Индекс для сортировки постов по дате создания
            #   ORDER BY time_create DESC
            models.Index(fields=["-time_create"]),
            # Индекс для получения постов конкретного автора в сортировке по дате создания:
            #   Post.objects.filter(author=...).order_by('-time_create')
            #       WHERE author_id = 17
            #       ORDER BY time_create DESC
            models.Index(fields=["author", "-time_create"]),
        ]

    def __init__(self, *args, **kwargs):
        """
        Сохраняет исходное значение content, загруженное из БД.
        Используется для оптимизации рендеринга Markdown при сохранении.
        """
        super().__init__(*args, **kwargs)
        # Сохранение записанного в БД значения content для проверки изменения поля
        self._original_content = self.content

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return Truncator(self.title).chars(40, truncate="…")

    def save(self, *args, **kwargs):
        """
        Добавлена логика при сохранении объекта:
        - Автоматическая генерация slug на основе заголовка (только при создании).
        - Рендеринг Markdown в HTML только при создании или изменении контента.
        """
        if not self.slug:
            self.slug = generate_slug(self.title, self.MAX_TITLE_SLUG_LENGTH_POST)

        if not self.pk or self.content != self._original_content:
            self.rendered_content = render_markdown_safe(self.content)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Возвращает уникальный URL для поста на основе pk и slug."""
        return reverse("posts:detail", kwargs={"pk": self.pk, "slug": self.slug})

    @property
    def is_edited(self):
        """Вычисляемое свойство. Определяет факт редактирования поста."""
        return (self.time_update - self.time_create).total_seconds() > 3


class CommentQuerySet(models.QuerySet):
    """
    QuerySet для модели Comment с дополнительными методами
    для работы с иерархией комментариев.
    """

    def roots(self):
        """Возвращает родительские комментарии (которые без родительского комментария)."""
        return self.filter(parent_comment__isnull=True)

    def children(self):
        """Возвращает дочерние комментарии (имеющие родительский комментарий)."""
        return self.filter(parent_comment__isnull=False)


class Comment(models.Model):
    """
    Модель комментария к посту.

    Поля:
    - post (ForeignKey): Пост, к которому относится комментарий.
    - author (ForeignKey): Автор комментария.
    - parent_comment (ForeignKey): Родительский комментарий (для вложенности).
    - reply_to (ForeignKey): Комментарий, на который даётся ответ.
    - content (TextField): Исходный текст в формате Markdown.
    - rendered_content (TextField): Сгенерированный HTML-код из Markdown (для кеширования).
    - likes (GenericRelation): Связь с моделью лайков (Like).
    - notifications (GenericRelation): Связь с моделью уведомлений (Notification).
    - time_create (DateTimeField): Дата и время создания.
    - time_update (DateTimeField): Дата и время последнего изменения.
    """

    MAX_CONTENT_LENGTH: Final = 5000  # максимальная длина содержимого комментария

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments", verbose_name="Пост"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор",
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

    content = models.TextField(
        max_length=MAX_CONTENT_LENGTH,
        validators=[MaxLengthValidator(MAX_CONTENT_LENGTH)],
        verbose_name="Текст комментария",
    )
    rendered_content = models.TextField(
        blank=True,
        verbose_name="Отрендеренный текст (HTML из Markdown)",
    )

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

    objects = CommentQuerySet.as_manager()

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ["-time_create"]
        permissions = [("moderate_comment", "Can moderate comments")]
        indexes = [
            # Индекс для получения комментариев конкретного поста и сортировки их по дате создания,
            # включая возможность фильтрации по родительскому комментарию:
            #   Comment.objects.filter(post=post, parent_comment=None).order_by('-time_create')
            #       WHERE post_id = ? AND parent_comment_id IS NULL
            #       ORDER BY time_create DESC
            models.Index(fields=["post", "parent_comment", "-time_create"]),
            # Индекс для получения всех ответов (дочерних комментариев) на родительский комментарий
            # и сортировки их по дате создания:
            #   Comment.objects.filter(parent_comment=parent).order_by('-time_create')
            #       WHERE parent_comment_id = ?
            #       ORDER BY time_create DESC
            models.Index(fields=["parent_comment", "-time_create"]),
        ]

    def __init__(self, *args, **kwargs):
        """
        Сохраняет исходное значение content, загруженное из БД.
        Используется для оптимизации рендеринга Markdown при сохранении.
        """
        super().__init__(*args, **kwargs)
        # Сохранение записанного в БД значения content для проверки изменения поля
        self._original_content = self.content

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return f"{self.author}: {Truncator(self.content).chars(30, truncate="…")}"

    def save(self, *args, **kwargs):
        """
        Добавлена логика при сохранении комментария:
        - Рендеринг Markdown в HTML только при создании или изменении контента.
        """
        if not self.pk or self.content != self._original_content:
            self.rendered_content = render_markdown_safe(self.content)

        super().save(*args, **kwargs)

    def clean(self):
        """
        Валидация комментария.

        Проверяет:
        - что комментарий не пустой;
        - что текущий комментарий и комментарий, на который отвечают (reply_to),
          относятся к одному и тому же родительскому комментарию;
        - невозможность ссылок на самого себя;
        - принадлежность всех комментариев одному посту.
        """
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

    def get_absolute_url(self):
        """Возвращает уникальный URL комментария (страница поста с якорем на комментарий)."""
        return f"{self.post.get_absolute_url()}#comment-card-{self.pk}"

    @property
    def has_parent_comment(self):
        """Проверяет, есть ли родительский комментарий."""
        return self.parent_comment is not None

    @property
    def is_edited(self):
        """Вычисляемое свойство. Определяет факт редактирования комментария."""
        return (self.time_update - self.time_create).total_seconds() > 3


class LikeManager(models.Manager):
    """
    Менеджер модели Like с дополнительной логикой проверки лайков.
    """

    def is_liked(self, user, obj):
        """Проверяет, поставил ли пользователь лайк указанному объекту."""
        ct = ContentType.objects.get_for_model(obj)
        return self.filter(content_type=ct, object_id=obj.pk, user=user).exists()


class Like(models.Model):
    """
    Универсальная модель лайков для объектов Post и Comment.

    Поля:
    - user (ForeignKey): Пользователь, поставивший лайк.
    - content_type (ForeignKey): Тип объекта (Post, Comment).
    - object_id (PositiveIntegerField): ID объекта.
    - content_object (GenericForeignKey): Ссылка на объект.
    - notifications (GenericRelation): Связь с уведомлениями.
    - time_create (DateTimeField): Дата и время создания лайка.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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
        verbose_name = "Лайк"
        verbose_name_plural = "Лайки"
        ordering = ["-time_create"]

        # Уникальность связи и индекс для фильтрации лайков по пользователю и объекту:
        #   Like.objects.filter(user=user, content_type=ct, object_id=obj.id).exists()
        #       WHERE user_id = ? AND content_type_id = ? AND object_id = ?
        unique_together = ("user", "content_type", "object_id")

        indexes = [
            # Индекс для получения всех лайков конкретного объекта (Post, Comment):
            #   Like.objects.filter(content_type=ct, object_id=obj_id)
            #       WHERE content_type_id = ? AND object_id = ?
            models.Index(fields=["content_type_id", "object_id"]),
        ]

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return f"Like by {self.user} on {self.content_object}"

    def get_absolute_url(self):
        """Возвращает URL объекта, на который поставлен лайк."""
        return self.content_object.get_absolute_url()
