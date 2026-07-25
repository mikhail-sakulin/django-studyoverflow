from types import SimpleNamespace
from typing import Any

from users.services.social_providers import handle_github, handle_google, handle_vk, handle_yandex


class TestHandleGithub:
    def test_full_name_split_bio_and_avatar(self):
        """Проверяет разделение имени, запись bio и возврат avatar_url."""
        user: Any = SimpleNamespace()
        data = {
            "name": "Ivan Ivanov",
            "bio": "Test bio.",
            "avatar_url": "github_avatar_url",
        }

        avatar_url = handle_github(user, data)

        assert user.first_name == "Ivan"
        assert user.last_name == "Ivanov"
        assert user.bio == "Test bio."
        assert avatar_url == "github_avatar_url"

    def test_single_word_name_and_missing_bio_and_avatar(self):
        """Имя без фамилии может задаваться, bio/avatar не задаются, если их нет в ответе."""
        user: Any = SimpleNamespace(last_name="Existing", bio="Existing bio")
        data = {"name": "Ivan"}

        avatar_url = handle_github(user, data)

        assert user.first_name == "Ivan"
        assert user.last_name == "Existing"
        assert user.bio == "Existing bio"
        assert avatar_url is None


class TestHandleGoogle:
    def test_avatar_size_replacement(self):
        """Проверяет подмену строки размера аватара с s96-c на s1024-c."""
        user: Any = SimpleNamespace()
        data = {
            "given_name": "Ivan",
            "family_name": "Ivanov",
            "picture": "abc=s96-c",
        }

        avatar_url = handle_google(user, data)

        assert user.first_name == "Ivan"
        assert user.last_name == "Ivanov"
        assert avatar_url == "abc=s1024-c"

    def test_no_picture_returns_none(self):
        user: Any = SimpleNamespace()

        assert handle_google(user, {}) is None


class TestHandleYandex:
    def test_avatar_url_formatting(self):
        """Проверяет правильность сборки URL-адреса аватара по его ID."""
        user: Any = SimpleNamespace()
        data = {
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "default_avatar_id": "54321",
        }

        avatar_url = handle_yandex(user, data)

        assert user.first_name == "Ivan"
        assert user.last_name == "Ivanov"
        assert avatar_url == "https://avatars.mds.yandex.net/get-yapic/54321/islands-200"

    def test_no_avatar_id_returns_none(self):
        user: Any = SimpleNamespace()

        assert handle_yandex(user, {"first_name": "Ivan"}) is None


class TestHandleVk:
    def test_avatar_query_cs_overridden_other_params_preserved(self):
        """Проверяет, что cs перезаписывается, а остальные query-параметры сохраняются."""
        user: Any = SimpleNamespace()
        data = {
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "avatar": "photo.jpg?size=200x200&cs=100x100",
        }

        avatar_url = handle_vk(user, data)

        assert avatar_url is not None
        assert user.first_name == "Ivan"
        assert user.last_name == "Ivanov"
        assert "cs=1080x1080" in avatar_url
        assert "cs=100x100" not in avatar_url
        assert "size=200x200" in avatar_url

    def test_no_avatar_returns_none(self):
        user: Any = SimpleNamespace()

        assert handle_vk(user, {"first_name": "Ivan"}) is None
