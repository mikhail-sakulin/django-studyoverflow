from posts.api.permissions import IsAuthorOrModeratorPermission
from posts.api.serializers import PostSerializer
from posts.models import Post
from posts.services import log_post_event
from posts.views.mixins import PostAnnotateQuerysetMixin, PostFilterSortMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet


class PostViewSetPagination(PageNumberPagination):
    """
    Пагинация для постов и комментариев.
    """

    page_size = 7
    page_size_query_param = "page_size"
    max_page_size = 100


class PostViewSet(
    PostAnnotateQuerysetMixin,
    PostFilterSortMixin,
    ModelViewSet,
):
    """
    ViewSet для обработки api запросов постов.

    Добавляет аннотированные поля, реализует фильтрацию и сортировку.
    Логирует действия, связанные с постами.
    """

    queryset = Post.objects.all()
    serializer_class = PostSerializer
    pagination_class = PostViewSetPagination
    moderator_permission_name = "posts.moderate_post"

    def get_permissions(self):
        """
        Логика прав доступа:
        - Просмотр (list, retrieve): Доступно всем.
        - Создание (create): Только авторизованным пользователям.
        - Изменение/Удаление (update, partial_update, destroy): Автору или Модератору.
        """
        if self.action == "create":
            return [IsAuthenticated()]

        if self.action in ["update", "partial_update", "destroy"]:
            return [
                IsAuthenticated(),
                IsAuthorOrModeratorPermission(moderate_permission=self.moderator_permission_name),
            ]

        return [AllowAny()]

    def get_queryset(self):
        """
        Использует:
        - ContextTagMixin: для добавления тегов в контекст.
        - PostAnnotateQuerysetMixin: select_related, prefetch_related и аннотации.
        - PostFilterSortMixin: фильтрация и сортировка.
        """

        queryset = super().get_queryset()

        # Фильтрация по полям модели (через PostFilterSortMixin)
        queryset = self.filter_by_model_fields(queryset, self.request)

        # select_related, prefetch_related и аннотации (через PostAnnotateQuerysetMixin)
        queryset = self.get_annotate_queryset(queryset)

        # Фильтрация и сортировка по аннотированным полям (через PostFilterSortMixin)
        queryset = self.filter_and_sort_by_annotations(queryset, self.request)

        return queryset

    def perform_create(self, serializer):
        """Создание поста с добавлением текущего пользователя."""
        post = serializer.save(author=self.request.user)
        log_post_event("post_create", post, self.request.user, source="api")

    def perform_update(self, serializer):
        post = super().perform_update(serializer)
        log_post_event("post_update", post, self.request.user, source="api")

    def perform_destroy(self, instance):
        log_post_event("post_delete", instance, self.request.user, source="api")
        instance.delete()
