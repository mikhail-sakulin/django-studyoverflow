from django.contrib.auth import get_user_model
from django.db.models import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from posts.api.openapi_responses import (
    CommentFieldErrorValidationOpenApiResponse,
    PaginationErrorOpenApiResponse,
    PermissionDeniedOpenApiResponse,
    PostFieldErrorValidationOpenApiResponse,
    create_new_not_found_response,
)
from posts.api.pagination import PostCommentsPagination
from posts.api.permissions import IsAuthorOrModeratorPermission
from posts.api.serializers import (
    AuthorSerializer,
    CommentSerializer,
    DetailSerializer,
    PostSerializer,
    TagSerializer,
)
from posts.mixins import (
    CommentSortMixin,
    CommentTreeQuerysetMixin,
    LikeAnnotationsMixin,
    PostAnnotateQuerysetMixin,
    PostFilterSortMixin,
)
from posts.models import Comment, LowercaseTag, Post
from posts.services import (
    get_cached_post,
    get_cached_tags,
    log_comment_event,
    log_post_event,
    perform_toggle_like,
)
from users.api.openapi_responses_examples import OpenApiUnauthenticated401Response


User = get_user_model()


class LikeMixin:
    """
    Mixin, добавляющий ViewSet действия для работы с лайками объекта.

    Добавляет два кастомных endpoint'а:

    1) toggle-like (POST):
    Инвертирует лайк пользователя:
    - если пользователь еще не лайкал объект — лайк добавляется;
    - если лайк уже существует — лайк удаляется.

    2) likers-list (GET):
    Возвращает список пользователей, поставивших лайк объекту.
    """

    @extend_schema(
        summary="Переключение лайка (поставить или убрать) на объекте.",
        request=None,
        responses={
            200: OpenApiResponse(
                description="Статус лайка успешно изменен.",
                response=inline_serializer(
                    name="LikeToggleSerializer",
                    fields={
                        "liked_now": serializers.BooleanField(),
                        "likes_count_on_object": serializers.IntegerField(),
                    },
                ),
            ),
            401: OpenApiUnauthenticated401Response,
            404: create_new_not_found_response('"Object"'),
        },
    )
    @action(
        detail=True, methods=["post"], permission_classes=[IsAuthenticated], url_path="toggle-like"
    )
    def like(self, request, *args, **kwargs):
        """
        Кастомное действие, которое инвертирует лайк от пользователя к объекту:
        ставит, если нет, убирает, если есть.
        """
        obj = self.get_object()  # type: ignore[attr-defined]
        user = request.user

        liked_now, likes_count = perform_toggle_like(user, obj, source="api")

        return Response({"liked_now": liked_now, "likes_count_on_object": likes_count})

    @extend_schema(
        summary="Список пользователей, лайкнувших объект.",
        auth=[],
        responses={
            200: OpenApiResponse(
                description="Список пользователей успешно получен.",
                response=AuthorSerializer(many=True),
            ),
            404: create_new_not_found_response('"Object"'),
        },
    )
    @action(detail=True, methods=["get"], url_path="likers-list")
    def likes(self, request, *args, **kwargs):
        """
        Кастомное действие, которое возвращает список пользователей, лайкнувших объект.
        """
        obj = self.get_object()  # type: ignore[attr-defined]
        user_ids = obj.likes.values_list("user_id", flat=True)
        queryset = User.objects.filter(id__in=user_ids).order_by("id")

        page = self.paginate_queryset(queryset)  # type: ignore[attr-defined]
        if page is not None:
            serializer = AuthorSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)  # type: ignore[attr-defined]

        serializer = AuthorSerializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="Список постов.",
        description=(
            "Возвращает список постов с аннотацией `user_has_liked`.\n\n"
            "**Фильтрация (GET):**\n"
            "- `q`: Поиск по тексту в названии, контенте или именах тегов.\n"
            "- `tags`: Теги через запятую.\n"
            "- `tag_match`: Логика совпадения тегов (`any` / `all`).\n"
            "- `author`: Имя автора (не зависит от регистра).\n"
            "- `has_comments`: Наличие комментариев (`yes` / `no` / `any`).\n\n"
            "**Сортировка (GET):**\n"
            "- `sort`: Поле сортировки (`created`, `likes`, `comments`).\n"
            "- `order`: Направление (`asc`, `desc`)."
        ),
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Поиск по тексту в названии, контенте или именах тегов.",
            ),
            OpenApiParameter(
                name="tags",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Теги через запятую (например: python,django).",
            ),
            OpenApiParameter(
                name="tag_match",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Логика совпадения тегов.",
                enum=["any", "all"],
                default="any",
            ),
            OpenApiParameter(
                name="author",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Имя автора (не зависит от регистра).",
            ),
            OpenApiParameter(
                name="has_comments",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Фильтр по наличию комментариев.",
                enum=["yes", "no", "any"],
                default="any",
            ),
            OpenApiParameter(
                name="sort",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Поле для сортировки.",
                enum=["created", "likes", "comments"],
                default="created",
            ),
            OpenApiParameter(
                name="order",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Направление сортировки.",
                enum=["asc", "desc"],
                default="desc",
            ),
        ],
        auth=[],
        responses={
            200: OpenApiResponse(
                description="Список постов успешно получен.", response=PostSerializer(many=True)
            ),
            404: PaginationErrorOpenApiResponse,
        },
    ),
    retrieve=extend_schema(
        summary="Просмотр конкретного поста.",
        description="Возвращает детальную информацию о посте.",
        auth=[],
        responses={
            200: OpenApiResponse(
                description="Данные поста успешно получены.", response=PostSerializer
            ),
            404: create_new_not_found_response("Post"),
        },
    ),
    create=extend_schema(
        summary="Создание нового поста.",
        description="Создает новый пост с текущим пользователем в качестве автора.",
        responses={
            201: OpenApiResponse(description="Пост успешно создан.", response=PostSerializer),
            400: PostFieldErrorValidationOpenApiResponse,
            401: OpenApiUnauthenticated401Response,
        },
    ),
    partial_update=extend_schema(
        summary="Частичное обновление поста.",
        description="Изменяет переданные поля поста. Доступно автору или модератору.",
        responses={
            200: OpenApiResponse(description="Пост успешно обновлен.", response=PostSerializer),
            400: PostFieldErrorValidationOpenApiResponse,
            401: OpenApiUnauthenticated401Response,
            403: PermissionDeniedOpenApiResponse,
            404: create_new_not_found_response("Post"),
        },
    ),
    destroy=extend_schema(
        summary="Удаление поста.",
        description="Удаляет пост. Доступно автору или модератору.",
        responses={
            204: OpenApiResponse(
                description="Пост успешно удален.",
                response=DetailSerializer,
            ),
            401: OpenApiUnauthenticated401Response,
            403: PermissionDeniedOpenApiResponse,
            404: create_new_not_found_response("Post"),
        },
    ),
)
class PostViewSet(
    PostAnnotateQuerysetMixin,
    PostFilterSortMixin,
    LikeMixin,
    ModelViewSet,
):
    """
    ViewSet для обработки api запросов постов.

    Добавляет аннотированные поля, реализует фильтрацию и сортировку.
    Логирует действия, связанные с постами.
    """

    queryset = Post.objects.all()
    serializer_class = PostSerializer
    moderator_permission_name = "posts.moderate_post"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        """
        Логика прав доступа:
        - Просмотр (list, retrieve): Доступно всем.
        - Создание (create): Только авторизованным пользователям.
        - Изменение/Удаление (update, partial_update, destroy): Автору или Модератору.
        """
        if self.action in ["create", "like"]:
            return [IsAuthenticated()]

        if self.action in ["update", "partial_update", "destroy"]:
            return [
                IsAuthenticated(),
                IsAuthorOrModeratorPermission(moderate_permission=self.moderator_permission_name),
            ]

        return [AllowAny()]

    def get_object(self):
        """
        Возвращает объект поста с кешированием и добавляет
        пользовательский флаг user_has_liked.
        """
        queryset = self.filter_queryset(self.get_queryset())

        post = get_cached_post(
            post_id=self.kwargs[self.lookup_field],
            queryset=queryset,
        )

        self.check_object_permissions(self.request, post)

        # Добавляет объекту флаг лайка от пользователя
        return self.set_user_has_liked(post)

    def get_queryset(self):
        """
        Использует:
        - ContextTagMixin: для добавления тегов в контекст.
        - PostAnnotateQuerysetMixin: select_related, prefetch_related и аннотации.
        - PostFilterSortMixin: фильтрация и сортировка.
        """

        queryset = super().get_queryset()

        if self.action == "list":
            # Фильтрация по полям модели (через PostFilterSortMixin)
            queryset = self.filter_by_model_fields(queryset, self.request)

            # select_related, prefetch_related и аннотации (через PostAnnotateQuerysetMixin)
            queryset = self.get_annotate_queryset(queryset)

            # Фильтрация и сортировка по денормализованным полям-счетчикам
            # (через PostFilterSortMixin)
            queryset = self.filter_and_sort_by_counters(queryset, self.request)
        else:
            # select_related и prefetch_related через PostAnnotateQuerysetMixin
            queryset = self.prepare_post_queryset(queryset)

        return queryset

    def perform_create(self, serializer):
        """Создание поста с добавлением текущего пользователя."""
        post = serializer.save(author=self.request.user)
        log_post_event("post_create", post, self.request.user, source="api")

    def perform_update(self, serializer):
        post = serializer.save()
        log_post_event("post_update", post, self.request.user, source="api")

    def perform_destroy(self, instance):
        log_post_event("post_delete", instance, self.request.user, source="api")
        instance.delete()


