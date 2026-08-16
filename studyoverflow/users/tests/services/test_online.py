import pytest

from users.services import (
    get_cached_online_user_ids,
    get_online_user_ids,
    is_user_online,
    remove_user_offline,
    set_user_online,
)
from users.services.online import (
    ONLINE_SET_KEY,
    ONLINE_TTL,
    REDIS_KEY_PREFIX,
    get_user_key_for_redis,
)


@pytest.fixture
def mock_redis_conn(mocker):
    """Мок Redis-соединения с настроенным контекстным менеджером pipeline()."""
    mock_conn = mocker.MagicMock()
    mock_pipe = mocker.MagicMock()
    mock_conn.pipeline.return_value.__enter__.return_value = mock_pipe

    mocker.patch("users.services.online.get_redis_connection", return_value=mock_conn)

    return mock_conn, mock_pipe


def test_get_user_key_for_redis():
    """Проверяет правильность формирования Redis-ключа."""
    user_id = 5
    key = get_user_key_for_redis(user_id)
    assert key == f"{REDIS_KEY_PREFIX}:{user_id}"


def test_set_user_online(mock_redis_conn):
    """Проверяет отправку данных в Redis при установке онлайн-статуса."""
    _, mock_pipe = mock_redis_conn

    user_id = 5
    set_user_online(user_id)

    mock_pipe.set.assert_called_once_with(f"{REDIS_KEY_PREFIX}:{user_id}", "1", ex=ONLINE_TTL)
    mock_pipe.sadd.assert_called_once_with(ONLINE_SET_KEY, user_id)
    mock_pipe.execute.assert_called_once()


@pytest.mark.parametrize(
    ("exists_return", "expected"),
    [
        (1, True),
        (0, False),
    ],
)
def test_is_user_online(mock_redis_conn, exists_return, expected):
    """Проверяет онлайн- и офлайн-статус пользователя."""
    mock_conn, _ = mock_redis_conn
    mock_conn.exists.return_value = exists_return

    user_id = 5
    assert is_user_online(user_id) is expected
    mock_conn.exists.assert_called_once_with(f"{REDIS_KEY_PREFIX}:{user_id}")


def test_remove_user_offline(mock_redis_conn):
    """Проверяет удаление ключа из Redis при уходе пользователя в офлайн."""
    _, mock_pipe = mock_redis_conn

    user_id = 5
    remove_user_offline(user_id)

    mock_pipe.delete.assert_called_once_with(f"{REDIS_KEY_PREFIX}:{user_id}")
    mock_pipe.srem.assert_called_once_with(ONLINE_SET_KEY, user_id)
    mock_pipe.execute.assert_called_once()


class TestGetOnlineUserIds:
    def test_get_online_user_ids_no_users(self, mock_redis_conn):
        """Если множество онлайн-пользователей пусто - выход из тестируемой функции."""
        mock_conn, _ = mock_redis_conn
        mock_conn.smembers.return_value = []

        assert get_online_user_ids() == []
        mock_conn.pipeline.assert_not_called()

    def test_get_online_user_ids_filters_expired(self, mock_redis_conn):
        """Проверяет фильтрацию и удаление просроченных сессий пользователей."""
        mock_conn, mock_pipe = mock_redis_conn
        mock_conn.smembers.return_value = [b"10", b"20"]
        mock_pipe.execute.return_value = [True, False]

        active_ids = get_online_user_ids()

        assert active_ids == [10]
        mock_conn.srem.assert_called_once_with("online_users_set", 20)

    def test_get_online_user_ids_no_expired(self, mock_redis_conn):
        """Если просроченных записей нет — srem не вызывается"""
        mock_conn, mock_pipe = mock_redis_conn
        mock_conn.smembers.return_value = [b"10", b"20"]
        mock_pipe.execute.return_value = [True, True]

        active_ids = get_online_user_ids()

        assert active_ids == [10, 20]
        mock_conn.srem.assert_not_called()


class TestGetCachedOnlineUserIds:
    def test_get_cached_online_user_ids_cache_miss(self, mocker):
        """Проверяет поведение при отсутствии множества пользователей онлайн в кеше."""
        mock_get_online = mocker.patch(
            "users.services.online.get_online_user_ids", return_value=[10, 15]
        )
        mock_cache = mocker.patch("users.services.online.cache")
        mock_cache.get.return_value = None

        result = get_cached_online_user_ids()

        assert result == [10, 15]
        mock_get_online.assert_called_once()
        mock_cache.get.assert_called_once_with("cached_online_users_set")
        mock_cache.set.assert_called_once_with("cached_online_users_set", [10, 15], timeout=5)

    def test_get_cached_online_user_ids_cache_hit(self, mocker):
        """Проверяет поведение при наличии множества пользователей онлайн в кеше."""
        mock_get_online = mocker.patch("users.services.online.get_online_user_ids")
        mock_cache = mocker.patch("users.services.online.cache")
        mock_cache.get.return_value = [5]

        result = get_cached_online_user_ids()

        assert result == [5]
        mock_cache.get.assert_called_once_with("cached_online_users_set")
        mock_get_online.assert_not_called()
        mock_cache.set.assert_not_called()
