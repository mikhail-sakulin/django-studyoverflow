import os

import pytest
from helpers.data_generators import generate_user_register_data
from helpers.pages import AuthPage, CommentPage, PersonalProfilePage, PostsPage, PublicProfilePage


# стандартный хук pytest, настройка конфига перед тестами
def pytest_configure(config):
    config.option.base_url = os.environ["BASE_URL"]


@pytest.fixture
def create_registered_user(auth_page):
    """
    Фабрика, возвращает функцию для регистрации нового пользователя.
    """

    def _register(
        current_auth_page=None, first_name: str | None = None, last_name: str | None = None
    ):
        """
        Создаёт уникального пользователя через UI и возвращает его данные, не логинит пользователя.

        Использует либо фикстуру auth_page со стандартной page, либо принимает
        current_auth_page с другой изолированной page и использует ее, например, чтобы
        создавать нескольких пользователей в параллельных сессиях.
        """
        active_auth_page = current_auth_page or auth_page

        user_data = generate_user_register_data()

        if first_name is not None:
            user_data["first_name"] = first_name
        if last_name is not None:
            user_data["last_name"] = last_name

        active_auth_page.navigate_to_register()
        active_auth_page.register(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
            first_name=user_data.get("first_name", ""),
            last_name=user_data.get("last_name", ""),
        )
        return user_data

    return _register


@pytest.fixture
def register_and_login_user(auth_page, create_registered_user):
    """
    Фабрика для аутентификации пользователя.
    """

    def _login(current_auth_page=None, **kwargs):
        """
        Создает пользователя и авторизует созданного пользователя.

        Возвращает словарь с данными залогиненного пользователя.

        Использует либо фикстуру auth_page со стандартной page, либо принимает
        current_auth_page с другой изолированной page и использует ее, например, чтобы
        создавать нескольких пользователей в параллельных сессиях.
        """
        active_auth_page = current_auth_page or auth_page

        user_data = create_registered_user(current_auth_page=current_auth_page, **kwargs)

        active_auth_page.login(
            login_identifier=user_data["username"],
            password=user_data["password"],
        )
        return user_data

    return _login


@pytest.fixture
def auth_page(page):
    return AuthPage(page)


@pytest.fixture
def personal_profile_page(page):
    return PersonalProfilePage(page)


@pytest.fixture
def public_profile_page(page):
    return PublicProfilePage(page)


@pytest.fixture
def posts_page(page):
    return PostsPage(page)


@pytest.fixture
def comment_page(page):
    return CommentPage(page)
