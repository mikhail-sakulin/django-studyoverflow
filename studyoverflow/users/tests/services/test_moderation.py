import pytest
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from users.services import block_user_service, unblock_user_service


@pytest.mark.django_db
class TestUserBlockServices:

    @pytest.mark.parametrize(
        "service_func",
        [
            block_user_service,
            unblock_user_service,
        ],
    )
    def test_permission_denied(self, user_factory, mocker, service_func):
        mocker.patch("users.services.can_moderate", return_value=False)

        moderator = user_factory()
        target_user = user_factory()

        with pytest.raises(PermissionDenied) as exc:
            service_func(moderator, target_user)

        assert "Нельзя модерировать" in str(exc.value)

    @pytest.mark.parametrize(
        (
            "service_func",
            "initial_blocked",
            "expected_blocked",
            "event_type",
            "source",
            "service_kwargs",
        ),
        [
            (block_user_service, False, True, "user_blocked", "unknown", {}),
            (unblock_user_service, True, False, "user_unblocked", "api", {"source": "api"}),
        ],
    )
    def test_set_user_block_state_success(
        self,
        user_factory,
        mocker,
        service_func,
        initial_blocked,
        expected_blocked,
        event_type,
        source,
        service_kwargs,
    ):
        mocker.patch("users.services.moderation.can_moderate", return_value=True)
        mock_logger = mocker.patch("users.services.moderation.logger.info")

        now_mock = timezone.now()
        mocker.patch("users.services.moderation.timezone.now", return_value=now_mock)

        moderator = user_factory(username="mod_user")
        target_user = user_factory(username="target_user", is_blocked=initial_blocked)

        if initial_blocked:
            target_user.blocked_at = now_mock - timezone.timedelta(days=1)
            target_user.blocked_by = moderator
            target_user.save()

        success, message = service_func(moderator, target_user, **service_kwargs)

        assert success is True
        state_word = "заблокирован" if expected_blocked else "разблокирован"
        assert message == f"Пользователь target_user успешно {state_word}."

        # Проверка, что данные были записаны в БД (объект обновляет значение атрибутов на
        # значения из БД)
        target_user.refresh_from_db()
        assert target_user.is_blocked is expected_blocked

        if expected_blocked:
            assert target_user.blocked_at == now_mock
            assert target_user.blocked_by == moderator
        else:
            assert target_user.blocked_at is None
            assert target_user.blocked_by is None

        # Проверка лога
        mock_logger.assert_called_once()
        _, kwargs = mock_logger.call_args
        assert kwargs["extra"] == {
            "moderator_id": moderator.pk,
            "target_user_id": target_user.pk,
            "event_type": event_type,
            "source": source,
        }

    @pytest.mark.parametrize(
        ("service_func", "initial_blocked", "expected_msg"),
        [
            (block_user_service, True, "Пользователь target_user уже заблокирован."),
            (unblock_user_service, False, "Пользователь target_user уже разблокирован."),
        ],
    )
    def test_set_user_block_state_already_in_state(
        self, user_factory, mocker, service_func, initial_blocked, expected_msg
    ):
        mocker.patch("users.services.moderation.can_moderate", return_value=True)
        mock_logger = mocker.patch("users.services.moderation.logger.info")

        moderator = user_factory()
        target_user = user_factory(username="target_user", is_blocked=initial_blocked)

        success, message = service_func(moderator, target_user)

        assert success is False
        assert message == expected_msg
        mock_logger.assert_not_called()
