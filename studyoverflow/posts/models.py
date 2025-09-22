from django.db import models
from django.utils.text import slugify

from .utils import translit_rus_to_eng


class Post(models.Model):
    """
    Модель поста приложения posts.

    Атрибуты:
        title (CharFiled): Заголовок поста.
        slug (SlugField): Уникальный URL-идентификатор (slug).
        content (TextField): Текст поста.
        time_create (DateTimeField): Время создания поста.
        time_update (DateTimeField): Время последнего обновления поста.

    Методы:
        save(): Переопределяет стандартный метод сохранения объекта в БД для генерации slug.
    """

    MAX_TITLE_LENGTH = 255  # максимальная длина заголовка

    title = models.CharField(max_length=MAX_TITLE_LENGTH, verbose_name="Заголовок")

    slug = models.SlugField(
        max_length=MAX_TITLE_LENGTH, unique=True, db_index=True, verbose_name="Slug"
    )

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

        Сохраняет объект в БД с автоматической генерацией уникального slug.

        Slug генерируется на основе title. Если такой slug уже существует,
        к нему добавляется уникальный числовой суффикс.

        Длина slug не превышает 255 символов, при необходимости базовая
        часть slug обрезается.
        """

        if not self.slug:
            base_slug = slugify(translit_rus_to_eng(self.title))
            slug = base_slug[: self.MAX_TITLE_LENGTH]
            counter = 1

            while Post.objects.filter(slug=slug).exists():
                counter += 1
                counter_str = str(counter)

                # Вычисляется максимальная длина базовой части slug
                max_base_slug_length = self.MAX_TITLE_LENGTH - len(counter_str) - 1  # -1 для дефиса

                if len(base_slug) > max_base_slug_length:
                    truncated_base = base_slug[:max_base_slug_length]
                else:
                    truncated_base = base_slug

                slug = f"{truncated_base}-{counter_str}"

            self.slug = slug

        super().save(*args, **kwargs)
