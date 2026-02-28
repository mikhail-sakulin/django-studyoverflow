"""
Миксины для оптимизации выборок, аннотирования и фильтрации данных.
"""

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Exists, OuterRef, Prefetch, Q, QuerySet
from django.http import HttpRequest
from posts.models import Comment, Like, Post


class LikeAnnotationsMixin:
    """
    Миксин для аннотирования QuerySet данными о лайках.
    """

    like_related_field: str = "likes"
    request: HttpRequest

    def _get_content_type(self, model):
        """Возвращает ContentType для указанной модели, используя кеш Django."""
        return ContentType.objects.get_for_model(model)

    def annotate_queryset(self, queryset):
        """
        Добавляет к выборке счетчик лайков и флаг 'user_has_liked'.
        """
        if "likes_count" not in queryset.query.annotations:
            queryset = queryset.annotate(likes_count=Count(self.like_related_field))

        user = getattr(self.request, "user", None)

        if user and user.is_authenticated:
            content_type = self._get_content_type(queryset.model)

            queryset = queryset.annotate(
                user_has_liked=Exists(
                    Like.objects.filter(
                        content_type=content_type, object_id=OuterRef("pk"), user=user
                    )
                )
            )
        else:
            queryset = queryset.annotate(user_has_liked=Exists(Like.objects.none()))

        return queryset


class PostAnnotateQuerysetMixin(LikeAnnotationsMixin):
    """
    Аннотированный queryset для постов:
    - select_related author
    - prefetch_related tags
    - annotate likes_count и comments_count
    - флаг 'user_has_liked' через LikeAnnotationsMixin
    """

    def get_annotate_queryset(self, queryset):  # type: ignore
        queryset = (
            queryset.select_related("author")
            .prefetch_related("tags")
            .annotate(
                likes_count=Count("likes", distinct=True),
                comments_count=Count("comments", distinct=True),
            )
        )
        queryset = super().annotate_queryset(queryset)
        return queryset


class PostFilterSortMixin:
    """
    Миксин для фильтрации и сортировки постов по GET-параметрам:
    - q: поиск по заголовку или содержимому
    - tags: теги через запятую
    - tag_match: any/all
    - author: имя автора
    - has_comments: yes/no
    - sort: created/likes/answers
    - order: asc/desc
    """

    def filter_by_model_fields(self, queryset, request):
        """
        Выполняет поиск по текстовым полям и фильтрацию по связям tags, author.
        """
        # Поиск по тексту
        q = request.GET.get("q", "").strip()
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(content__icontains=q) | Q(tags__name__icontains=q)
            ).distinct()

        # Фильтр по тегам
        tags = request.GET.get("tags", "").strip()
        tag_match = request.GET.get("tag_match", "any")
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            if tag_list:
                if tag_match == "any":
                    queryset = queryset.filter(tags__name__in=tag_list)
                else:
                    for tag_name in tag_list:
                        queryset = queryset.filter(tags__name=tag_name)
                queryset = queryset.distinct()

        # Фильтр по автору
        author = request.GET.get("author", "").strip()
        if author:
            queryset = queryset.filter(author__username__iexact=author)

        return queryset

    def filter_and_sort_by_annotations(self, queryset, request):
        """
        Фильтрация по аннотированному полю comments_count.
        Сортировка по полям модели или аннотированным полям.
        """
        # Фильтр по наличию комментариев
        has_comments = request.GET.get("has_comments", "any")
        if has_comments == "yes":
            queryset = queryset.filter(comments_count__gt=0)
        elif has_comments == "no":
            queryset = queryset.filter(comments_count=0)

        ordering_map = {
            "created": "time_create",
            "likes": "likes_count",
            "comments": "comments_count",
        }

        # Сортировка
        sort = request.GET.get("sort")
        sort = sort if sort in ordering_map else "created"

        order = request.GET.get("order")
        order = order if order in ("asc", "desc") else "desc"

        ordering_field = ordering_map.get(sort, "time_create")

        if order == "desc":
            ordering_field = f"-{ordering_field}"

        queryset = queryset.order_by(ordering_field, "-time_create")

        return queryset


class CommentSortMixin:
    """
    Миксин для сортировки комментариев по дате и лайкам.
    """

    request: HttpRequest

    def sort_comments(self, queryset):
        """
        Упорядочивает queryset комментариев на основе параметров запроса.
        Сортирует комментарии по дате и лайкам.
        """
        ordering_map = {
            "date": "time_create",
            "likes": "likes_count",
        }

        sort = self.request.GET.get("comment_sort")
        sort = sort if sort in ordering_map else "date"

        order = self.request.GET.get("comment_order")
        order = order if order in ("asc", "desc") else "desc"

        field = ordering_map.get(sort, "time_create")
        if order == "desc":
            field = f"-{field}"

        queryset = queryset.order_by(field, "-time_create")

        return queryset


class CommentTreeQuerysetMixin:
    """
    Миксин для построения queryset комментариев с вложенностью, аннотациями и сортировкой.

    Требует реализации:
    - annotate_queryset(queryset)
    - sort_comments(queryset)
    """

    def get_comment_tree_queryset(
        self, post: Post, root_id: int | None = None
    ) -> QuerySet[Comment]:
        """
        Возвращает queryset родительских комментариев с
        prefetch_related queryset дочерних комментариев.

        Используются select_related для оптимизации запроса и аннотации.
        """
        child_queryset = self.annotate_queryset(  # type: ignore[attr-defined]
            Comment.objects.select_related(
                "author", "post", "reply_to", "reply_to__author"
            ).order_by("-time_create")
        )

        if root_id:
            queryset = Comment.objects.filter(pk=root_id)
        else:
            queryset = post.comments.roots()  # type: ignore[attr-defined]

        queryset = (
            queryset.select_related("author", "post")
            # prefetch_related для обратного доступа ForeignKey через related_name
            .prefetch_related(Prefetch("child_comments", queryset=child_queryset)).order_by(
                "-time_create"
            )
        )

        queryset = self.annotate_queryset(queryset)  # type: ignore[attr-defined]

        queryset = self.sort_comments(queryset)  # type: ignore[attr-defined]

        return queryset
