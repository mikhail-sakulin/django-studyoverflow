import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from posts.api.permissions import IsAuthorOrModeratorPermission


User = get_user_model()


@pytest.fixture
def request_factory():
    return APIRequestFactory()


@pytest.mark.django_db
class TestIsAuthorOrModeratorPermission:
    """Тестирование permission-класса IsAuthorOrModeratorPermission."""

    def test_permission_allows_author(self, user_factory, post_factory, mocker, request_factory):
        """Доступ разрешен, если пользователь является автором объекта."""
        author = user_factory()
        post = post_factory(author=author)

        mock_service = mocker.patch(
            "posts.api.permissions.is_author_or_moderator", return_value=True
        )

        permission = IsAuthorOrModeratorPermission(moderate_permission="posts.moderate_post")
        request = request_factory.get("/")
        request.user = author

        assert permission.has_object_permission(request, None, post) is True
        mock_service.assert_called_once_with(
            user=author, obj=post, permission_required="posts.moderate_post"
        )

    def test_permission_allows_moderator(self, user_factory, post_factory, mocker, request_factory):
        """Доступ разрешен, если у пользователя есть права модератора."""
        author = user_factory()
        moderator = user_factory()
        post = post_factory(author=author)

        mock_service = mocker.patch(
            "posts.api.permissions.is_author_or_moderator", return_value=True
        )

        permission = IsAuthorOrModeratorPermission(moderate_permission="posts.moderate_post")
        request = request_factory.get("/")
        request.user = moderator

        assert permission.has_object_permission(request, None, post) is True
        mock_service.assert_called_once_with(
            user=moderator, obj=post, permission_required="posts.moderate_post"
        )

    def test_permission_denies_regular_user(
        self, user_factory, post_factory, request_factory, mocker
    ):
        """Доступ запрещен для пользователя, который не автор и не модератор."""
        author = user_factory()
        regular_user = user_factory()
        post = post_factory(author=author)

        mock_service = mocker.patch(
            "posts.api.permissions.is_author_or_moderator", return_value=False
        )

        permission = IsAuthorOrModeratorPermission(moderate_permission="posts.moderate_post")
        request = request_factory.get("/")
        request.user = regular_user

        assert permission.has_object_permission(request, None, post) is False
        mock_service.assert_called_once_with(
            user=regular_user, obj=post, permission_required="posts.moderate_post"
        )
