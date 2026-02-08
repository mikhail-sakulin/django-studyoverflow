from typing import Any

from django.shortcuts import get_object_or_404, redirect
from posts.models import Post


class CommentGetMethodMixin:
    kwargs: dict[str, Any]

    def get(self, request, *args, **kwargs):
        post_id = self.kwargs.get("post_pk")
        post = get_object_or_404(Post, id=post_id)
        return redirect("posts:detail", pk=post.pk, slug=post.slug)


class SingleObjectCacheMixin:
    """
    Обеспечивает кеширование объекта внутри одного запроса.
    """

    def get_object(self, queryset=None):
        if not hasattr(self, "object") or self.object is None:  # type: ignore[has-type]
            self.object = super().get_object(queryset)  # type: ignore[misc]
        return self.object
