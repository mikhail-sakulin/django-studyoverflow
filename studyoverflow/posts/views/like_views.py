import json
import logging
from abc import ABC, abstractmethod
from typing import Type

from django.contrib import messages
from django.db import models
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from posts.models import Comment, Post

from .mixins import HTMXMessageMixin, LoginRequiredHTMXMixin


logger = logging.getLogger(__name__)


class ToggleLikeBaseView(LoginRequiredHTMXMixin, HTMXMessageMixin, View, ABC):
    """
    Абстрактное базовое представление для добавления/удаления лайков.

    Работает с HTMX и логирует действия с лайками.
    """

    model: Type[models.Model]
    pk_url_kwarg: str = "pk"

    @abstractmethod
    def _get_toggle_like_url(self, liked_object: models.Model) -> str:
        """
        Должен возвращать URL для кнопки лайка.

        Нужно переопределять в дочерних классах."""
        pass

    def post(self, request, *args, **kwargs):
        """
        Добавляет или удаляет лайк для объекта.

        Возвращает HTMX-ответ с количеством лайков или триггером с перезагрузкой страницы
        в случае отсутствия объекта (DoesNotExist).
        """
        try:
            liked_object = self.model.objects.get(pk=kwargs[self.pk_url_kwarg])
        except self.model.DoesNotExist:
            response = HttpResponse(status=404)
            response["HX-Trigger"] = json.dumps({"reloadPage": True})

            messages.error(self.request, "Ресурс был удален.")

            return response

        like, created = liked_object.likes.get_or_create(user=request.user)

        if not created:
            like.delete()
            message_text = "Лайк удален."
            message_type = "info"
        else:
            message_text = "Лайк добавлен."
            message_type = "success"

        event_type = "like_add" if created else "like_remove"

        logger.info(
            f"Лайк {event_type} для {self.model.__name__} (id: {liked_object.pk}).",
            extra={
                "object_type": self.model.__name__.lower(),
                "object_id": liked_object.pk,
                "user_id": request.user.pk,
                "event_type": event_type,
            },
        )

        context = {
            "toggle_like_url": self._get_toggle_like_url(liked_object),
            "liked_object": liked_object,
            "likes_count": liked_object.likes.count(),
            "user_has_liked": created,
        }

        response = render(request, "posts/likes/_like-button.html", context)

        response = self.add_htmx_message_to_response(
            message_text=message_text, message_type=message_type, response=response
        )

        return response


class ToggleLikePostView(ToggleLikeBaseView):
    """
    Лайк / удаление лайка для поста.
    """

    model = Post
    pk_url_kwarg = "post_pk"

    def _get_toggle_like_url(self, post):
        """Возвращает URL для кнопки лайка поста."""
        return reverse_lazy(
            "posts:toggle_like_post", kwargs={"post_pk": post.pk, "post_slug": post.slug}
        )


class ToggleLikeCommentView(ToggleLikeBaseView):
    """
    Лайк / удаление лайка для комментария.
    """

    model = Comment
    pk_url_kwarg = "comment_pk"

    def _get_toggle_like_url(self, comment):
        """Возвращает URL для кнопки лайка комментария."""
        return reverse_lazy(
            "posts:toggle_like_comment",
            kwargs={
                "post_pk": comment.post.pk,
                "post_slug": comment.post.slug,
                "comment_pk": comment.pk,
            },
        )
