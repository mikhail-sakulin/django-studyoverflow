from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model

from posts.api.permissions import IsAuthorOrModeratorPermission


User = get_user_model()


@pytest.mark.django_db
class TestIsAuthorOrModeratorPermission:
    """Тестирование permission-класса IsAuthorOrModeratorPermission."""

    def test_permission_allows_author(self, user_factory, post_factory):
        """Доступ разрешен, если пользователь является автором объекта."""
        author = user_factory()
        post = post_factory(author=author)

        permission = IsAuthorOrModeratorPermission(moderate_permission="posts.moderate_post")
        request = SimpleNamespace(user=author)

        assert permission.has_object_permission(request, None, post) is True

    def test_permission_allows_moderator(self, user_factory, post_factory):
        """Доступ разрешен, если у пользователя есть права модератора."""
        author = user_factory()
        moderator = user_factory(role=User.Role.MODERATOR)
        post = post_factory(author=author)

        permission = IsAuthorOrModeratorPermission(moderate_permission="posts.moderate_post")
        request = SimpleNamespace(user=moderator)

        assert permission.has_object_permission(request, None, post) is True

    def test_permission_denies_regular_user(self, user_factory, post_factory):
        """Доступ запрещен для пользователя, который не автор и не модератор."""
        author = user_factory()
        regular_user = user_factory()
        post = post_factory(author=author)

        permission = IsAuthorOrModeratorPermission(moderate_permission="posts.moderate_post")
        request = SimpleNamespace(user=regular_user)

        assert permission.has_object_permission(request, None, post) is False
