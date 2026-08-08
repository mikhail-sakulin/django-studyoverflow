import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from posts.models import Comment, Like, LowercaseTag, Post


User = get_user_model()


@pytest.fixture(autouse=True)
def clear_cache():
    """Очищает кеш до и после каждого теста."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestPostViewSet:
    def test_retrieve_nonexistent_post_returns_404(self, assert_not_found):
        """Для несуществующего поста возвращается 404."""
        assert_not_found(
            "api:posts:posts-detail", url_kwargs={"pk": 9999}, method="get", is_api=True
        )

    def test_create_post_unauthenticated(self, assert_login_required):
        """Для создания поста требуется авторизация, иначе возвращается 401."""
        assert_login_required("api:posts:posts-list", method="post", is_api=True)

    def test_list_posts_success(self, api_client, post_factory):
        """Успешное получение списка постов."""
        post_factory.create_batch(2)
        url = reverse("api:posts:posts-list")
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["count"] == 2
        # Проверка LikeAnnotationsMixin для анонима (нет лайка)
        assert response.data["results"][0]["user_has_liked"] is False

    def test_filter_and_sort_mixins(self, api_client, user_factory, post_factory):
        """
        PostFilterSortMixin: проверка фильтрации по q, tags, author, has_comments,
        и сортировки по likes и created.
        """
        user1 = user_factory(username="user1")
        user2 = user_factory(username="user2")

        post_python = post_factory(
            author=user1, title="Python news", likes_count=10, tags=["python", "backend"]
        )

        post_django = post_factory(
            author=user2,
            title="Django basics",
            likes_count=20,
            comments_count=1,
            tags=["python", "django"],
        )

        url = reverse("api:posts:posts-list")

        # Фильтр по q
        resp_q = api_client.get(url, {"q": "pyth"})
        assert resp_q.data["count"] == 2

        # Фильтр по author
        resp_author = api_client.get(url, {"author": "user1"})
        assert resp_author.data["count"] == 1
        assert resp_author.data["results"][0]["id"] == post_python.id

        # Фильтр по tags (any)
        resp_tags = api_client.get(url, {"tags": "django,frontend"})
        assert resp_tags.data["count"] == 1
        assert resp_tags.data["results"][0]["id"] == post_django.id

        # Фильтр по tags (all)
        resp_tags_all = api_client.get(url, {"tags": "python,django", "tag_match": "all"})
        assert resp_tags_all.data["count"] == 1
        assert resp_tags_all.data["results"][0]["id"] == post_django.id

        # Фильтр по наличию комментариев
        resp_comments = api_client.get(url, {"has_comments": "yes"})
        assert resp_comments.data["count"] == 1
        assert resp_comments.data["results"][0]["id"] == post_django.id

        # Сортировка по likes (по убыванию)
        resp_sort = api_client.get(url, {"sort": "likes", "order": "desc"})
        assert resp_sort.data["results"][0]["id"] == post_django.id
        assert resp_sort.data["results"][1]["id"] == post_python.id

    def test_retrieve_post_success(self, api_client, post_factory):
        """Успешное получение детальной информации о посте."""
        post = post_factory(title="API test detail")
        url = reverse("api:posts:posts-detail", kwargs={"pk": post.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["title"] == "API test detail"

    def test_retrieve_post_uses_cache(self, api_client, post_factory):
        """
        Повторное получение поста использует кеш и уменьшает количество SQL-запросов.
        """
        post = post_factory()

        url = reverse(
            "api:posts:posts-detail",
            kwargs={"pk": post.pk},
        )

        # Первый запрос - пост сохраняется в кеш
        with CaptureQueriesContext(connection) as queries_first:
            response = api_client.get(url)

        assert response.status_code == 200

        # Второй запрос - пост берется из кеша
        with CaptureQueriesContext(connection) as queries_second:
            response = api_client.get(url)

        assert response.status_code == 200

        assert len(queries_second) < len(queries_first)

        # Пост находится в кеше
        assert cache.get(f"post_detail_{post.pk}") is not None

    def test_create_post_success(self, api_client, user_factory, mocker):
        """Авторизованный пользователь успешно создает пост, вызывается логгер."""
        user = user_factory()
        api_client.force_authenticate(user=user)
        mock_log = mocker.patch("posts.api.views.log_post_event")

        url = reverse("api:posts:posts-list")
        data = {"title": "New API Post", "content": "API Content", "tags": ["drf", "api"]}

        response = api_client.post(url, data, format="json")

        assert response.status_code == 201
        assert response.data["title"] == "New API Post"
        assert Post.objects.filter(title="New API Post", author=user).exists()

        mock_log.assert_called_once_with("post_create", mocker.ANY, user, source="api")

    def test_update_post_unauthenticated(self, assert_login_required, post_factory):
        """Для редактирования поста требуется авторизация, иначе возвращается 401."""
        post = post_factory()
        assert_login_required(
            "api:posts:posts-detail", url_kwargs={"pk": post.pk}, method="patch", is_api=True
        )

    def test_delete_post_unauthenticated(self, assert_login_required, post_factory):
        """Для удаления поста требуется авторизация, иначе возвращается 401."""
        post = post_factory()
        assert_login_required(
            "api:posts:posts-detail", url_kwargs={"pk": post.pk}, method="delete", is_api=True
        )

    def test_update_post_permissions(self, api_client, user_factory, post_factory):
        """Редактировать пост может автор, другой пользователь не модератор - не может."""
        post = post_factory(title="Old title")
        other_user = user_factory()
        url = reverse("api:posts:posts-detail", kwargs={"pk": post.pk})

        # Не автор -> 403
        api_client.force_authenticate(user=other_user)
        response = api_client.patch(url, {"title": "Hack"}, format="json")
        assert response.status_code == 403

        # Автор -> 200
        api_client.force_authenticate(user=post.author)
        response = api_client.patch(url, {"title": "Updated title"}, format="json")
        assert response.status_code == 200
        assert response.data["title"] == "Updated title"

    def test_delete_post_permissions(self, api_client, user_factory, post_factory):
        """Удалить пост может автор, другой пользователь не модератор - не может."""
        post = post_factory(title="Old title")
        other_user = user_factory()
        url = reverse("api:posts:posts-detail", kwargs={"pk": post.pk})

        # Не автор -> 403
        api_client.force_authenticate(user=other_user)
        response = api_client.delete(url, {"title": "Hack"}, format="json")
        assert response.status_code == 403

        # Автор -> 204
        api_client.force_authenticate(user=post.author)
        response = api_client.delete(url, {"title": "Updated title"}, format="json")
        assert response.status_code == 204
        assert not Post.objects.filter(pk=post.pk).exists()

    def test_moderator_can_update_and_delete_post(
        self, api_client, user_factory, post_factory, mocker
    ):
        """Модератор с правами posts.moderate_post может изменять и удалять чужие посты."""
        moderator = user_factory(role=User.Role.MODERATOR)
        post = post_factory()
        url = reverse("api:posts:posts-detail", kwargs={"pk": post.pk})

        api_client.force_authenticate(user=moderator)
        mock_log = mocker.patch("posts.api.views.log_post_event")

        # Update
        response_patch = api_client.patch(url, {"title": "Moderated title"}, format="json")
        assert response_patch.status_code == 200
        mock_log.assert_called_with("post_update", mocker.ANY, moderator, source="api")

        # Delete
        response_delete = api_client.delete(url)
        assert response_delete.status_code == 204
        assert not Post.objects.filter(pk=post.pk).exists()
        mock_log.assert_called_with("post_delete", mocker.ANY, moderator, source="api")


@pytest.mark.django_db
class TestCommentViewSet:
    def test_retrieve_nonexistent_comment_returns_404(self, assert_not_found, post_factory):
        """Для несуществующего комментария возвращается 404."""
        post = post_factory()
        assert_not_found(
            "api:posts:post-comments-detail",
            url_kwargs={"post_pk": post.pk, "pk": 9999},
            method="get",
            is_api=True,
        )

    def test_create_comment_unauthenticated(self, assert_login_required, post_factory):
        """Для создания комментария требуется авторизация, иначе возвращается 401."""
        post = post_factory()
        assert_login_required(
            "api:posts:post-comments-list",
            url_kwargs={"post_pk": post.pk},
            method="post",
            is_api=True,
        )

    def test_list_comments_tree_and_sort_mixin(self, api_client, post_factory, comment_factory):
        """
        Проверка возврата древовидной структуры комментариев поста, кастомных полей пагинации
        (parents_comments_count, all_comments_count) и работы сортировки (CommentSortMixin).
        """
        post = post_factory(comments_count=3)
        root_comment1 = comment_factory(post=post, likes_count=5)
        root_comment2 = comment_factory(post=post, likes_count=10)

        # Дочерний комментарий
        comment_factory(post=post, parent_comment=root_comment2, reply_to=root_comment2)

        url = reverse("api:posts:post-comments-list", kwargs={"post_pk": post.pk})

        # Сортировка по лайкам по убыванию
        response = api_client.get(url, {"comment_sort": "likes", "comment_order": "desc"})

        assert response.status_code == 200
        assert response.data["parents_comments_count"] == 2
        # Всего комментариев 3 + 3 = 6, из-за post = post_factory(comments_count=3)
        assert response.data["all_comments_count"] == 6
        assert len(response.data["results"]) == 2

        # Проверка порядка корневых комментариев
        assert response.data["results"][0]["id"] == root_comment2.pk
        assert response.data["results"][1]["id"] == root_comment1.pk

        # Проверка вложенности (children_count и prefetch_related)
        assert response.data["results"][0]["children_count"] == 1
        assert "child_comments" in response.data["results"][0]

    def test_comment_thread_action(self, api_client, post_factory, comment_factory):
        """Проверка работы кастомного endpoint'а ветки комментариев thread."""
        post = post_factory()
        root_comment = comment_factory(post=post)
        child_comment = comment_factory(
            post=post, parent_comment=root_comment, reply_to=root_comment
        )

        # Запрашивается ветка, через ID дочернего комментария
        url = reverse(
            "api:posts:post-comments-thread", kwargs={"post_pk": post.pk, "pk": child_comment.pk}
        )
        response = api_client.get(url)

        assert response.status_code == 200
        # Возвращается родительский комментарий (корень ветки)
        assert response.data["id"] == root_comment.pk
        # Дочерний комментарий должен быть в child_comments
        assert len(response.data["child_comments"]) == 1
        assert response.data["child_comments"][0]["id"] == child_comment.pk

    def test_create_comment_success(self, api_client, user_factory, post_factory, mocker):
        """Успешное создание комментария с привязкой к посту, вызывается логгер."""
        user = user_factory()
        post = post_factory()
        api_client.force_authenticate(user=user)
        mock_log = mocker.patch("posts.api.views.log_comment_event")

        url = reverse("api:posts:post-comments-list", kwargs={"post_pk": post.pk})
        data = {"content": "API Comment content"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == 201
        assert "API Comment content" in response.data["rendered_content"]
        assert Comment.objects.filter(
            post=post, author=user, content="API Comment content"
        ).exists()

        mock_log.assert_called_once_with("comment_create", mocker.ANY, user, source="api")

    def test_update_and_delete_comment_permissions(self, api_client, user_factory, comment_factory):
        """
        Изменить или удалить комментарий может автор, другой пользователь не модератор - не может.
        """
        comment = comment_factory(content="Old comment")
        other_user = user_factory()
        url = reverse(
            "api:posts:post-comments-detail", kwargs={"post_pk": comment.post.pk, "pk": comment.pk}
        )

        # Не автор -> 403
        api_client.force_authenticate(user=other_user)
        assert api_client.patch(url, {"content": "Hack"}, format="json").status_code == 403
        assert api_client.delete(url).status_code == 403

        # Автор -> 200, 204
        api_client.force_authenticate(user=comment.author)
        assert (
            api_client.patch(url, {"content": "Updated comment"}, format="json").status_code == 200
        )
        assert api_client.delete(url).status_code == 204
        assert not Comment.objects.filter(pk=comment.pk).exists()

    def test_moderator_can_update_and_delete_post(
        self, api_client, user_factory, comment_factory, mocker
    ):
        """
        Модератор с правами comments.moderate_comment может изменять и удалять чужие комментарии.
        """
        moderator = user_factory(role=User.Role.MODERATOR)
        comment = comment_factory(content="Old comment")
        url = reverse(
            "api:posts:post-comments-detail", kwargs={"post_pk": comment.post.pk, "pk": comment.pk}
        )

        api_client.force_authenticate(user=moderator)
        mock_log = mocker.patch("posts.api.views.log_comment_event")

        # Update
        response_patch = api_client.patch(url, {"content": "Moderated content"}, format="json")
        assert response_patch.status_code == 200
        mock_log.assert_called_with("comment_update", mocker.ANY, moderator, source="api")

        # Delete
        response_delete = api_client.delete(url)
        assert response_delete.status_code == 204
        assert not Comment.objects.filter(pk=comment.pk).exists()
        mock_log.assert_called_with("comment_delete", mocker.ANY, moderator, source="api")


@pytest.mark.django_db
class TestLikeMixin:
    """Тестирование LikeMixin на примере постов ('toggle-like' и 'likers-list')."""

    def test_toggle_like_nonexistent_post_returns_404(
        self, assert_not_found, user_factory, api_client
    ):
        """Для несуществующего поста возвращается 404."""
        user = user_factory()
        api_client.force_authenticate(user=user)
        assert_not_found(
            "api:posts:posts-like", url_kwargs={"pk": 9999}, method="post", is_api=True
        )

    def test_toggle_like_unauthenticated(self, assert_login_required, post_factory):
        """Для постановки или снятия лайка требуется авторизация, иначе возвращается 401."""
        post = post_factory()
        assert_login_required(
            "api:posts:posts-like", url_kwargs={"pk": post.pk}, method="post", is_api=True
        )

    def test_toggle_like_success(self, api_client, user_factory, post_factory, mocker):
        """Успешное переключение лайка (toggle-like)."""
        user = user_factory()
        post = post_factory()
        api_client.force_authenticate(user=user)

        mock_perform = mocker.patch(
            "posts.api.views.perform_toggle_like",
            # (liked_now, likes_count)
            return_value=(True, 1),
        )

        url = reverse("api:posts:posts-like", kwargs={"pk": post.pk})
        response = api_client.post(url)

        assert response.status_code == 200
        assert response.data["liked_now"] is True
        assert response.data["likes_count_on_object"] == 1

        mock_perform.assert_called_once_with(user, post, source="api")

    def test_likes_list_success(self, api_client, user_factory, post_factory, mocker):
        """Успешное получение списка лайкнувших пользователей (likers-list)."""
        user1 = user_factory(username="liker1")
        user2 = user_factory(username="liker2")
        post = post_factory()

        Like.objects.create(user=user1, content_object=post)
        Like.objects.create(user=user2, content_object=post)

        url = reverse("api:posts:posts-likes", kwargs={"pk": post.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        results = response.data["results"]

        assert len(results) == 2
        usernames = [user["username"] for user in results]
        assert "liker1" in usernames
        assert "liker2" in usernames


@pytest.mark.django_db
class TestTagReadOnlyViewSet:
    def test_retrieve_nonexistent_tag_returns_404(self, assert_not_found):
        """Для несуществующего тега возвращается 404."""
        assert_not_found(
            "api:posts:tags-detail", url_kwargs={"pk": 9999}, method="get", is_api=True
        )

    def test_list_and_search_tags(self, api_client):
        """Получение списка тегов и корректная работа фильтра '?search='."""
        LowercaseTag.objects.create(name="python")
        LowercaseTag.objects.create(name="django")
        LowercaseTag.objects.create(name="postgres")

        url = reverse("api:posts:tags-list")

        # Список тегов
        resp_all = api_client.get(url)
        assert resp_all.status_code == 200
        results_all = resp_all.data["results"] if "results" in resp_all.data else resp_all.data
        assert len(results_all) == 3

        # Поиск по подстроке
        resp_search = api_client.get(url, {"search": "thon"})
        results_search = resp_search.data
        assert len(results_search) == 1
        assert results_search[0]["name"] == "python"

    def test_list_tags_uses_cache(self, api_client):
        """Проверка, что при получении списка тегов без фильтрации используется кеш."""
        LowercaseTag.objects.create(name="python")
        LowercaseTag.objects.create(name="django")

        url = reverse("api:posts:tags-list")

        # Первый запрос - кеш пуст, происходит запрос к БД
        response_first = api_client.get(url)
        assert response_first.status_code == 200
        assert cache.get("all_tags_list") is not None

        # Второй запрос - данные берутся из кеша
        with CaptureQueriesContext(connection) as queries:
            response_second = api_client.get(url)

        assert response_second.status_code == 200
        # Проверка отсутствия запросов к таблице тегов
        assert not any("posts_lowercasetag" in q["sql"].lower() for q in queries)

        # Третий запрос - используется фильтрация, кеш должен игнорироваться
        with CaptureQueriesContext(connection) as search_queries:
            response_search = api_client.get(url, {"search": "py"})

        assert response_search.status_code == 200
        # Проверка, что при фильтрации был запрос к БД
        assert any("posts_lowercasetag" in q["sql"].lower() for q in search_queries)
