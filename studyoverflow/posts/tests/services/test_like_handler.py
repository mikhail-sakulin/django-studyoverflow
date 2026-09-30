import pytest

from posts.services.like_handler import perform_toggle_like


@pytest.mark.django_db
class TestPerformToggleLike:
    """Тестирование сервисной функции переключения лайков."""

    def test_perform_toggle_like_add(self, mocker):
        """Если лайка не было, он создается, логируется и возвращается (True, count)."""
        user = mocker.MagicMock()
        obj = mocker.MagicMock()
        obj.likes_count = 1
        source = "web"
        pk = 1

        queryset = mocker.MagicMock()
        queryset.select_for_update.return_value.get.return_value = obj

        # Мокается новый созданный лайк
        fake_like = mocker.MagicMock()
        obj.likes.get_or_create.return_value = (fake_like, True)

        mock_log = mocker.patch("posts.services.like_handler.log_like_event")

        returned_obj, created = perform_toggle_like(
            user=user, queryset=queryset, pk=pk, source=source
        )

        assert created is True
        assert returned_obj is obj
        assert returned_obj.likes_count == 1

        fake_like.delete.assert_not_called()

        mock_log.assert_called_once_with(
            event_type="like_add",
            obj=obj,
            user=user,
            source=source,
        )
        obj.refresh_from_db.assert_called_once_with(fields=["likes_count"])

    def test_perform_toggle_like_remove(self, mocker):
        """Если лайк уже существовал, он удаляется, логируется и возвращается (False, count)."""
        user = mocker.MagicMock()
        obj = mocker.MagicMock()
        obj.likes_count = 0
        source = "api"
        pk = 1

        queryset = mocker.MagicMock()
        queryset.select_for_update.return_value.get.return_value = obj

        # Мокается уже существующий лайк
        fake_like = mocker.MagicMock()
        obj.likes.get_or_create.return_value = (fake_like, False)

        mock_log = mocker.patch("posts.services.like_handler.log_like_event")

        returned_obj, created = perform_toggle_like(
            user=user, queryset=queryset, pk=pk, source=source
        )

        assert created is False
        assert returned_obj is obj
        assert returned_obj.likes_count == 0

        fake_like.delete.assert_called_once()

        mock_log.assert_called_once_with(
            event_type="like_remove",
            obj=obj,
            user=user,
            source=source,
        )
        obj.refresh_from_db.assert_called_once_with(fields=["likes_count"])
