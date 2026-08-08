import re

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from users.services import get_user_cache_key


User = get_user_model()


@pytest.fixture(autouse=True)
def mock_redis_conn(mocker):
    """
    Автоматически мокает подключение к Redis во всех тестах.

    Часто нужен в тестах, поскольку в OnlineStatusMiddleware, если пользователь аутентифицирован,
    есть обращение к сервисной функции set_user_online, в которой есть прямое обращение к Redis.
    """
    mock_conn = mocker.patch("users.services.online.get_redis_connection")
    return mock_conn


@pytest.fixture()
def clear_cache():
    """Очищает кеш до и после теста."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestSessionLoginLogoutAPIView:
    """Тестирование session_login и session_logout."""

    def test_success_login(self, api_client, user_factory):
        """Успешная аутентификация создает сессию и возвращает профиль пользователя."""
        password = "StrongPassword123"
        user = user_factory(password=password)

        response = api_client.post(
            reverse("api:users:auth-session-login"),
            {
                "username": user.username,
                "password": password,
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["username"] == user.username
        assert "_auth_user_id" in api_client.session

    def test_invalid_credentials(self, api_client, user_factory):
        """Неверные учетные данные возвращают 401."""
        user = user_factory(password="StrongPassword123")

        response = api_client.post(
            reverse("api:users:auth-session-login"),
            {
                "username": user.username,
                "password": "WrongPassword123",
            },
            format="json",
        )

        assert response.status_code == 401
        assert response.data["detail"] == "Неверные учетные данные."

    def test_logout_login_required(self, assert_login_required):
        """Требуется авторизация."""
        assert_login_required("api:users:auth-session-logout", method="post", is_api=True)

    def test_success_logout(self, api_client, user_factory):
        """Активная сессия удаляется."""
        user = user_factory(password="StrongPassword123")
        api_client.force_login(user)

        response = api_client.post(reverse("api:users:auth-session-logout"))

        assert response.status_code == 200
        assert response.data["detail"] == "Сессия удалена."

    def test_logout_without_session(self, api_client, user_factory):
        """При отсутствии активной сессии возвращается ошибка."""
        user = user_factory()
        api_client.force_authenticate(user=user)

        response = api_client.post(reverse("api:users:auth-session-logout"))

        assert response.status_code == 400
        assert response.data["detail"] == "У вас нет активной сессии."


@pytest.mark.django_db
class TestDRFTokenLoginLogoutAPIView:
    """Тестирование drf_token_login и drf_token_logout."""

    def test_success_drf_token_login(self, api_client, user_factory):
        """При успешной аутентификации создается DRF токен."""
        password = "StrongPassword123"
        user = user_factory(password=password)

        response = api_client.post(
            reverse("api:users:auth-drf-token-login"),
            {
                "username": user.username,
                "password": password,
            },
            format="json",
        )

        assert response.status_code == 200

        token = Token.objects.get(user=user)

        assert response.data["drf_token"] == token.key
        assert response.data["user"]["username"] == user.username

    def test_existing_drf_token_is_reused(self, api_client, user_factory):
        """Если токен уже существует, новый не создается."""
        password = "StrongPassword123"
        user = user_factory(password=password)

        token = Token.objects.create(user=user)

        response = api_client.post(
            reverse("api:users:auth-drf-token-login"),
            {
                "username": user.username,
                "password": password,
            },
            format="json",
        )

        assert response.status_code == 200
        assert Token.objects.filter(user=user).count() == 1
        assert response.data["drf_token"] == token.key

    def test_invalid_credentials(self, api_client, user_factory):
        """Неверные учетные данные возвращают 401."""
        user = user_factory(password="StrongPassword123")

        response = api_client.post(
            reverse("api:users:auth-drf-token-login"),
            {
                "username": user.username,
                "password": "WrongPassword",
            },
            format="json",
        )

        assert response.status_code == 401
        assert response.data["detail"] == "Неверные учетные данные."

    def test_token_logout_login_required(self, assert_login_required):
        """Требуется авторизация для drf token logout."""
        assert_login_required("api:users:auth-drf-token-logout", method="post", is_api=True)

    def test_success_drf_token_logout(self, api_client, user_factory):
        """DRF токен успешно удаляется."""
        user = user_factory()

        token = Token.objects.create(user=user)

        api_client.force_authenticate(user=user, token=token)

        response = api_client.post(reverse("api:users:auth-drf-token-logout"))

        assert response.status_code == 200
        assert not Token.objects.filter(user=user).exists()

    def test_drf_token_logout_without_token(self, api_client, user_factory):
        """Если токен отсутствует, возвращается 400."""
        user = user_factory()

        api_client.force_authenticate(user=user)

        response = api_client.post(reverse("api:users:auth-drf-token-logout"))

        assert response.status_code == 400
        assert response.data["detail"] == "Нет активного DRF token."


@pytest.mark.django_db
class TestJWTTokenLogoutAPIView:
    """
    Тестирование jwt_token_logout.

    Не тестируются jwt_login, jwt_refresh и jwt_verify, поскольку используются стандартные
    классы Simple JWT, они переопределены только для написания схем Open API.
    """

    def test_jwt_logout_login_required(self, assert_login_required):
        """Требуется авторизация."""
        assert_login_required("api:users:auth-jwt-token-logout", method="post", is_api=True)

    def test_without_refresh(self, api_client, user_factory):
        """Refresh токен обязателен."""
        user = user_factory()

        api_client.force_authenticate(user=user)

        response = api_client.post(reverse("api:users:auth-jwt-token-logout"), {}, format="json")

        assert response.status_code == 400
        assert response.data["detail"] == "Не передан refresh токен."

    def test_success_jwt_logout_(self, api_client, user_factory):
        """Refresh токен успешно помещается в blacklist."""
        user = user_factory()

        api_client.force_authenticate(user=user)

        refresh = str(RefreshToken.for_user(user))

        response = api_client.post(
            reverse("api:users:auth-jwt-token-logout"),
            {"refresh": refresh},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["detail"] == "JWT refresh токен теперь заблокирован."

    def test_invalid_refresh(self, api_client, user_factory):
        """Невалидный refresh токен возвращает ошибку."""
        user = user_factory()

        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("api:users:auth-jwt-token-logout"),
            {"refresh": "invalid"},
            format="json",
        )

        assert response.status_code == 400
        assert response.data["detail"] == "Передан неверный или просроченный JWT refresh токен."

    def test_unexpected_exception(self, api_client, user_factory, mocker):
        """Непредвиденная ошибка обработки refresh токена возвращает 500."""
        user = user_factory()

        api_client.force_authenticate(user=user)

        mocker.patch(
            "users.api.views.RefreshToken.blacklist",
            side_effect=Exception(),
        )

        refresh = str(RefreshToken.for_user(user))

        response = api_client.post(
            reverse("api:users:auth-jwt-token-logout"),
            {"refresh": refresh},
            format="json",
        )

        assert response.status_code == 500
        assert response.data["detail"] == "Ошибка обработки JWT refresh токена."


@pytest.mark.django_db
class TestLogoutAllMethodsAPIView:
    """Тестирование logout_all (удаление сессии, DRF токена и JWT refresh)."""

    def test_logout_all_unauthenticated(self, assert_login_required):
        """Требуется авторизация."""
        assert_login_required("api:users:auth-logout-all-methods", method="post", is_api=True)

    def test_success_without_refresh(self, api_client, user_factory):
        """Удаляются DRF токен и сессия, refresh не передан — ошибки нет."""
        user = user_factory()
        Token.objects.create(user=user)
        api_client.force_login(user)

        url = reverse("api:users:auth-logout-all-methods")
        response = api_client.post(url, {}, format="json")

        assert response.status_code == 200
        assert not Token.objects.filter(user=user).exists()
        assert not api_client.session.session_key

    def test_success_with_valid_refresh(self, api_client, user_factory):
        """Удаляются DRF токен, сессия и refresh-токен попадает в blacklist."""
        user = user_factory()
        Token.objects.create(user=user)
        refresh = RefreshToken.for_user(user)

        api_client.force_login(user)

        url = reverse("api:users:auth-logout-all-methods")
        response = api_client.post(url, {"refresh": str(refresh)}, format="json")

        assert response.status_code == 200
        assert not Token.objects.filter(user=user).exists()
        assert not api_client.session.session_key
        with pytest.raises(TokenError):
            RefreshToken(refresh).check_blacklist()

    def test_invalid_refresh_returns_400(self, api_client, user_factory):
        """Невалидный refresh токен возвращает 400."""
        user = user_factory()
        api_client.force_login(user)

        url = reverse("api:users:auth-logout-all-methods")
        response = api_client.post(url, {"refresh": "invalid_token"}, format="json")

        assert response.status_code == 400
        assert "неверный" in response.data["detail"].lower()


@pytest.mark.django_db
class TestRegisterAPIView:
    """Тестирование регистрации пользователя."""

    def test_success_register(self, api_client, user_factory):
        """Успешная регистрация создает пользователя и возвращает его профиль."""
        data = {
            "username": "new_user",
            "email": "newuser@example.com",
            "password": "StrongPassword123",
            "password_confirm": "StrongPassword123",
        }

        response = api_client.post(reverse("api:users:auth-register"), data, format="json")

        assert response.status_code == 201
        assert response.data["username"] == data["username"]
        assert User.objects.filter(username=data["username"]).exists()

    def test_register_existing_username(self, api_client, user_factory):
        """Попытка регистрации с уже существующим username возвращает 400."""
        user_factory(username="duplicate_user")
        data = {
            "username": "duplicate_user",
            "email": "other@example.com",
            "password": "StrongPass123",
            "password_confirm": "StrongPass123",
        }

        response = api_client.post(reverse("api:users:auth-register"), data, format="json")

        assert response.status_code == 400
        assert "username" in response.data

    def test_register_password_mismatch(self, api_client):
        """Несовпадение паролей возвращает 400."""
        data = {
            "username": "new_user",
            "email": "test@example.com",
            "password": "StrongPassword123",
            "password_confirm": "WrongPassword123",
        }

        response = api_client.post(reverse("api:users:auth-register"), data, format="json")

        assert response.status_code == 400
        assert "password_confirm" in response.data

    def test_register_weak_password(self, api_client):
        """Слишком короткий или простой пароль возвращают 400."""
        data = {
            "username": "new_user",
            "email": "test@example.com",
            "password": "123",
            "password_confirm": "123",
        }

        response = api_client.post(reverse("api:users:auth-register"), data, format="json")

        assert response.status_code == 400
        assert "password" in response.data

    def test_register_missing_required_fields(self, api_client):
        """Отсутствие обязательных полей возвращает 400."""
        response = api_client.post(reverse("api:users:auth-register"), {}, format="json")

        assert response.status_code == 400
        for field in ["username", "password", "password_confirm"]:
            assert field in response.data


@pytest.mark.django_db
class TestPasswordChangeAPIView:
    """Тестирование смены пароля."""

    def test_password_change_unauthenticated(self, api_client, assert_login_required):
        """Для смены пароля требуется авторизация."""
        assert_login_required("api:users:auth-password-change", method="post", is_api=True)

    def test_password_change_success(self, api_client, user_factory):
        """Авторизованный пользователь (не через соцсеть) может изменить пароль."""
        old_password = "OldPass123"
        new_password = "NewStrongPass123"
        user = user_factory(password=old_password)
        api_client.force_authenticate(user=user)
        data = {
            "password_old": old_password,
            "password_new": new_password,
            "password_new_confirm": new_password,
        }

        response = api_client.post(reverse("api:users:auth-password-change"), data, format="json")

        assert response.status_code == 200
        assert response.data["detail"] == "Пароль успешно изменен."
        user.refresh_from_db()
        assert user.check_password(new_password)

    def test_password_change_wrong_old_password(self, api_client, user_factory):
        """Неверный текущий пароль возвращает 400."""
        user = user_factory(password="CorrectOld123")
        api_client.force_authenticate(user=user)

        data = {
            "password_old": "WrongOld456",
            "password_new": "NewPass123",
            "password_new_confirm": "NewPass123",
        }

        response = api_client.post(reverse("api:users:auth-password-change"), data, format="json")

        assert response.status_code == 400
        assert "password_old" in response.data

    def test_password_change_weak_new_password(self, api_client, user_factory):
        """Слабый новый пароль возвращает 400."""
        user = user_factory(password="OldPass123")
        api_client.force_authenticate(user=user)

        data = {
            "password_old": "OldPass123",
            "password_new": "123",
            "password_new_confirm": "123",
        }

        response = api_client.post(reverse("api:users:auth-password-change"), data, format="json")

        assert response.status_code == 400
        assert "password_new" in response.data

    def test_password_change_social_user_forbidden(self, api_client, user_factory):
        """
        Пользователь, зарегистрированный через соцсеть, не может сменить пароль,
        (UserPasswordNotSocialPermission).
        """
        user = user_factory(password="OldPass123", is_social=True)
        api_client.force_authenticate(user=user)

        data = {
            "password_old": "OldPass123",
            "password_new": "NewPass123",
            "password_new_confirm": "NewPass123",
        }

        response = api_client.post(reverse("api:users:auth-password-change"), data, format="json")

        assert response.status_code == 403
        assert "социальные сети" in response.data["detail"]


@pytest.mark.django_db
class TestPasswordResetAPIView:
    """Тестирование запроса на восстановление пароля."""

    def test_api_password_reset_full_flow(self, mocker, api_client, user_factory):
        """
        Интеграционный тест полного цикла через API:
        Запрос сброса -> Выполнение Celery задачи -> Письмо -> Парсинг -> Смена пароля -> Вход.
        """
        user = user_factory(
            username="api_reset_user", email="reset@example.com", password="OldPassword123"
        )

        # Мок transaction.on_commit для выполнения Celery задачи немедленно.
        mocker.patch("users.api.views.transaction.on_commit", side_effect=lambda func: func())

        # 1) Запрос сброса пароля
        response_request = api_client.post(
            reverse("api:users:auth-password-reset"),
            data={"email": "reset@example.com"},
            format="json",
        )
        assert response_request.status_code == 200
        assert "инструкция" in response_request.data["detail"].lower()

        # 2) Проверка, что Celery (при ALWAYS_EAGER) отправил письмо в outbox
        assert len(mail.outbox) == 1
        sent_email = mail.outbox[0]
        assert "reset@example.com" in sent_email.to

        email_body = sent_email.body
        link_match = re.search(
            r"password-reset/confirm/(?P<uidb64>[^/]+)/(?P<token>[^/]+)/", email_body
        )
        assert link_match is not None

        uidb64 = link_match.group("uidb64")
        token = link_match.group("token")

        # 3) Подтверждение и смена пароля через API
        response_confirm = api_client.post(
            reverse("api:users:auth-password-reset-confirm"),
            data={
                "uidb64": uidb64,
                "token": token,
                "password_new": "NewStrongPass123",
                "password_new_confirm": "NewStrongPass123",
            },
            format="json",
        )
        assert response_confirm.status_code == 200
        assert response_confirm.data["detail"] == "Пароль успешно изменен."

        # 4) Проверка, что пароль обновился в БД
        user.refresh_from_db()

        assert not user.check_password("OldPassword123")
        assert user.check_password("NewStrongPass123")

    def test_password_reset_nonexistent_email(self, mocker, api_client):
        """
        Если email не существует, все равно возвращается 200 (защита от перебора),
        письмо не отправляется.
        """
        data = {"email": "not_exist@example.com"}

        # Мок transaction.on_commit для выполнения Celery задачи немедленно.
        mocker.patch("users.api.views.transaction.on_commit", side_effect=lambda func: func())

        response = api_client.post(reverse("api:users:auth-password-reset"), data, format="json")

        assert response.status_code == 200
        assert "инструкция" in response.data["detail"].lower()

        # Celery задача отправки письма не отработала
        assert len(mail.outbox) == 0

    def test_password_reset_invalid_email_format(self, api_client):
        """Некорректный формат email возвращает 400."""
        data = {"email": "not-an-email"}

        response = api_client.post(reverse("api:users:auth-password-reset"), data, format="json")

        assert response.status_code == 400
        assert "email" in response.data


@pytest.mark.django_db
class TestUserViewSetRetrieve:

    def test_test_retrieve_nonexistent_user_returns_404(self, assert_not_found):
        """Для несуществующего пользователя возвращается 404."""
        assert_not_found(
            "api:users:users-detail",
            url_kwargs={"username": "non_existent_user"},
            method="get",
            is_api=True,
        )

    def test_retrieve_other_user_uses_public_serializer(self, api_client, user_factory):
        """При просмотре чужого профиля не показаны приватные поля."""
        client_user = user_factory(username="client_user")
        target_user = user_factory(username="target_user")

        api_client.force_authenticate(user=client_user)
        url = reverse("api:users:users-detail", kwargs={"username": target_user.username})
        response = api_client.get(url)

        assert response.status_code == 200
        # Приватного поля 'is_social' нет в ответе
        assert "is_social" not in response.data

    def test_retrieve_self_uses_my_profile_serializer(self, api_client, user_factory):
        """
        Если пользователь запрашивает свой профиль через /users/<username>/,
        используется сериализатор с приватными полями.
        """
        user = user_factory(username="my_user", is_social=True)

        api_client.force_authenticate(user=user)
        url = reverse("api:users:users-detail", kwargs={"username": user.username})
        response = api_client.get(url)

        assert response.status_code == 200
        # Приватное поле 'is_social' есть в ответе
        assert "is_social" in response.data
        assert response.data["is_social"] is True

    def test_list_users_default_sorting(self, api_client, user_factory):
        """По умолчанию пользователи сортируются по убыванию репутации."""
        user_factory(username="low", reputation=10)
        user_factory(username="high", reputation=50)

        url = reverse("api:users:users-list")
        response = api_client.get(url)

        assert response.status_code == 200
        results = response.data["results"]
        assert results[0]["username"] == "high"
        assert results[1]["username"] == "low"

    def test_list_users_filter_offline(self, api_client, user_factory, mocker):
        """Фильтрация online=offline возвращает только офлайн-пользователей."""
        user_online = user_factory(username="online_user")
        user_factory(username="offline_user")

        mocker.patch(
            "users.mixins.filter_mixins.get_cached_online_user_ids",
            return_value=[user_online.id],
        )

        url = reverse("api:users:users-list")
        response = api_client.get(url, {"online": "offline"})

        assert response.status_code == 200
        results = response.data["results"]
        assert len(results) == 1
        assert results[0]["username"] == "offline_user"

    def test_retrieve_user_uses_cache_and_avoids_db(self, clear_cache, api_client, user_factory):
        """
        Проверка сохранения профиля пользователя в кеш.
        """
        user = user_factory(username="cached_user")
        cache_key = get_user_cache_key(user.username)
        url = reverse("api:users:users-detail", kwargs={"username": user.username})

        # Первый запрос - сохранение в кеше, запрос в БД
        with CaptureQueriesContext(connection) as queries_1:
            response_1 = api_client.get(url)

        assert response_1.status_code == 200
        assert cache.get(cache_key) is not None

        # Второй запрос - данные из кеша
        with CaptureQueriesContext(connection) as queries_2:
            response_2 = api_client.get(url)

        assert response_2.status_code == 200

        assert any("users_user" in q["sql"].lower() for q in queries_1)
        assert not any("users_user" in q["sql"].lower() for q in queries_2)


@pytest.mark.django_db
class TestUserViewSetMe:
    """Тестирование личного профиля пользователя."""

    def test_me_get_unauthenticated(self, api_client, assert_login_required):
        """Для просмотра собственного профиля требуется авторизация."""
        assert_login_required("api:users:users-me", method="get", is_api=True)

    def test_me_patch_unauthenticated(self, api_client, assert_login_required):
        """Для изменения собственного профиля требуется авторизация."""
        assert_login_required("api:users:users-me", method="patch", is_api=True)

    def test_me_get_success(self, api_client, user_factory):
        """Успешное получение своего профиля."""
        user = user_factory()
        api_client.force_authenticate(user=user)

        url = reverse("api:users:users-me")
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["username"] == user.username
        assert "is_social" in response.data

    def test_me_delete_success(self, api_client, user_factory):
        """При DELETE запросе аккаунт удаляется, возвращается 204."""
        user = user_factory()
        api_client.force_authenticate(user=user)

        url = reverse("api:users:users-me")
        response = api_client.delete(url)

        assert response.status_code == 204
        assert not User.objects.filter(pk=user.pk).exists()

    def test_me_patch_success(self, api_client, user_factory):
        """Частичное обновление профиля: успешное изменение username."""
        user = user_factory(username="old_name", email="old@example.com")
        api_client.force_authenticate(user=user)

        url = reverse("api:users:users-me")
        response = api_client.patch(url, {"username": "new_name"}, format="json")

        assert response.status_code == 200
        assert response.data["username"] == "new_name"
        user.refresh_from_db()
        assert user.username == "new_name"


@pytest.mark.django_db
class TestUserViewSetAvatarFull:
    """Тестирование получения оригинала аватара."""

    def test_avatar_full_not_found(self, assert_not_found):
        """Если указан несуществующий пользователь, возвращается 404."""
        assert_not_found(
            "api:users:users-avatar-full",
            url_kwargs={"username": "non_existent_user"},
            method="get",
            is_api=True,
        )

    def test_avatar_full_success(self, api_client, user_factory):
        """Если аватар есть, возвращается URL."""
        user = user_factory(avatar="avatars/test_avatar.jpg")

        url = reverse("api:users:users-avatar-full", kwargs={"username": user.username})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["username"] == user.username
        assert "http" in response.data["full_avatar_url"]
        assert "avatars/test_avatar.jpg" in response.data["full_avatar_url"]


@pytest.mark.django_db
class TestUserViewSetModeration:
    """Тестирование блокировки/разблокировки пользователей."""

    def test_block_nonexistent_user_returns_404(self, api_client, user_factory, assert_not_found):
        """Если указан несуществующий пользователь, возвращается 404."""
        moderator = user_factory(role=User.Role.MODERATOR)
        api_client.force_authenticate(user=moderator)

        assert_not_found(
            "api:users:users-block",
            url_kwargs={"username": "non_existent_user"},
            method="post",
            is_api=True,
        )

    def test_unblock_nonexistent_user_returns_404(self, api_client, user_factory, assert_not_found):
        """Если указан несуществующий пользователь, возвращается 404."""
        moderator = user_factory(role=User.Role.MODERATOR)
        api_client.force_authenticate(user=moderator)

        assert_not_found(
            "api:users:users-unblock",
            url_kwargs={"username": "non_existent_user"},
            method="post",
            is_api=True,
        )

    def test_block_user_success(self, api_client, user_factory, mocker):
        """Успешная блокировка пользователя."""
        moderator = user_factory(role=User.Role.MODERATOR)
        target = user_factory(is_blocked=False)

        api_client.force_authenticate(user=moderator)

        mock_block_service = mocker.patch(
            "users.api.views.block_user_service",
            return_value=(True, "Пользователь успешно заблокирован."),
        )
        mocker.patch(
            "users.api.permissions.CanBlockUserPermission.has_permission", return_value=True
        )
        mocker.patch(
            "users.api.permissions.CanBlockUserPermission.has_object_permission", return_value=True
        )

        url = reverse("api:users:users-block", kwargs={"username": target.username})
        response = api_client.post(url)

        assert response.status_code == 200
        assert response.data["message"] == "Пользователь успешно заблокирован."
        mock_block_service.assert_called_once()

        args, kwargs = mock_block_service.call_args
        assert kwargs["moderator"] == moderator
        assert kwargs["target_user"] == target

    def test_block_user_already_blocked(self, api_client, user_factory, mocker):
        """Если пользователь уже заблокирован, возвращается 400."""
        moderator = user_factory(role=User.Role.MODERATOR)
        target = user_factory(is_blocked=True)

        api_client.force_authenticate(user=moderator)

        mocker.patch(
            "users.api.views.block_user_service",
            return_value=(False, "Пользователь уже заблокирован."),
        )
        mocker.patch(
            "users.api.permissions.CanBlockUserPermission.has_permission", return_value=True
        )
        mocker.patch(
            "users.api.permissions.CanBlockUserPermission.has_object_permission", return_value=True
        )

        url = reverse("api:users:users-block", kwargs={"username": target.username})
        response = api_client.post(url)

        assert response.status_code == 400
        assert response.data["message"] == "Пользователь уже заблокирован."

    def test_unblock_user_success(self, api_client, user_factory, mocker):
        """Успешная разблокировка пользователя."""
        moderator = user_factory(role=User.Role.MODERATOR)
        target = user_factory(is_blocked=True)

        api_client.force_authenticate(user=moderator)

        mock_unblock_service = mocker.patch(
            "users.api.views.unblock_user_service",
            return_value=(True, "Пользователь успешно разблокирован."),
        )
        mocker.patch(
            "users.api.permissions.CanBlockUserPermission.has_permission", return_value=True
        )
        mocker.patch(
            "users.api.permissions.CanBlockUserPermission.has_object_permission", return_value=True
        )

        url = reverse("api:users:users-unblock", kwargs={"username": target.username})
        response = api_client.post(url)

        assert response.status_code == 200
        assert response.data["message"] == "Пользователь успешно разблокирован."
        mock_unblock_service.assert_called_once()

        args, kwargs = mock_unblock_service.call_args
        assert kwargs["moderator"] == moderator
        assert kwargs["target_user"] == target
