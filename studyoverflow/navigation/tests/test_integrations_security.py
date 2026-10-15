"""
Интеграционные тесты безопасности проекта Studyoverflow.

Проверяют:
- защиту от изменения значений для API-запросов, которые пользователь менять сам не должен (для
  пользователей, постов и комментариев);
- сквозной сценарий: заблокированный пользователь теряет доступ через все способы аутентификации
  (сессия, DRF-токен, JWT), после разблокировки доступ восстанавливается.

Модерация постов, комментариев и пользователей проверяется в соответствующих тестах сервисов,
web- и api-views приложений.
"""

from typing import Final

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient

from posts.models import Comment, Post


User = get_user_model()


# Поля модели User, которые пользователь не может менять и задавать сам
PROTECTED_USER_FIELDS: Final[tuple[str, ...]] = (
    "role",
    "is_staff",
    "is_superuser",
    "is_blocked",
    "blocked_at",
    "blocked_by",
    "reputation",
    "posts_count",
    "comments_count",
    "is_social",
    "date_joined",
    "last_seen",
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Очищает кеш до и после каждого теста."""
    cache.clear()
    yield
    cache.clear()


def get_clients_for_all_api_auth_methods(username: str, password: str) -> dict[str, APIClient]:
    """Возвращает api-клиентов, аутентифицированных каждым из способов."""
    data = {"username": username, "password": password}

    session_client = APIClient()
    response = session_client.post(reverse("api:users:auth-session-login"), data, format="json")
    assert response.status_code == 200

    response = APIClient().post(reverse("api:users:auth-drf-token-login"), data, format="json")
    assert response.status_code == 200
    drf_client = APIClient()
    drf_client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['drf_token']}")

    response = APIClient().post(reverse("api:users:jwt_login"), data, format="json")
    assert response.status_code == 200
    jwt_client = APIClient()
    jwt_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    return {"session": session_client, "DRF-token": drf_client, "JWT-access": jwt_client}


@pytest.mark.django_db
class TestFieldsProtection:
    """
    Поля, которые не может поменять сам пользовать и которые управляются сервером, игнорируются,
    если клиент передает их в теле запроса.
    """

    def test_me_patch_ignores_protected_fields(self, api_client, user_factory):
        """
        Пользователь через API (PATCH /users/me/) меняет только разрешенные поля, остальные поля
        из тела запроса игнорируются.
        """
        user = user_factory(role=User.Role.USER, reputation=5)
        other = user_factory()
        before = User.objects.filter(pk=user.pk).values(*PROTECTED_USER_FIELDS).get()
        api_client.force_authenticate(user=user)

        response = api_client.patch(
            reverse("api:users:users-me"),
            {
                "first_name": "Ivan",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_blocked": True,
                "blocked_by": other.pk,
                "reputation": 9999,
                "posts_count": 9999,
                "comments_count": 9999,
                "is_social": True,
            },
            format="json",
        )

        assert response.status_code == 200
        # Разрешенное поле изменилось
        assert response.data["first_name"] == "Ivan"
        assert response.data["role"] == User.Role.USER

        user.refresh_from_db()
        assert user.first_name == "Ivan"
        # Неразрешенные поля не менялись
        assert User.objects.filter(pk=user.pk).values(*PROTECTED_USER_FIELDS).get() == before
        # Пользователь не состоит в группах
        assert not user.groups.exists()

    def test_register_ignores_privileged_fields(self, api_client):
        """Регистрация через API не позволяет задать неразрешенные поля."""
        response = api_client.post(
            reverse("api:users:auth-register"),
            {
                "username": "new_user",
                "email": "new_user@example.com",
                "password": "StrongPassword123",
                "password_confirm": "StrongPassword123",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_blocked": True,
                "reputation": 9999,
                "is_social": True,
            },
            format="json",
        )

        assert response.status_code == 201

        user = User.objects.get(username="new_user")
        assert user.role == User.Role.USER
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.is_blocked is False
        assert user.reputation == 0
        assert user.is_social is False
        assert not user.groups.exists()

    def test_post_create_ignores_server_controlled_fields(self, api_client, user_factory):
        """
        При создании поста через API определенные поля задаются сервером,
        а не клиентом в теле запроса.
        """
        user = user_factory()
        other = user_factory()
        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("api:posts:posts-list"),
            {
                "title": "New test post",
                "content": "Content",
                "tags": ["drf"],
                "author": other.pk,
                "slug": "hacked-slug",
                "likes_count": 999,
                "comments_count": 999,
                "rendered_content": "<script>alert(1)</script>",
            },
            format="json",
        )

        assert response.status_code == 201

        post = Post.objects.get(pk=response.data["id"])
        assert post.author == user
        assert post.slug == "new-test-post"
        assert (post.likes_count, post.comments_count) == (0, 0)
        assert "<script>" not in post.rendered_content

    def test_post_patch_ignores_server_controlled_fields(
        self, api_client, user_factory, post_factory
    ):
        """PATCH-запрос для поста меняет только разрешенные поля."""
        post = post_factory(title="Original post title")
        author_id, slug, rendered_content = post.author_id, post.slug, post.rendered_content
        other = user_factory()
        api_client.force_authenticate(user=post.author)

        response = api_client.patch(
            reverse("api:posts:posts-detail", kwargs={"pk": post.pk}),
            {
                "title": "Updated post title",
                "author": other.pk,
                "slug": "hacked-slug",
                "likes_count": 9999,
                "comments_count": 9999,
                "rendered_content": "<script>alert(1)</script>",
            },
            format="json",
        )

        assert response.status_code == 200

        post.refresh_from_db()
        assert post.title == "Updated post title"
        assert post.author_id == author_id
        assert post.slug == slug
        assert post.rendered_content == rendered_content
        assert (post.likes_count, post.comments_count) == (0, 0)

    def test_comment_create_ignores_server_controlled_fields(
        self, api_client, user_factory, post_factory
    ):
        """
        При создании комментария через API определенные поля задаются сервером,
        а не клиентом в теле запроса.
        """
        user = user_factory()
        other = user_factory()
        post = post_factory()
        other_post = post_factory()
        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("api:posts:post-comments-list", kwargs={"post_pk": post.pk}),
            {
                "content": "Comment",
                "post": other_post.pk,
                "author": other.pk,
                "likes_count": 9999,
                "rendered_content": "<script>alert(1)</script>",
            },
            format="json",
        )

        assert response.status_code == 201

        comment = Comment.objects.get(pk=response.data["id"])
        assert comment.post == post
        assert comment.author == user
        assert comment.likes_count == 0
        assert "<script>" not in comment.rendered_content
        assert not other_post.comments.exists()

    def test_comment_patch_ignores_server_controlled_fields(
        self, api_client, user_factory, post_factory, comment_factory
    ):
        """PATCH-запрос для комментария меняет только разрешенные поля."""
        post = post_factory()
        other_post = post_factory()
        root = comment_factory(post=post)
        other_root = comment_factory(post=post)
        child = comment_factory(
            post=post, parent_comment=root, reply_to=root, content="Old content"
        )
        author_id = child.author_id
        other = user_factory()
        api_client.force_authenticate(user=child.author)

        response = api_client.patch(
            reverse("api:posts:post-comments-detail", kwargs={"post_pk": post.pk, "pk": child.pk}),
            {
                "content": "New content",
                "parent_comment": other_root.pk,
                "reply_to": other_root.pk,
                "author": other.pk,
                "post": other_post.pk,
                "likes_count": 999,
            },
            format="json",
        )

        assert response.status_code == 200

        child.refresh_from_db()
        assert child.content == "New content"
        assert child.parent_comment_id == root.pk
        assert child.reply_to_id == root.pk
        assert child.author_id == author_id
        assert child.post_id == post.pk
        assert child.likes_count == 0


@pytest.mark.django_db
class TestBlockedUserLosesAccess:
    """
    Сценарий тестирования: заблокированный пользователь теряет доступ через все способы
    аутентификации (сессия, DRF-токен, JWT), после разблокировки доступ восстанавливается.
    """

    def test_block_revokes_all_access_and_unblock_restores_login(self, client, user_factory):
        password = "StrongPassword123"
        moderator = user_factory(role=User.Role.MODERATOR)
        target = user_factory(password=password)
        login_data = {"username": target.username, "password": password}
        me_url = reverse("api:users:users-me")

        moderator_client = APIClient()
        moderator_client.force_authenticate(user=moderator)

        # 1) До блокировки выданы сессия, DRF-токен и JWT access, все способы
        # аутентификации работают
        api_clients = get_clients_for_all_api_auth_methods(target.username, password)
        for name, api in api_clients.items():
            assert api.get(me_url).status_code == 200, name

        # 2) Модератор блокирует пользователя через API
        response = moderator_client.post(
            reverse("api:users:users-block", kwargs={"username": target.username})
        )
        assert response.status_code == 200
        target.refresh_from_db()
        assert target.is_blocked is True

        # 3) Аутентификация невозможна никаким из способов (используются новые api-клиенты)
        # Для api
        for url_name in (
            "api:users:auth-session-login",
            "api:users:auth-drf-token-login",
            "api:users:jwt_login",
        ):
            response = APIClient().post(reverse(url_name), login_data, format="json")
            assert response.status_code == 401, url_name

        # Для web
        response = client.post(reverse("users:login"), data=login_data)
        # Возвращается форма с ошибкой, редиректа нет
        assert response.status_code == 200
        assert "_auth_user_id" not in client.session

        # 4) Уже выданные сессия, DRF-токен и JWT-access не аутентифицируют
        # пользователя (проверяются уже существующие api_clients до аутентификаций)
        for name, api in api_clients.items():
            assert api.get(me_url).status_code == 401, name

        # Сессия не действительна и для web
        response = api_clients["session"].get(reverse("users:my_profile"))
        assert response.status_code == 302
        assert reverse("users:login") in response.url

        # 5) После разблокировки аутентификация снова доступна всеми способами
        response = moderator_client.post(
            reverse("api:users:users-unblock", kwargs={"username": target.username})
        )
        assert response.status_code == 200

        for name, api in get_clients_for_all_api_auth_methods(target.username, password).items():
            assert api.get(me_url).status_code == 200, name