@extend_schema_view(
    list=extend_schema(
        summary="Список комментариев к посту.",
        description=(
            "Возвращает дерево комментариев (родительские комментарии "
            "с предзагруженными дочерними ответами) для конкретного поста.\n\n"
            "**Сортировка (GET):**\n"
            "- `comment_sort`: Поле сортировки (`date`, `likes`).\n"
            "- `comment_order`: Направление (`asc`, `desc`)."
        ),
        parameters=[
            OpenApiParameter(
                name="comment_sort",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Поле для сортировки комментариев.",
                enum=["date", "likes"],
                default="date",
            ),
            OpenApiParameter(
                name="comment_order",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Направление сортировки.",
                enum=["asc", "desc"],
                default="desc",
            ),
        ],
        auth=[],
        responses={
            200: OpenApiResponse(
                description="Дерево комментариев успешно получено.",
                response=CommentSerializer(many=True),
            ),
            404: create_new_not_found_response("Post"),
        },
    ),
    retrieve=extend_schema(
        summary="Просмотр конкретного комментария.",
        description="Возвращает детальную информацию о конкретном комментарии поста.",
        auth=[],
        responses={
            200: OpenApiResponse(
                description="Данные комментария успешно получены.", response=CommentSerializer
            ),
            404: create_new_not_found_response('"Object"'),
        },
    ),
    create=extend_schema(
        summary="Создание нового комментария.",
        description="Создает новый комментарий (или ответ на другой комментарий) "
        "к указанному посту от имени текущего авторизованного пользователя.",
        responses={
            201: OpenApiResponse(
                description="Комментарий успешно создан.", response=CommentSerializer
            ),
            400: CommentFieldErrorValidationOpenApiResponse,
            401: OpenApiUnauthenticated401Response,
            404: create_new_not_found_response('"Object"'),
        },
    ),
    partial_update=extend_schema(
        summary="Частичное обновление комментария.",
        description="Изменяет текст комментария. Доступно автору или модератору.",
        responses={
            200: OpenApiResponse(
                description="Комментарий успешно обновлен.", response=CommentSerializer
            ),
            400: CommentFieldErrorValidationOpenApiResponse,
            401: OpenApiUnauthenticated401Response,
            403: PermissionDeniedOpenApiResponse,
            404: create_new_not_found_response('"Object"'),
        },
    ),
    destroy=extend_schema(
        summary="Удаление комментария.",
        description="Удаляет комментарий. Доступно автору или модератору.",
        responses={
            204: OpenApiResponse(
                description="Комментарий успешно удален.",
            ),
            401: OpenApiUnauthenticated401Response,
            403: PermissionDeniedOpenApiResponse,
            404: create_new_not_found_response('"Object"'),
        },
    ),
)
class CommentViewSet(
    LikeAnnotationsMixin,
    CommentSortMixin,
    CommentTreeQuerysetMixin,
    LikeMixin,
    ModelViewSet,
):
    """
    ViewSet для обработки api запросов комментариев.

    Реализует логику вложенных комментариев (1 уровень вложенности).
    """

    pagination_class = PostCommentsPagination
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    moderator_permission_name = "posts.moderate_comment"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        """
        Логика прав доступа:
        - Просмотр (list, retrieve): Доступно всем.
        - Создание (create): Только авторизованным пользователям.
        - Изменение/Удаление (update, partial_update, destroy): Автору или Модератору.
        """
        if self.action in ["create", "like"]:
            return [IsAuthenticated()]

        if self.action in ["update", "partial_update", "destroy"]:
            return [
                IsAuthenticated(),
                IsAuthorOrModeratorPermission(moderate_permission=self.moderator_permission_name),
            ]

        return [AllowAny()]

    def get_queryset(self):
        """
        Возвращает оптимизированный queryset родительских комментариев с
        prefetch_related queryset дочерних комментариев.
        """
        post = self.get_post()

        if self.action == "list":
            # queryset родительских комментариев с prefetch_related queryset дочерних комментариев
            # для отображения списка комментариев поста
            queryset = self.get_comment_tree_queryset(post)
        else:
            # select_related автора и аннотирование комментария для его детального отображения
            queryset = super().get_queryset().filter(post_id=post.pk).select_related("author")
            # Аннотирование полями для лайков
            queryset = self.annotate_queryset(queryset)

        queryset = queryset.annotate(children_count=Count("child_comments", distinct=True))

        return queryset

    @extend_schema(
        summary="Получение ветки комментариев (ответов) конкретного комментария.",
        auth=[],
        responses={
            200: OpenApiResponse(
                description="Ветка комментариев успешно получена.", response=CommentSerializer
            ),
            404: create_new_not_found_response('"Object"'),
        },
    )
    @action(detail=True, methods=["get"])
    def thread(self, request, post_pk=None, pk=None):
        """
        Кастомное действие для получения полной ветки обсуждения конкретного комментария.

        Если передан pk дочернего комментария, метод найдет родительский комментарий
        и отобразит его ветку.
        """
        instance = get_object_or_404(Comment, post_id=post_pk, pk=pk)

        # Определение id корня ветки (родительского комментария)
        root_id = instance.parent_comment_id if instance.parent_comment_id else instance.pk

        queryset = self.get_comment_tree_queryset(post=self.get_post(), root_id=root_id)

        queryset = queryset.annotate(children_count=Count("child_comments", distinct=True))

        root_comment = queryset.first()

        serializer = self.get_serializer(root_comment)
        return Response(serializer.data)

    def get_serializer_context(self):
        """Передает post в serializer context."""
        context = super().get_serializer_context()
        context["post"] = self.get_post()
        context["display_tree"] = self.action in ["list", "thread"]
        return context

    def get_post(self):
        """Получает пост и кеширует его."""
        if not hasattr(self, "_post"):
            self._post = get_object_or_404(Post, pk=self.kwargs["post_pk"])
        return self._post

    def perform_create(self, serializer):
        """Создание комментария с добавлением текущего пользователя и указанного pk поста."""
        comment = serializer.save(author=self.request.user, post_id=self.kwargs["post_pk"])
        user = self.request.user
        log_comment_event("comment_create", comment, user, source="api")

    def perform_update(self, serializer):
        comment = serializer.save()
        user = self.request.user
        log_comment_event("comment_update", comment, user, source="api")

    def perform_destroy(self, instance):
        comment = instance
        user = self.request.user
        log_comment_event("comment_delete", comment, user, source="api")
        instance.delete()


