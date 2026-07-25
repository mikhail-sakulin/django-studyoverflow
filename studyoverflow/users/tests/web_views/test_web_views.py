import re

import pytest
from allauth.account.signals import user_signed_up
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse


User = get_user_model()


@pytest.fixture(autouse=True)
def clear_cache():
    """Изолирует тесты друг от друга, очищая кеш до и после запуска теста."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def mock_redis_conn(mocker):
    """
    Автоматически мокает подключение к Redis во всех тестах.

    Часто нужен в тестах, поскольку в OnlineStatusMiddleware, если пользователь аутентифицирован,
    есть обращение к сервисной функции set_user_online, в которой есть прямое обращение к Redis.
    """
    mock_conn = mocker.patch("users.services.online.get_redis_connection")
    return mock_conn


@pytest.mark.django_db
class TestUsersListView:
    def test_users_list_view_status_and_context(self, client, user_factory):
        """Проверяет доступность страницы и сортировку по репутации."""
        user_factory(username="alex", reputation=10)
        user_factory(username="boris", reputation=20)

        url = reverse("users:list")
        response = client.get(url)

        assert response.status_code == 200
        assert "users" in response.context
        assert response.context["section_of_menu_selected"] == "users:list"

        users = response.context["users"]
        assert users[0].username == "boris"
        assert users[1].username == "alex"

    def test_users_list_view_caching(self, client, user_factory):
        """Проверяет, что при попадании в кеш повторный запрос не делает лишних SQL-запросов."""
        user_factory()
        url = reverse("users:list")

        # Первый запрос к "users:list" — замер количества SQL-запросов
        with CaptureQueriesContext(connection) as first_call:
            client.get(url)

        assert cache.get("users_first_page") is not None

        # Второй запрос к "users:list" — также замер количества SQL-запросов,
        # запросов к БД должно быть меньше из-за кеша
        with CaptureQueriesContext(connection) as second_call:
            client.get(url)

        assert len(second_call) < len(first_call)


@pytest.mark.django_db
class TestUsersListHTMXView:
    def test_htmx_view_integration_mixins(self, user_factory, client, mocker):
        """
        Проверяет работу view вместе с миксинами:
        сортировку, фильтрацию по статусу 'онлайн' и offset-limit пагинацию.
        """
        url = reverse("users:list_htmx")

        # Пользователи с разной репутацией для проверки сортировки
        user_low = user_factory(username="user_low", reputation=10)
        user_factory(username="user_mid", reputation=20)
        user_high = user_factory(username="user_high", reputation=30)

        mocker.patch(
            "users.mixins.filter_mixins.get_cached_online_user_ids",
            return_value=[user_low.id, user_high.id],
        )

        response = client.get(
            url,
            data={
                "online": "online",
                "user_sort": "reputation",
                "user_order": "desc",
                "limit": 1,
                "offset": 0,
            },
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200

        # В users должен попасть только один пользователь после limit == 1
        users_in_context = list(response.context["users"])
        assert len(users_in_context) == 1
        assert users_in_context[0] == user_high

        # Проверка остального context после работы view и миксинов
        assert response.context["online_ids"] == [user_low.id, user_high.id]
        assert response.context["remaining"] is True
        assert response.context["offset"] == 0
        assert response.context["limit"] == 1

    def test_htmx_view_pagination_invalid_params(self, client, user_factory, caplog):
        """Проверяет обработку некорректных параметров пагинации."""
        user_factory(username="test_user")
        url = reverse("users:list_htmx")

        response = client.get(
            url,
            data={"limit": "invalid", "offset": "string"},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        # При ValueError (некорректные "limit" и "offset") возвращается queryset.none()
        assert len(response.context["users"]) == 0

        assert "Некорректные параметры пагинации." in caplog.text

    def test_htmx_view_sorting_fallback_to_defaults(self, client, user_factory):
        """Проверяет, что при невалидных параметрах сортировки применяются дефолтные."""
        user_factory(username="alex", reputation=10)
        user_factory(username="boris", reputation=50)

        url = reverse("users:list_htmx")
        response = client.get(
            url,
            data={
                "user_sort": "non_existent_field",
                "user_order": "random_string",
            },
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        users = response.context["users"]

        # Сортировка по умолчанию: reputation desc
        assert users[0].username == "boris"
        assert users[1].username == "alex"

    def test_htmx_view_filter_offline_users(self, client, user_factory, mocker):
        """Проверяет фильтрацию офлайн пользователей."""
        user_online = user_factory(username="online_user")
        user_offline = user_factory(username="offline_user")

        mocker.patch(
            "users.mixins.filter_mixins.get_cached_online_user_ids",
            return_value=[user_online.id],
        )

        url = reverse("users:list_htmx")
        response = client.get(
            url,
            data={"online": "offline"},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        users = list(response.context["users"])

        assert len(users) == 1
        assert users[0] == user_offline


@pytest.mark.django_db
class TestUserRegisterView:
    def test_register_view_passes_next_to_context(self, client):
        """
        Проверка, что get-параметр next передается в контекст шаблона
        для редиректа обратно после регистрации.
        """
        url = reverse("users:register") + "?next=/posts/"
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["next"] == "/posts/"

    def test_registration_submits_successfully_and_sends_signal(self, client, mocker):
        """
        Успешная валидация формы регистрирует пользователя и отправляется сигнал allauth
        о регистрации нового пользователя.

        Редирект на home, если не задан параметр next.
        """
        mock_signal = mocker.patch.object(user_signed_up, "send")
        url = reverse("users:register")

        form_data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password1": "Password123!!",
            "password2": "Password123!!",
        }

        response = client.post(url, data=form_data)

        assert response.status_code == 302
        # response.url есть только при редиректе
        assert response.url == reverse("home")
        mock_signal.assert_called_once()

    def test_registration_redirects_to_next_url(self, client):
        """Если задан параметр next, то после успешной регистрации редирект на next."""
        url = reverse("users:register") + "?next=/posts/"
        form_data = {
            "username": "next_user",
            "email": "next_user@example.com",
            "password1": "Password123!!",
            "password2": "Password123!!",
        }

        response = client.post(url, data=form_data)

        assert response.status_code == 302
        assert response.url == "/posts/"


@pytest.mark.django_db
class TestUserLoginView:
    def test_login_redirects_to_next_url(self, client, user_factory):
        """При успешном входе редирект на next."""
        user_factory(username="user", password="StrongPassword123")
        url = reverse("users:login") + "?next=/"
        form_data = {"username": "user", "password": "StrongPassword123"}

        response = client.post(url, data=form_data)

        assert response.status_code == 302
        assert response.url == "/"

    def test_login_adds_welcome_message(self, client, user_factory):
        """При успешном входе создается message с приветствием, также редирект на next."""
        user_factory(username="user", password="StrongPassword123")
        url = reverse("users:login") + "?next=/"
        form_data = {"username": "user", "password": "StrongPassword123"}

        # follow=True - клиент автоматически пройдет по всей цепочке HTTP-редиректов
        response = client.post(url, data=form_data, follow=True)

        assert response.status_code == 200
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert str(messages[0]) == "Добро пожаловать, user!"


@pytest.mark.django_db
class TestUserLogoutView:
    def test_authenticated_user_can_logout_via_post(self, client, user_factory):
        """Аутентифицированный пользователь может выйти из аккаунта по POST-запросу."""
        user = user_factory()
        # Аутентификация созданного пользователя
        client.force_login(user)

        url = reverse("users:logout")
        # follow=True - клиент автоматически пройдет по всей цепочке HTTP-редиректов
        response = client.post(url, follow=True)

        assert response.status_code == 200
        # После logout нет сессии
        assert "_auth_user_id" not in client.session

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert str(messages[0]) == "Вы вышли из аккаунта."

    def test_unauthenticated_user_cannot_logout(self, assert_login_required):
        assert_login_required(url_name="users:logout", method="post")


@pytest.mark.django_db
class TestAuthorProfileView:

    def test_nonexistent_user_profile_returns_404(self, assert_not_found):
        """Для несуществующего пользователя возвращается 404."""
        assert_not_found(
            "users:profile",
            url_kwargs={"username": "non_existent_user"},
            method="get",
            is_api=False,
        )

    def test_redirect_to_my_profile_if_self_open(self, client, user_factory):
        """
        Если пользователь открывает свой же публичный профиль,
        его редиректит в личный кабинет (/me/).
        """
        user = user_factory(username="user_me")
        client.force_login(user)

        url = reverse("users:profile", kwargs={"username": "user_me"})
        response = client.get(url)

        assert response.status_code == 302
        assert response.url == reverse("users:my_profile")

    def test_view_other_author_profile_and_caching(self, client, user_factory, mock_redis_conn):
        """Просмотр чужого профиля доступен, и данные пользователя кешируются."""
        mock_redis_conn.return_value.exists.return_value = 0

        me = user_factory(username="user_me")
        other = user_factory(username="other_author")
        client.force_login(me)

        url = reverse("users:profile", kwargs={"username": "other_author"})
        response = client.get(url)

        # Проверка статуса онлайн в профиле (моком выше задано, что other_author не в сети)
        assert "был в сети" in response.content.decode("utf-8")

        assert response.status_code == 200
        assert response.context["author"] == other

        cached_user = cache.get("user_profile_other_author")
        assert cached_user is not None
        assert cached_user.username == "other_author"


@pytest.mark.django_db
class TestUserProfileUpdateView:

    def test_unauthenticated_user_cannot_get_update_profile_page(self, assert_login_required):
        assert_login_required(url_name="users:my_profile", method="get")

    def test_authenticated_user_can_load_and_submit_update_profile(
        self, client, user_factory, mock_redis_conn
    ):
        """
        Авторизованный пользователь может просматривать профиль с онлайн-статусом
        и обновлять свои данные.
        """
        mock_redis_conn.return_value.exists.return_value = 1

        user = user_factory(username="user_test", email="old@example.com")
        client.force_login(user)

        url = reverse("users:my_profile")

        assert client.get(url).status_code == 200

        response_get = client.get(url)
        assert response_get.status_code == 200
        # Проверка статуса онлайн в профиле (моком выше задано, что статус онлайн положительный)
        assert "Сейчас в сети" in response_get.content.decode("utf-8")

        form_data = {
            "username": "user_test",
            "email": "new_email@example.com",
            "first_name": "NewName",
        }
        response = client.post(url, data=form_data, follow=True)

        assert response.status_code == 200

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert str(messages[0]) == "Профиль успешно изменен!"


@pytest.mark.django_db
class TestAvatarPreview:

    def test_avatar_preview_nonexistent_user_returns_404(self, assert_not_found):
        """Если указан несуществующий пользователь, возвращается 404."""
        assert_not_found(
            "users:avatar_preview",
            url_kwargs={"username": "ghost"},
            method="get",
            is_api=False,
        )

    def test_avatar_preview_returns_html_fragment(self, client, user_factory):
        """Проверяет запрос на превью аватара."""
        user = user_factory(username="avatar_user")

        response = client.get(reverse("users:avatar_preview", kwargs={"username": "avatar_user"}))

        assert response.status_code == 200
        assert response.context["author"] == user


@pytest.mark.django_db
class TestUserDeleteView:

    def test_unauthenticated_user_cannot_delete_profile(self, assert_login_required):
        assert_login_required(url_name="users:delete", method="post")

    def test_delete_user_performs_logout_and_redirects(self, client, user_factory):
        """
        Удаление аккаунта удаляет пользователя из БД, завершает его сессию и
        редиректит на главную страницу.
        """
        user = user_factory(username="user_to_delete")
        client.force_login(user)

        response = client.post(reverse("users:delete"))

        assert response.status_code == 302
        assert response.url == reverse("home")

        assert "_auth_user_id" not in client.session
        assert not User.objects.filter(username="user_to_delete").exists()


@pytest.mark.django_db
class TestUserPasswordChangeView:

    def test_unauthenticated_user_cannot_get_update_profile_page(self, assert_login_required):
        assert_login_required(url_name="users:password_change", method="get")

    def test_password_change_logging_and_success_message(self, client, user_factory, mocker):
        """Смена пароля создает кастомный лог и выводит сообщение."""
        mock_logger = mocker.patch("users.views.user_views.logger.info")

        user = user_factory(username="password_changer", password="StrongPassword123")
        client.force_login(user)

        response = client.post(
            reverse("users:password_change"),
            data={
                "old_password": "StrongPassword123",
                "new_password1": "NewStrongPassword123!",
                "new_password2": "NewStrongPassword123!",
            },
        )

        assert response.status_code == 302

        mock_logger.assert_called_once()
        assert "успешно сменил пароль" in mock_logger.call_args[0][0]
        assert mock_logger.call_args[1]["extra"]["event_type"] == "user_password_change_success"

    def test_password_change_forbidden_for_social_user(self, client, user_factory):
        """Пользователям с регистрацией через соцсеть смена пароля запрещена."""
        user = user_factory(username="social_user", password="StrongPassword123", is_social=True)
        client.force_login(user)

        response = client.post(
            reverse("users:password_change"),
            data={
                "old_password": "StrongPassword123",
                "new_password1": "NewStrongPassword123!",
                "new_password2": "NewStrongPassword123!",
            },
        )

        assert response.status_code == 403


@pytest.mark.django_db
class TestPasswordResetViews:

    def test_password_reset_flow_pages(self, client):
        """Проверка, что страницы восстановления пароля доступны."""
        assert client.get(reverse("users:password_reset")).status_code == 200
        assert client.get(reverse("users:password_reset_done")).status_code == 200
        assert client.get(reverse("users:password_reset_complete")).status_code == 200

    def test_password_reset_full_flow(self, client, user_factory):
        """
        Интеграционный тест полного цикла сброса пароля:
        Запрос сброса -> Получение письма -> Переход по ссылке ->
        -> Смена пароля -> Вход с новым паролем.
        """
        user = user_factory(
            username="reset_user", email="reset@example.com", password="OldPassword123"
        )

        # 1) Запрос сброса пароля
        response_post_email = client.post(
            reverse("users:password_reset"), data={"email": "reset@example.com"}
        )
        # После успешной отправки формы редирект на страницу 'done'
        assert response_post_email.status_code == 302
        assert response_post_email.url == reverse("users:password_reset_done")

        # 2) Проверка отправки письма и самого письма, получение ссылки на восстановление пароля
        assert len(mail.outbox) == 1
        sent_email = mail.outbox[0]

        assert "Сброс пароля" in sent_email.subject
        assert "reset@example.com" in sent_email.to

        email_body = sent_email.body
        link_match = re.search(
            r"password-reset/confirm/(?P<uidb64>[^/]+)/(?P<token>[^/]+)/", email_body
        )

        assert link_match is not None

        uidb64 = link_match.group("uidb64")
        token = link_match.group("token")

        # 3) Переход по ссылки из письма
        confirm_url = reverse(
            "users:password_reset_confirm", kwargs={"uidb64": uidb64, "token": token}
        )
        response_set_password = client.get(confirm_url, follow=True)
        assert response_set_password.status_code == 200

        # 4) Восстановление пароля
        response_complete = client.post(
            # Django редиректит с confirm_url с token на url без token
            f"/users/password-reset/confirm/{uidb64}/set-password/",
            data={"new_password1": "NewPassword123", "new_password2": "NewPassword123"},
        )
        # После успешного изменения пароля редирект на 'complete'
        assert response_complete.status_code == 302
        assert response_complete.url == reverse("users:password_reset_complete")

        # 5) Проверка, что пароль изменился
        user.refresh_from_db()

        assert not user.check_password("OldPassword123")
        assert user.check_password("NewPassword123")


@pytest.mark.django_db
class TestModeratorActions:

    def test_block_nonexistent_user_returns_404(self, client, user_factory, assert_not_found):
        """Для несуществующего пользователя возвращается 404."""
        moderator = user_factory(username="moder", role=User.Role.MODERATOR)
        client.force_login(moderator)

        assert_not_found(
            "users:block_user",
            url_kwargs={"user_id": 9999},
            method="post",
            is_api=False,
        )

    def test_unblock_nonexistent_user_returns_404(self, client, user_factory, assert_not_found):
        """Для несуществующего пользователя возвращается 404."""
        moderator = user_factory(username="moder", role=User.Role.MODERATOR)
        client.force_login(moderator)

        assert_not_found(
            "users:unblock_user",
            url_kwargs={"user_id": 9999},
            method="post",
            is_api=False,
        )

    def test_unauthenticated_user_cannot_moderate(self, user_factory, assert_login_required):
        user_for_block = user_factory(username="user_for_block")
        assert_login_required(
            url_name="users:block_user", url_kwargs={"user_id": user_for_block.pk}, method="post"
        )
        assert_login_required(
            url_name="users:unblock_user", url_kwargs={"user_id": user_for_block.pk}, method="post"
        )

    def test_block_user_requires_permission(self, client, user_factory):
        """Без права users.block_user запрос завершается с кодом 403."""
        moderator = user_factory(username="fake_moder", role=User.Role.USER)
        user_for_block = user_factory(username="user_for_block")
        client.force_login(moderator)

        response = client.get(reverse("users:block_user", kwargs={"user_id": user_for_block.pk}))

        assert response.status_code == 403

        response = client.get(reverse("users:unblock_user", kwargs={"user_id": user_for_block.pk}))

        assert response.status_code == 403

    def test_block_user_success(self, client, user_factory, mocker):
        """
        При наличии права users.block_user вызывается сервис блокировки и возвращается сообщение.
        """
        mock_service = mocker.patch(
            "users.views.user_views.block_user_service",
            return_value=(True, "Пользователь заблокирован."),
        )

        moderator = user_factory(username="real_moder", role=User.Role.MODERATOR)
        client.force_login(moderator)

        user_for_block = user_factory(username="user_for_block")

        response = client.post(
            reverse("users:block_user", kwargs={"user_id": user_for_block.pk}), follow=True
        )

        assert response.status_code == 200
        mock_service.assert_called_once_with(
            moderator=moderator, target_user=user_for_block, source="web"
        )

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert str(messages[0]) == "Пользователь заблокирован."

    def test_unblock_user_success(self, client, user_factory, mocker):
        """
        При наличии права users.block_user вызывается сервис блокировки и возвращается сообщение.
        """
        mock_service = mocker.patch(
            "users.views.user_views.unblock_user_service",
            return_value=(True, "Пользователь разблокирован."),
        )

        moderator = user_factory(username="real_moder", role=User.Role.MODERATOR)
        client.force_login(moderator)

        user_for_unblock = user_factory(username="user_for_unblock")

        response = client.post(
            reverse("users:unblock_user", kwargs={"user_id": user_for_unblock.pk}), follow=True
        )

        assert response.status_code == 200
        mock_service.assert_called_once_with(
            moderator=moderator, target_user=user_for_unblock, source="web"
        )

        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert str(messages[0]) == "Пользователь разблокирован."
