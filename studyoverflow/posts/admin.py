from datetime import timedelta
from typing import Type

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Count
from django.db.models.functions import Length
from django.utils.text import Truncator
from posts.models import Comment, Like, LowercaseTag, Post, TaggedPost


class IsEditedFilter(admin.SimpleListFilter):
    title = "Отредактировано"
    parameter_name = "is_edited"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(time_update__gt=models.F("time_create") + timedelta(seconds=3))

        elif self.value() == "no":
            return queryset.filter(time_update__lte=models.F("time_create") + timedelta(seconds=3))

        return queryset


class ContentEmptyFilter(admin.SimpleListFilter):
    title = "Контент пустой"
    parameter_name = "content_empty"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(content="")

        elif self.value() == "no":
            return queryset.exclude(content="")

        return queryset


class LikeContentTypeFilter(admin.SimpleListFilter):
    title = "Тип объекта"
    parameter_name = "content_type"

    def lookups(self, request, model_admin):
        allowed_models: list[Type[models.Model]] = [Post, Comment]

        return [
            (ct.id, ct.model_class()._meta.verbose_name.title())
            for ct in ContentType.objects.filter(
                model__in=[m._meta.model_name for m in allowed_models]
            )
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(content_type_id=self.value())

        return queryset


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "time_create",
        "is_edited_display",
        "short_title",
        "brief_info",
    )
    list_display_links = (
        "id",
        "short_title",
        "brief_info",
    )
    ordering = [
        "-time_create",
        "title",
    ]
    list_per_page = 15
    actions = [
        "clear_content",
    ]
    search_fields = [
        "title",
        "content",
    ]
    list_filter = [
        IsEditedFilter,
        ContentEmptyFilter,
    ]
    fields = [
        "id",
        "author",
        "time_create",
        "time_update",
        "title",
        "slug",
        "content",
        "tags",
    ]
    readonly_fields = ["id", "author", "slug", "time_create", "time_update"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(content_len=Length("content"))

    def get_actions(self, request):
        actions = super().get_actions(request)

        if not self._can_clear_content(request.user):
            actions.pop("clear_content", None)

        return actions

    @admin.action(description="Очистить контент выбранных постов")
    def clear_content(self, request, queryset):
        if not self._can_clear_content(request.user):
            self.message_user(
                request,
                "Недостаточно прав для выполнения действия.",
                level=messages.ERROR,
            )
            return

        count = queryset.update(content="")
        self.message_user(request, f"Содержимое {count} постов очищено.")

    @admin.display(description="Отредактировано", boolean=True)
    def is_edited_display(self, post: Post):
        return post.is_edited

    @admin.display(description="Заголовок", ordering="title")
    def short_title(self, post: Post):
        return Truncator(post.title).chars(40, truncate="...")

    @admin.display(description="Краткое описание", ordering="content_len")
    def brief_info(self, post: Post):
        return f"Контент из {post.content_len or 0} символов."

    def _can_clear_content(self, user):
        UserModel = get_user_model()  # noqa: N806
        return user.role in {UserModel.Role.ADMIN, UserModel.Role.MODERATOR}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "time_create",
        "is_edited_display",
        "author",
        "short_content",
        "short_post",
    )
    list_display_links = ("id", "short_content")
    search_fields = ["content", "author__username", "post__title"]
    list_filter = [IsEditedFilter]
    ordering = ["-time_create", "-id"]
    list_per_page = 15
    fields = [
        "id",
        "time_create",
        "time_update",
        "author",
        "post",
        "parent_comment",
        "reply_to",
        "content",
    ]
    readonly_fields = ["id", "time_create", "time_update", "post", "author"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(content_len=Length("content"))

    @admin.display(description="Комментарий", ordering="content_len")
    def short_content(self, comment: Comment):
        return Truncator(comment.content).chars(40, truncate="...")

    @admin.display(description="Отредактировано", boolean=True)
    def is_edited_display(self, comment: Comment):
        return comment.is_edited

    @admin.display(description="Пост")
    def short_post(self, comment: Comment):
        return Truncator(comment.post.title).chars(40, truncate="...")


@admin.register(LowercaseTag)
class LowercaseTagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "posts_count")
    list_display_links = (
        "id",
        "name",
    )
    search_fields = [
        "name",
    ]
    readonly_fields = [
        "slug",
    ]
    ordering = ["name", "id"]
    list_per_page = 15

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(posts_count=Count("tagged_posts"))

    @admin.display(description="Количество постов с этим тегом", ordering="posts_count")
    def posts_count(self, tag: LowercaseTag):
        return tag.posts_count


@admin.register(TaggedPost)
class TaggedPostAdmin(admin.ModelAdmin):
    list_display = ("id", "tag__name", "short_content_object")
    list_display_links = ("id", "tag__name", "short_content_object")
    fields = ["id", "tag", "content_type", "short_content_object", "object_id"]
    readonly_fields = ("id", "content_type", "short_content_object")
    list_per_page = 15
    ordering = ["-tag__name", "-id"]
    search_fields = [
        "tag__name",
    ]

    @admin.display(description="Объект, имеющий тег")
    def short_content_object(self, tagged_post: TaggedPost):
        if not tagged_post.content_object:
            return "—"
        return Truncator(str(tagged_post.content_object)).chars(40, truncate="…")


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "time_create",
        "user",
        "short_content_object",
        "content_type",
        "object_id",
    )
    list_display_links = (
        "id",
        "short_content_object",
    )
    list_filter = (LikeContentTypeFilter,)
    ordering = ["-time_create"]
    readonly_fields = (
        "id",
        "user",
        "time_create",
        "short_content_object",
        "content_type",
        "object_id",
    )
    search_fields = [
        "user__username",
    ]
    list_per_page = 15

    def has_add_permission(self, request):
        return False

    @admin.display(description="Лайкнутый объект")
    def short_content_object(self, like: Like):
        if not like.content_object:
            return "—"
        return Truncator(str(like.content_object)).chars(40, truncate="…")