@extend_schema_view(
    list=extend_schema(
        summary="Список всех тегов.",
        description=(
            "Возвращает список всех тегов, отсортированных по имени.\n\n"
            "**Поиск (GET):**\n"
            "- Поддерживает поиск по совпадению подстроки в имени тега с "
            "помощью параметра `?search=`."
        ),
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Поиск тегов по названию (без учета регистра).",
            ),
        ],
        auth=[],
        responses={
            200: OpenApiResponse(
                description="Список тегов успешно получен.",
                response=TagSerializer(many=True),
            )
        },
    ),
    retrieve=extend_schema(
        summary="Просмотр конкретного тега.",
        description="Возвращает информацию о теге по его ID.",
        auth=[],
        responses={
            200: OpenApiResponse(
                description="Информация о теге успешно получена.",
                response=TagSerializer,
            ),
            404: create_new_not_found_response('"LowercaseTag"'),
        },
    ),
)
class TagReadOnlyViewSet(ReadOnlyModelViewSet):
    """
    API endpoint для просмотра списка тегов.

    Поддерживает поиск по подстроке: ?search=python.

    Для кеширования тегов вместо переопределения list и использования готового
    сервиса get_cached_tags можно использовать:
        @method_decorator(cache_page(2))
        def dispatch(self, *args, **kwargs):
            return super().dispatch(*args, **kwargs)
    Но тогда кешироваться будут любые запросы, и с GET-параметром search тоже.
    """

    queryset = LowercaseTag.objects.all().order_by("name")
    serializer_class = TagSerializer
    pagination_class = None
    filter_backends = [SearchFilter]
    search_fields = ["name"]

    def list(self, request, *args, **kwargs):  # noqa: A003
        """
        Использует кешированный список тегов, если не задан GET-параметр search.
        """
        search_query = request.query_params.get("search", "").lower()

        if search_query:
            # Если задан GET-параметр search, то кеш, содержащий все теги, не используется
            return super().list(request, *args, **kwargs)

        # Если фильтрации нет, то используется кеш
        tags = get_cached_tags()

        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)
