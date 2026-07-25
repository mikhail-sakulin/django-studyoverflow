from posts.services import perform_toggle_like


class TestPerformToggleLike:
    """Тестирование сервисной функции переключения лайков."""

    def test_perform_toggle_like_add(self, mocker):
        """Если лайка не было, он создается, логируется и возвращается (True, count)."""
        user = mocker.MagicMock()
        obj = mocker.MagicMock()
        obj.likes_count = 1
        source = "web"

        # Мокается новый созданный лайк
        fake_like = mocker.MagicMock()
        obj.likes.get_or_create.return_value = (fake_like, True)

        mock_log = mocker.patch("posts.services.like_handler.log_like_event")

        created, likes_count = perform_toggle_like(user=user, obj=obj, source=source)

        assert created is True
        assert likes_count == 1

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

        # Мокается уже существующий лайк
        fake_like = mocker.MagicMock()
        obj.likes.get_or_create.return_value = (fake_like, False)

        mock_log = mocker.patch("posts.services.like_handler.log_like_event")

        created, likes_count = perform_toggle_like(user=user, obj=obj, source=source)

        assert created is False
        assert likes_count == 0

        fake_like.delete.assert_called_once()

        mock_log.assert_called_once_with(
            event_type="like_remove",
            obj=obj,
            user=user,
            source=source,
        )
        obj.refresh_from_db.assert_called_once_with(fields=["likes_count"])
