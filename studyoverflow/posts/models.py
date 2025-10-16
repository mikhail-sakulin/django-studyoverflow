from typing import Final

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from posts.services.domain import generate_slug
from taggit.managers import TaggableManager
from taggit.models import GenericTaggedItemBase, TagBase


MAX_TITLE_SLUG_LENGTH_POST: Final = 255  # максимальная длина заголовка и slug поста
MAX_NAME_SLUG_LENGTH_TAG: Final = 50  # максимальная длина заголовка и slug тега


class LowercaseTag(TagBase):
    """
    Пользовательская модель тега (наследование от taggit.TagBase).

    Атрибуты:
        name (CharField): Имя тега.
        slug (SlugField): Человекопонятная часть уникального URL-идентификатора /slug/pk/.

    Методы:
        - save(*args, **kwargs):
            - преобразует имя тега в нижний регистр перед сохранением с удалением лишних пробелов,
            - генерирует slug;
        - get_absolute_url(): Возвращает уникальный URL для тега на основе slug и pk.
    """

    name = models.CharField(max_length=MAX_NAME_SLUG_LENGTH_TAG, unique=True, verbose_name="Тег")
    slug = models.SlugField(max_length=MAX_NAME_SLUG_LENGTH_TAG, verbose_name="Slug")

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def save(self, *args, **kwargs):
        self.name = self.name.strip().lower()
        if not self.slug:
            self.slug = generate_slug(self.name, max_length=MAX_NAME_SLUG_LENGTH_TAG)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Возвращает уникальный URL для тега на основе slug и pk.
        """
        return reverse("tag", kwargs={"tag_slug": self.slug, "pk": self.pk})


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
