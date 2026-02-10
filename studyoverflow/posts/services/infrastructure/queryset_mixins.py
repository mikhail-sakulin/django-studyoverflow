from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Exists, OuterRef, Q
from django.http import HttpRequest
from posts.models import Like, Post


class LikeAnnotationsMixin:
    like_model = None
    like_related_field = "likes"
    request: HttpRequest

    def _get_content_type(self, model):
        return ContentType.objects.get_for_model(model)

    def annotate_queryset(self, queryset):
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
    """

    model: type[Post]

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
        Фильтрация по полям модели (q, tags, author).
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
        Фильтрация и сортировка по аннотациям (likes_count, comments_count).
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
    request: HttpRequest

    def sort_comments(self, queryset):
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
