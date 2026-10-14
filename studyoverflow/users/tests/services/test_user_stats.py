import pytest

from posts.models import Comment, Post
from users.services.user_stats import get_counts_map, get_reputation_map, update_user_counter_field


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


@pytest.mark.django_db
class TestGetCountsMap:

    def test_returns_correct_counts_posts_mapping(self, user_factory, post_factory):
        """Проверяет сборку словаря агрегации для постов."""
        author_1, author_2 = user_factory(), user_factory()
        post_factory.create_batch(2, author=author_1)
        post_factory(author=author_2)

        assert get_counts_map(Post, "author_id") == {author_1.pk: 2, author_2.pk: 1}

        author_1.refresh_from_db()
        author_2.refresh_from_db()
        assert (author_1.posts_count, author_2.posts_count) == (2, 1)

    def test_returns_correct_counts_comments_mapping(
        self, user_factory, post_factory, comment_factory
    ):
        """Проверяет сборку словаря агрегации для комментариев."""
        post = post_factory()
        commenter = user_factory()
        comment_factory.create_batch(3, post=post, author=commenter)

        assert get_counts_map(Comment, "author_id") == {commenter.pk: 3}

        post.refresh_from_db()
        assert post.comments_count == 3

    def test_empty_table(self):
        """Проверяет работу при пустой таблице."""
        assert get_counts_map(Comment, "author_id") == {}


@pytest.mark.django_db
class TestGetReputationMap:

    def test_merges_post_and_comment_likes_correctly(
        self, user_factory, post_factory, comment_factory, like_factory
    ):
        """Проверяет суммирование лайков из постов и комментариев для каждого автора."""
        author_a, author_b = user_factory(), user_factory()
        liker_1, liker_2 = user_factory(), user_factory()

        post_a = post_factory(author=author_a)
        comment_b = comment_factory(post=post_a, author=author_b)
        like_factory(user=liker_1, content_object=post_a)
        like_factory(user=liker_2, content_object=post_a)
        like_factory(user=liker_1, content_object=comment_b)

        result = get_reputation_map(Post, Comment)

        assert result == {author_a.pk: 2, author_b.pk: 1}

        # Проверка значений в БД.
        # reputation - денормализованное поле-счетчик, изменяется через сигналы, значения
        # синхронизируются через периодические Celery-задачи.
        author_a.refresh_from_db()
        author_b.refresh_from_db()
        assert (author_a.reputation, author_b.reputation) == (2, 1)

    def test_author_without_likes_has_zero(self, user_factory, post_factory):
        """Для автора, у которого нет лайков, возвращается 0."""
        author = user_factory()
        post_factory(author=author)

        assert get_reputation_map(Post, Comment) == {author.pk: 0}
