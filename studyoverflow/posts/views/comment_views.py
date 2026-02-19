import json
import logging

from django.contrib import messages
from django.db.models import Count, Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from posts.forms import CommentCreateForm, CommentUpdateForm
from posts.models import Comment, Post
from users.views.mixins import IsAuthorOrModeratorMixin

from .mixins import (
    CommentGetMethodMixin,
    CommentSortMixin,
    HTMXHandle404CommentMixin,
    HTMXMessageMixin,
    LikeAnnotationsMixin,
    LoginRequiredHTMXMixin,
    SingleObjectCacheMixin,
)


logger = logging.getLogger(__name__)


class CommentListView(LikeAnnotationsMixin, CommentSortMixin, ListView):
    """
    Страница со списком комментариев к посту с аннотациями и сортировкой.
    """

    model = Comment
    template_name = "posts/comments/comment_list.html"
    context_object_name = "root_comments"

    def _get_post_object(self):
        """
        Возвращает кешированный объект поста, к которому относятся комментарии.
        """
        if not hasattr(self, "_post_object"):
            post_pk = self.kwargs.get("post_pk")
            self._post_object = get_object_or_404(
                Post.objects.annotate(comments_count=Count("comments")), pk=post_pk
            )
        return self._post_object

    def get_queryset(self):
        """
        Возвращает queryset родительских комментариев с
        prefetch_related queryset дочерних комментариев.

        Используются select_related для оптимизации запроса и аннотации.
        """
        post = self._get_post_object()

        child_queryset = self.annotate_queryset(
            Comment.objects.select_related(
                "author", "post", "reply_to", "reply_to__author"
            ).order_by("-time_create")
        )

        queryset = (
            post.comments.roots()
            .select_related("author", "post")
            # prefetch_related для обратного доступа ForeignKey через related_name
            .prefetch_related(Prefetch("child_comments", queryset=child_queryset))
            .order_by("-time_create")
        )

        queryset = self.annotate_queryset(queryset)

        queryset = self.sort_comments(queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self._get_post_object()
        context["post"] = post
        context["comment_form"] = CommentCreateForm()
        return context


class CommentRootCreateView(
    LoginRequiredHTMXMixin, HTMXMessageMixin, CommentGetMethodMixin, CreateView
):
    """
    Создание родительского комментария к посту.

    Работает с HTMX для создания комментария и обновления списка комментариев
    без перезагрузки страницы.
    Логирует создание комментария.
    """

    model = Comment
    form_class = CommentCreateForm
    template_name = "posts/comments/_comment_root_form.html"

    def get_form_kwargs(self):
        """
        Добавляет в kwargs пользователя и пост, к которому пишется комментарий.
        """
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        if not hasattr(self, "_cached_post"):
            self._cached_post = get_object_or_404(Post, id=self.kwargs.get("post_pk"))
        kwargs["post"] = self._cached_post
        return kwargs

    def get_context_data(self, form, form_valid=True, **kwargs):
        context = super().get_context_data(**kwargs)
        context.pop("form")
        reply_to = form.cleaned_data.get("reply_to")
        context = {
            "post": form.post,
            "comment": reply_to,
            "comment_form": self.form_class() if form_valid else form,
        }
        return context

    def form_valid(self, form):
        form.instance.post = form.post
        form.instance.author = self.request.user
        self.object = form.save()

        context = self.get_context_data(form, form_valid=True)

        logger.info(
            f"Создан комментарий (id: {self.object.pk}) к посту (id: {form.post.pk}).",
            extra={
                "comment_id": self.object.pk,
                "post_id": form.post.pk,
                "author_id": self.request.user.pk,
                "event_type": "comment_create",
            },
        )

        response = render(self.request, self.template_name, context)
        response["HX-Trigger"] = json.dumps({"commentsUpdated": {}, "commentRootFormSuccess": {}})

        # add htmx_message to response
        return self.htmx_message(
            message_text="Комментарий создан.", message_type="success", response=response
        )

    def form_invalid(self, form):
        context = self.get_context_data(form, form_valid=False)

        response = render(self.request, self.template_name, context)
        response["HX-Trigger"] = json.dumps({"commentRootFormError": {}})

        return response


class CommentChildCreateView(CommentRootCreateView):
    """
    Создание дочернего комментария в ответ на другой комментарий (reply_to).

    Расширяет CommentRootCreateView.
    """

    template_name = "posts/comments/_comment_child_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)

        reply_to = form.cleaned_data.get("reply_to")

        # Определяется commentId для события
        comment_id = reply_to.pk

        # Передаются данные в формате JSON для HX-Trigger
        response["HX-Trigger"] = json.dumps(
            {"commentsUpdated": {}, "commentChildFormSuccess": {"commentId": comment_id}}
        )

        return self.htmx_message(
            message_text="Комментарий создан.", message_type="success", response=response
        )

    def form_invalid(self, form):
        response = super().form_invalid(form)

        reply_to = form.cleaned_data.get("reply_to")

        if not reply_to:
            # Когда указан некорректный reply_to, ошибки формы
            # выводятся в messages (нет формы, где их выводить).
            self._add_errors_to_messages(form)
            # Страница перезагружается для корректировки отображаемых данных.
            response["HX-Refresh"] = "true"
            return response

        comment_id = reply_to.pk

        response["HX-Trigger"] = json.dumps({"commentChildFormError": {"commentId": comment_id}})

        return response

    def _add_errors_to_messages(self, form):
        """
        Добавляет ошибки формы в messages для отображения у клиента.
        """
        messages.error(self.request, "Возможно, комментарий был удален.")
        for field, errors in form.errors.items():
            for error in errors:
                if field == "__all__":
                    # ошибки на уровне формы
                    messages.error(self.request, f"Ошибка: {error}")
                else:
                    # ошибки конкретного поля
                    messages.error(self.request, f'Ошибка в "{form.fields[field].label}": {error}')


class CommentUpdateView(
    LoginRequiredHTMXMixin,
    HTMXMessageMixin,
    IsAuthorOrModeratorMixin,
    SingleObjectCacheMixin,
    LikeAnnotationsMixin,
    HTMXHandle404CommentMixin,
    CommentGetMethodMixin,
    UpdateView,
):
    """
    Изменение комментария к посту.

    Работает с HTMX для изменения комментария и обновления его содержимого
    без перезагрузки страницы.
    Логирует изменение комментария.
    """

    model = Comment
    form_class = CommentUpdateForm
    pk_url_kwarg = "comment_pk"
    template_name = "posts/comments/_comment_card.html"
    permission_required = "posts.moderate_comment"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("author", "post")
        queryset = self.annotate_queryset(queryset)
        return queryset

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(**kwargs)
        context.pop("form")
        context = {
            "comment_update_form": form,
            "comment_form": self.form_class(),
            "comment": self.object,
            "post": self.object.post,
        }
        return context

    def form_valid(self, form):
        self.object = form.save()
        context = self.get_context_data(form)

        logger.info(
            f"Комментарий обновлен (id: {self.object.pk}) "
            f"пользователем {self.request.user.username}.",
            extra={
                "comment_id": self.object.pk,
                "post_id": self.object.post.pk,
                "user_id": self.request.user.pk,
                "event_type": "comment_update",
            },
        )

        response = render(self.request, self.template_name, context)
        response["HX-Trigger"] = json.dumps({"commentUpdateSuccess": {"commentId": self.object.pk}})

        return self.htmx_message(
            message_text="Комментарий изменен.", message_type="success", response=response
        )

    def form_invalid(self, form):
        context = self.get_context_data(form)

        response = render(self.request, self.template_name, context)
        response["HX-Trigger"] = json.dumps({"commentUpdateError": {"commentId": self.object.pk}})
        return response


class CommentDeleteView(
    LoginRequiredHTMXMixin,
    HTMXMessageMixin,
    HTMXHandle404CommentMixin,
    IsAuthorOrModeratorMixin,
    SingleObjectCacheMixin,
    CommentGetMethodMixin,
    DeleteView,
):
    """
    Удаление комментария к посту.

    Работает с HTMX для удаления комментария и обновления списка комментариев
    без перезагрузки страницы.
    Логирует удаление комментария.
    """

    model = Comment
    pk_url_kwarg = "comment_pk"
    permission_required = "posts.moderate_comment"

    def form_valid(self, form):
        comment_id = self.object.pk
        post_id = self.object.post.pk
        self.object.delete()

        logger.info(
            f"Комментарий удален (id: {comment_id}).",
            extra={
                "comment_id": comment_id,
                "post_id": post_id,
                "user_id": self.request.user.pk,
                "event_type": "comment_delete",
            },
        )

        response = HttpResponse()
        response["HX-Trigger"] = json.dumps({"commentsUpdated": {}})

        return self.htmx_message(
            message_text="Комментарий удален.", message_type="info", response=response
        )
