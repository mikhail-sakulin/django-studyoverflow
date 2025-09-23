from typing import Final

from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from .utils import translit_rus_to_eng


MAX_TITLE_SLUG_LENGTH: Final = 255  # максимальная длина заголовка и slug


class Post(models.Model):
    """
    Модель поста приложения posts.

    Атрибуты:
        title (CharField): Заголовок поста.
        slug (SlugField): Человекопонятная часть уникального URL-идентификатора /slug/pk/.
        content (TextField): Текст поста.
        time_create (DateTimeField): Время создания поста.
        time_update (DateTimeField): Время последнего обновления поста.

    Методы:
        save(*args, **kwargs): Переопределяет стандартный метод сохранения объекта в БД для
            генерации slug.
        get_absolute_url(): Возвращает уникальный URL для поста на основе slug и pk.
    """

    title = models.CharField(max_length=MAX_TITLE_SLUG_LENGTH, verbose_name="Заголовок")
    slug = models.SlugField(max_length=MAX_TITLE_SLUG_LENGTH, verbose_name="Slug")
    content = models.TextField(blank=True, verbose_name="Текст поста")
    time_create = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    time_update = models.DateTimeField(auto_now=True, verbose_name="Время изменения")

    def __str__(self):
        return self.title

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
        """

        base_slug = slugify(translit_rus_to_eng(self.title))
        slug = base_slug[:MAX_TITLE_SLUG_LENGTH]
        self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Возвращает уникальный URL для поста на основе slug и pk.
        """
        return reverse("post", kwargs={"post_slug": self.slug, "pk": self.pk})
