from django.db.models import Count
from posts.api.permissions import IsAuthorOrModeratorPermission
from posts.api.serializers import CommentSerializer, PostSerializer
from posts.models import Comment, Post
from posts.services import log_comment_event, log_post_event
from posts.views.mixins import (
    CommentSortMixin,
    CommentTreeQuerysetMixin,
    LikeAnnotationsMixin,
    PostAnnotateQuerysetMixin,
    PostFilterSortMixin,
)
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


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
        post = serializer.save()
        log_post_event("post_update", post, self.request.user, source="api")

    def perform_destroy(self, instance):
        log_post_event("post_delete", instance, self.request.user, source="api")
        instance.delete()


class CommentViewSet(
    LikeAnnotationsMixin,
    CommentSortMixin,
    CommentTreeQuerysetMixin,
    ModelViewSet,
):
    """
    ViewSet для обработки api запросов комментариев.

    Реализует логику вложенных комментариев (1 уровень вложенности).
    """

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    moderator_permission_name = "posts.moderate_comment"

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
        Возвращает оптимизированный queryset родительских комментариев с
        prefetch_related queryset дочерних комментариев.
        """
        post = self.get_post()

        if self.action == "list":
            # queryset родительских комментариев с prefetch_related queryset дочерних комментариев
            # для отображения списка комментариев поста
            queryset = self.get_comment_tree_queryset(post)
        else:
            # select_related автора и аннотирование поста для детального отображения 1 поста
            queryset = super().get_queryset().filter(post_id=post.pk).select_related("author")
            # Аннотирование полями для лайков
            queryset = self.annotate_queryset(queryset)

        queryset = queryset.annotate(children_count=Count("child_comments"))

        return queryset

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

        queryset = queryset.annotate(children_count=Count("child_comments"))

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
