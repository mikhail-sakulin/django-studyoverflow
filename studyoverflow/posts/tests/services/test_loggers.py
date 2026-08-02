from types import SimpleNamespace

import pytest

from posts.services import log_comment_event, log_like_event, log_post_event


@pytest.fixture
def mock_logger(mocker):
    return mocker.patch("posts.services.loggers.logger.info")


@pytest.fixture
def mock_user():
    """Фикстура stub авторизованного пользователя."""
    return SimpleNamespace(pk=1, username="test_user", is_authenticated=True)


@pytest.fixture
def mock_anon_user():
    """Фикстура stub неавторизованного пользователя."""
    return SimpleNamespace(pk=None, username="", is_authenticated=False)


class TestLogPostEvent:
    """Тесты функции log_post_event."""

    @pytest.fixture
    def mock_post(self):
        return SimpleNamespace(pk=10, title="Тестовый пост")

    @pytest.mark.parametrize(
        ("event_type", "expected_msg"),
        [
            ("post_create", "Пост создан: Тестовый пост (id: 10)."),
            ("post_update", "Пост отредактирован: Тестовый пост (id: 10)."),
            ("post_delete", "Пост удален: Тестовый пост (id: 10)."),
        ],
    )
    def test_post_event_with_auth_use(
        self, mock_logger, mock_user, mock_post, event_type, expected_msg
    ):
        """Успешное логирование различных событий поста."""
        log_post_event(event_type, mock_post, mock_user, source="api")

        mock_logger.assert_called_once_with(
            expected_msg,
            extra={
                "post_id": mock_post.pk,
                "source": "api",
                "event_type": event_type,
                "user_id": mock_user.pk,
            },
        )

    def test_post_event_with_anonymous_user(self, mock_logger, mock_anon_user, mock_post):
        """Для неавторизованного пользователя user_id устанавливается в None."""
        log_post_event("post_create", mock_post, mock_anon_user)

        _, kwargs = mock_logger.call_args
        assert kwargs["extra"]["user_id"] is None

    def test_unknown_event_type_uses_standard_message(self, mock_logger, mock_user, mock_post):
        """Неизвестный event_type логируется с дефолтным сообщением."""
        log_post_event("post_archive", mock_post, mock_user)

        args, _ = mock_logger.call_args
        assert args[0] == "Событие поста"


class TestLogCommentEvent:
    """Тесты функции log_comment_event."""

    @pytest.fixture
    def mock_comment(self):
        return SimpleNamespace(pk=20, post_id=10)

    @pytest.mark.parametrize(
        ("event_type", "expected_msg"),
        [
            (
                "comment_create",
                "Создан комментарий (id: 20) пользователем test_user к посту (id: 10).",
            ),
            (
                "comment_update",
                "Комментарий обновлен (id: 20) пользователем test_user к посту (id: 10).",
            ),
            (
                "comment_delete",
                "Комментарий удален (id: 20) пользователем test_user к посту (id: 10).",
            ),
        ],
    )
    def test_comment_events_write_log(
        self, mock_logger, mock_user, mock_comment, event_type, expected_msg
    ):
        """Успешное логирование различных событий комментария."""
        log_comment_event(event_type, mock_comment, mock_user, source="web")

        mock_logger.assert_called_once_with(
            expected_msg,
            extra={
                "comment_id": mock_comment.pk,
                "post_id": mock_comment.post_id,
                "user_id": mock_user.pk,
                "event_type": event_type,
                "source": "web",
            },
        )

    def test_comment_event_with_anonymous_user(self, mock_logger, mock_anon_user, mock_comment):
        """Для неавторизованного пользователя user_id устанавливается в None."""
        log_comment_event("comment_create", mock_comment, mock_anon_user)

        _, kwargs = mock_logger.call_args
        assert kwargs["extra"]["user_id"] is None

    def test_unknown_event_type_uses_standard_message(self, mock_logger, mock_user, mock_comment):
        """Неизвестный event_type логируется с дефолтным сообщением."""
        log_comment_event("comment_archive", mock_comment, mock_user)

        args, _ = mock_logger.call_args
        assert args[0] == "Событие комментария"


class TestLogLikeEvent:
    """Тесты функции log_like_event."""

    @pytest.fixture
    def mock_model_instance(self):
        """Фикстура для stub любого объекта моделей Post, Comment с замоканным Meta."""
        meta = SimpleNamespace(verbose_name="Пост", model_name="post")
        return SimpleNamespace(pk=30, _meta=meta)

    @pytest.mark.parametrize(
        ("event_type", "expected_msg"),
        [
            ("like_add", "Лайк добавлен к пост (id: 30) пользователем test_user."),
            ("like_remove", "Лайк удален у пост (id: 30) пользователем test_user."),
        ],
    )
    def test_like_events_write_log(
        self, mock_logger, mock_user, mock_model_instance, event_type, expected_msg
    ):
        """При добавлении и удалении лайка данные логируются."""
        log_like_event(event_type, mock_model_instance, mock_user, source="api")

        mock_logger.assert_called_once_with(
            expected_msg,
            extra={
                "object_id": mock_model_instance.pk,
                "object_type": "post",
                "user_id": mock_user.pk,
                "event_type": event_type,
                "source": "api",
            },
        )

    def test_like_event_with_anonymous_user(self, mock_logger, mock_anon_user, mock_model_instance):
        """Для неавторизованного пользователя user_id устанавливается в None."""
        log_like_event("like_add", mock_model_instance, mock_anon_user, "web")

        _, kwargs = mock_logger.call_args
        assert kwargs["extra"]["user_id"] is None

    def test_unknown_event_type_uses_standard_message(
        self, mock_logger, mock_user, mock_model_instance
    ):
        """Неизвестный event_type логируется с дефолтным сообщением."""
        log_like_event("like_unknown", mock_model_instance, mock_user, source="web")

        args, _ = mock_logger.call_args
        assert args[0] == "Событие лайка"
