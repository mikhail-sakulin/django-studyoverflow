import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from posts.models import Post


User = get_user_model()


@pytest.fixture(autouse=True)
def clear_cache():
    """Очищает кеш до и после каждого теста."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestPostListView:
    def test_status_and_context(self, client, post_factory):
        """Успешное получение постов, проверка данных в context."""
        post_factory.create_batch(2)
        url = reverse("posts:list")
        response = client.get(url)

        assert response.status_code == 200
        assert "posts" in response.context
        assert "filter_form" in response.context
        assert "all_tags" in response.context
        assert response.context["section_of_menu_selected"] == "posts:list"
        assert len(response.context["posts"]) == 2

    def test_tags_caching(self, client):
        """Теги из ContextTagMixin кешируются и не вызывают дублирующих SQL-запросов."""
        url = reverse("posts:list")
        # Создается кеш
        client.get(url)
        assert cache.get("all_tags_list") is not None

        # Получение списка SQL запросов при запросе client.get(url)
        with CaptureQueriesContext(connection) as queries:
            client.get(url)

        # Запроса к тегам не было из-за кеша, posts_lowercasetag - имя таблицы тегов
        assert not any("posts_lowercasetag" in q["sql"].lower() for q in queries)

    def test_filter_by_search_query_and_author(self, client, user_factory, post_factory):
        """
        Параметр 'q' ищет текст по title/content/tags_name,
        параметр 'author' фильтрует по автору.
        """
        alice = user_factory(username="alice")
        post_factory(author=alice, title="Python news", content="Some text")
        post_factory(title="Django news", content="advanced python usage")
        post_factory(tags=["python"])

        url = reverse("posts:list")

        resp = client.get(url, {"q": "python"})
        assert len(resp.context["posts"]) == 3

        resp = client.get(url, {"q": "yth"})
        assert len(resp.context["posts"]) == 3

        resp = client.get(url, {"author": "alice"})
        assert len(resp.context["posts"]) == 1
        assert resp.context["posts"][0].author == alice

    def test_filter_by_tags(self, client, post_factory):
        """Проверка фильтрации по тегам: tag_match=any (любой) и tag_match=all (все)."""
        post_factory(title="Only Py", tags=["python"])
        post_both_tags = post_factory(title="Async Py", tags=["python", "asyncio"])

        url = reverse("posts:list")

        resp_any = client.get(url, {"tags": "python,asyncio", "tag_match": "any"})
        assert len(resp_any.context["posts"]) == 2

        resp_all = client.get(url, {"tags": "python,asyncio", "tag_match": "all"})
        assert len(resp_all.context["posts"]) == 1
        assert resp_all.context["posts"][0] == post_both_tags

    def test_sorting(self, client, post_factory):
        """Сортировка по лайкам по убыванию."""
        title1 = "New title Post1"
        title2 = "New title Post2"
        post_factory(title=title1, likes_count=10)
        post_factory(title=title2, likes_count=20)

        url = reverse("posts:list")
        resp = client.get(url, {"sort": "likes", "order": "desc"})

        titles = [p.title for p in resp.context["posts"]]
        assert titles == [title2, title1]


@pytest.mark.django_db
class TestPostCreateView:
    def test_unauthenticated_redirect(self, assert_login_required):
        """GET-запрос без авторизации перенаправляет на страницу логина."""
        assert_login_required(url_name="posts:create", method="get")

    def test_successful_creation(self, client, user_factory, mocker):
        """Успешное создание поста: запись в БД, вызов логгера и показ success-сообщения."""
        user = user_factory()
        client.force_login(user)
        mock_log = mocker.patch("posts.views.post_views.log_post_event")

        url = reverse("posts:create")
        data = {"title": "Test New Post", "content": "Content", "tags": "django"}
        response = client.post(url, data, follow=True)

        assert response.status_code == 200
        assert Post.objects.filter(title="Test New Post", author=user).exists()

        # Проверка логгера
        mock_log.assert_called_once_with("post_create", mocker.ANY, user, source="web")

        # Проверка messages
        messages = list(response.context["messages"])
        assert any("пост успешно создан" in str(m).lower() for m in messages)


@pytest.mark.django_db
class TestPostDetailView:
    def test_nonexistent_post_returns_404(self, assert_not_found):
        """Для несуществующего поста возвращается 404."""
        assert_not_found(
            "posts:detail",
            url_kwargs={"pk": 9999, "slug": "none"},
            method="get",
            is_api=False,
        )

    def test_view_context(self, client, post_factory, assert_not_found):
        """Страница поста содержит пост и форму."""
        post = post_factory(title="Detail post")
        url = reverse("posts:detail", kwargs={"pk": post.pk, "slug": post.slug})

        resp = client.get(url)
        assert resp.status_code == 200
        assert resp.context["post"] == post
        assert "comment_form" in resp.context

    def test_caching_reduces_queries(self, client, post_factory):
        """Объект сохраняется в кеш."""
        post = post_factory()
        url = reverse("posts:detail", kwargs={"pk": post.pk, "slug": post.slug})

        # Первый запрос в БД без кеша
        with CaptureQueriesContext(connection) as queries_first:
            client.get(url)

        # Второй запрос - данные из кеша
        with CaptureQueriesContext(connection) as queries_second:
            client.get(url)

        assert len(queries_second) < len(queries_first)

        assert cache.get(f"post_detail_{post.pk}") is not None


@pytest.mark.django_db
class TestPostUpdateView:
    def test_unauthenticated_redirect(self, assert_login_required, post_factory):
        """GET и POST запросы без авторизации перенаправляет на страницу логина."""
        post = post_factory()
        kwargs = {"pk": post.pk, "slug": post.slug}

        assert_login_required(url_name="posts:edit", url_kwargs=kwargs, method="get")
        assert_login_required(url_name="posts:edit", url_kwargs=kwargs, method="post")

    def test_nonexistent_post_returns_404(self, client, user_factory, assert_not_found):
        """Для несуществующего поста возвращается 404."""
        client.force_login(user_factory())
        assert_not_found(
            "posts:edit",
            url_kwargs={"pk": 9999, "slug": "none"},
            method="get",
            is_api=False,
        )

    def test_permissions(self, client, user_factory, post_factory, assert_login_required):
        """Возвращает 403 для не авторов, 200 для авторов."""
        post = post_factory()
        kwargs = {"pk": post.pk, "slug": post.slug}
        url = reverse("posts:edit", kwargs=kwargs)

        # Не автор -> 403 на GET и POST
        client.force_login(user_factory())
        assert client.get(url).status_code == 403
        assert client.post(url).status_code == 403

        # Автор -> 200
        client.force_login(post.author)
        assert client.get(url).status_code == 200

    def test_moderator_can_edit_foreign_post(self, client, user_factory, post_factory, mocker):
        """Модератор с правом posts.moderate_post может редактировать чужой пост."""
        moderator = user_factory(role=User.Role.MODERATOR)
        post = post_factory()

        mock_log = mocker.patch("posts.views.post_views.log_post_event")

        client.force_login(moderator)
        url = reverse("posts:edit", kwargs={"pk": post.pk, "slug": post.slug})

        response = client.post(
            url, {"title": "Moderated title", "content": post.content, "tags": post.tags}
        )

        assert response.status_code == 302
        post.refresh_from_db()
        assert post.title == "Moderated title"
        mock_log.assert_called_once_with("post_update", post, moderator, source="web")

    def test_successful_edit(self, client, user_factory, post_factory, mocker):
        """Автор успешно редактирует пост, изменения сохраняются, событие логируется."""
        post = post_factory(title="Old title Post")
        client.force_login(post.author)
        mock_log = mocker.patch("posts.views.post_views.log_post_event")

        url = reverse("posts:edit", kwargs={"pk": post.pk, "slug": post.slug})
        client.post(url, {"title": "New title Post", "content": post.content, "tags": post.tags})

        post.refresh_from_db()
        assert post.title == "New title Post"
        mock_log.assert_called_once_with("post_update", post, post.author, source="web")


@pytest.mark.django_db
class TestPostDeleteView:
    def test_unauthenticated_redirect(self, assert_login_required, post_factory):
        """GET и POST запросы без авторизации перенаправляет на страницу логина."""
        post = post_factory()
        kwargs = {"pk": post.pk, "slug": post.slug}

        assert_login_required(url_name="posts:delete", url_kwargs=kwargs, method="get")
        assert_login_required(url_name="posts:delete", url_kwargs=kwargs, method="post")

    def test_nonexistent_post_returns_404(self, client, user_factory, assert_not_found):
        """Для несуществующего поста возвращается 404."""
        client.force_login(user_factory())
        assert_not_found(
            "posts:delete",
            url_kwargs={"pk": 9999, "slug": "none"},
            method="post",
            is_api=False,
        )

    def test_permissions(self, client, user_factory, post_factory, assert_login_required):
        """Возвращает 403 для не авторов, 200 для авторов."""
        post = post_factory()
        kwargs = {"pk": post.pk, "slug": post.slug}
        url = reverse("posts:delete", kwargs=kwargs)

        # Не автор -> 403 на GET и POST
        client.force_login(user_factory())
        assert client.get(url).status_code == 403
        assert client.post(url).status_code == 403

    def test_moderator_can_delete_foreign_post(self, client, user_factory, post_factory, mocker):
        """Модератор с правом posts.moderate_post может удалить чужой пост."""
        moderator = user_factory(role=User.Role.MODERATOR)
        post = post_factory()
        mock_log = mocker.patch("posts.views.post_views.log_post_event")

        client.force_login(moderator)
        url = reverse("posts:delete", kwargs={"pk": post.pk, "slug": post.slug})

        response = client.post(url, follow=True)

        assert response.status_code == 200
        assert not Post.objects.filter(pk=post.pk).exists()
        mock_log.assert_called_once_with("post_delete", mocker.ANY, moderator, source="web")

        messages = list(response.context["messages"])
        assert any("удален" in str(m).lower() for m in messages)

    def test_successful_delete(self, client, user_factory, post_factory, mocker):
        """Автор успешно удаляет пост, срабатывает логгер и возвращается сообщение."""
        post = post_factory()
        client.force_login(post.author)
        mock_log = mocker.patch("posts.views.post_views.log_post_event")

        url = reverse("posts:delete", kwargs={"pk": post.pk, "slug": post.slug})
        resp = client.post(url, follow=True)

        assert resp.status_code == 200
        assert not Post.objects.filter(pk=post.pk).exists()

        mock_log.assert_called_once_with("post_delete", mocker.ANY, post.author, source="web")

        messages = list(resp.context["messages"])
        assert any("удален" in str(m).lower() for m in messages)
