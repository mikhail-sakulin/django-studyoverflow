import pytest

from posts.models import Post


@pytest.mark.django_db
class TestIContainsILikeLookup:
    """
    Проверка кастомного лукапа (Lookup) для Django ORM, реализующего оператор ILIKE в PostgreSQL.
    """

    def test_ilike_icontains_search(self, post_factory):
        """Проверка работы лукапа: регистронезависимый поиск по подстроке."""
        post_target_1 = post_factory(title="Основы Python и Django")
        post_target_2 = post_factory(title="Продвинутый PYTHON")
        post_not_target = post_factory(title="Изучаем JavaScript")

        results = Post.objects.filter(title__ilike_icontains="yth")

        assert results.count() == 2
        assert post_target_1 in results
        assert post_target_2 in results
        assert post_not_target not in results
