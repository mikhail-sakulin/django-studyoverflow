import pytest

from users.services import get_counts_map, get_reputation_map, update_user_counter_field


@pytest.mark.django_db
class TestUpdateUserCounterField:

    def test_raises_value_error_for_non_existent_field(self):
        """Если у модели User нет переданного поля, функция вызывает ValueError."""
        with pytest.raises(ValueError, match="User has no field invalid_field"):
            update_user_counter_field(author_id=1, counter_field="invalid_field", value_change=1)

    def test_successfully_increments_counter(self, user_factory):
        """Проверяет корректное атомарное увеличение счетчика пользователя."""
        user = user_factory(posts_count=2)

        update_user_counter_field(user.pk, "posts_count", 1)

        user.refresh_from_db()
        assert user.posts_count == 3

    def test_prevents_counter_from_dropping_below_zero(self, user_factory):
        """Проверяет работу Greatest: счетчик не может уйти в минус."""
        user = user_factory(posts_count=0)

        update_user_counter_field(user.pk, "posts_count", -1)

        user.refresh_from_db()
        assert user.posts_count == 0

    def test_does_not_affect_other_users(self, user_factory):
        """Обновление счетчика одного пользователя не должно затрагивать других."""
        target = user_factory(posts_count=5)
        other = user_factory(posts_count=5)

        update_user_counter_field(target.pk, "posts_count", 1)

        target.refresh_from_db()
        other.refresh_from_db()
        assert target.posts_count == 6
        assert other.posts_count == 5


class TestGetCountsMap:

    def test_returns_correct_counts_mapping_ignoring_none(self, mocker):
        """Проверяет сборку словаря агрегации и обработку пустого group_field."""
        mock_model = mocker.MagicMock()
        mock_model.objects.values.return_value.annotate.return_value = [
            {"author_id": 42, "count": 12},
            {"author_id": 100, "count": 1},
            {"author_id": None, "count": 5},
        ]

        result = get_counts_map(mock_model, "author_id")

        assert result == {42: 12, 100: 1}
        mock_model.objects.values.assert_called_once_with("author_id")


class TestGetReputationMap:

    def test_merges_post_and_comment_likes_correctly(self, mocker):
        """Проверяет суммирование лайков из постов и комментариев для каждого автора."""
        mock_post_model = mocker.MagicMock()
        mock_comment_model = mocker.MagicMock()

        # Лайки за посты
        mock_post_model.objects.values.return_value.annotate.return_value = [
            {"author_id": 1, "total_likes": 10},
            {"author_id": 2, "total_likes": 5},
            {"author_id": None, "total_likes": 99},
        ]
        # Лайки за комментарии
        mock_comment_model.objects.values.return_value.annotate.return_value = [
            {"author_id": 2, "total_likes": 3},
            {"author_id": 3, "total_likes": 15},
            {"author_id": None, "total_likes": 50},
        ]

        result = get_reputation_map(mock_post_model, mock_comment_model)

        assert result == {
            1: 10,
            2: 8,
            3: 15,
        }
