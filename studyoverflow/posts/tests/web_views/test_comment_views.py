import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from posts.models import Comment


User = get_user_model()


@pytest.mark.django_db
class TestCommentListView:
    def test_nonexistent_post_returns_404(self, assert_not_found):
        """Для несуществующего поста при запросе комментариев возвращается 404."""
        assert_not_found(
            "posts:comment_list",
            url_kwargs={"post_pk": 9999, "post_slug": "none"},
            method="get",
            is_api=False,
        )

    def test_status_and_context(self, client, post_factory, comment_factory):
        """
        Успешное получение списка комментариев, проверка данных в context.
        """
        post = post_factory()
        comment_factory.create_batch(2, post=post)

        url = reverse("posts:comment_list", kwargs={"post_pk": post.pk, "post_slug": post.slug})
        response = client.get(url)

        assert response.status_code == 200
        assert "root_comments" in response.context
        assert "comment_form" in response.context
        assert response.context["post"] == post
        assert response.context["post_pk"] == post.pk
        assert response.context["post_slug"] == post.slug
        assert len(response.context["root_comments"]) == 2


@pytest.mark.django_db
class TestCommentRootCreateView:
    def test_unauthenticated_redirect(self, assert_login_required, post_factory):
        """POST-запрос без авторизации перенаправляет на страницу логина."""
        post = post_factory()
        url_kwargs = {"post_pk": post.pk, "post_slug": post.slug}
        assert_login_required(
            url_name="posts:comment_root_create", url_kwargs=url_kwargs, method="post"
        )

    def test_successful_creation(self, client, user_factory, post_factory, mocker):
        """
        Успешное создание корневого комментария: запись в БД, логгер и htmx триггер commentsUpdated.
        """
        user = user_factory()
        client.force_login(user)
        post = post_factory()

        mock_log = mocker.patch("posts.views.comment_views.log_comment_event")

        url = reverse(
            "posts:comment_root_create", kwargs={"post_pk": post.pk, "post_slug": post.slug}
        )
        data = {"content": "Test root comment"}
        response = client.post(url, data, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        assert Comment.objects.filter(content="Test root comment", author=user, post=post).exists()

        mock_log.assert_called_once_with("comment_create", mocker.ANY, user, source="web")

        trigger = json.loads(response["HX-Trigger"])
        assert "commentsUpdated" in trigger

    def test_invalid_form_returns_error_trigger(self, client, user_factory, post_factory):
        """
        Невалидная форма возвращает htmx триггер ошибки commentRootFormError
        без создания комментария.
        """
        user = user_factory()
        client.force_login(user)
        post = post_factory()

        url = reverse(
            "posts:comment_root_create", kwargs={"post_pk": post.pk, "post_slug": post.slug}
        )
        data = {"content": ""}
        response = client.post(url, data, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        assert not Comment.objects.filter(post=post).exists()

        trigger = json.loads(response["HX-Trigger"])
        assert "commentRootFormError" in trigger


@pytest.mark.django_db
class TestCommentChildCreateView:
    def test_successful_creation(self, client, user_factory, post_factory, comment_factory, mocker):
        """Успешное создание дочернего комментария с указанием reply_to и "parent_comment"."""
        user = user_factory()
        client.force_login(user)
        post = post_factory()
        root_comment = comment_factory(post=post)

        mock_log = mocker.patch("posts.views.comment_views.log_comment_event")

        url = reverse(
            "posts:comment_child_create", kwargs={"post_pk": post.pk, "post_slug": post.slug}
        )
        data = {
            "content": "Test child comment",
            "reply_to": root_comment.pk,
            "parent_comment": root_comment.pk,
        }
        response = client.post(url, data, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        assert Comment.objects.filter(content="Test child comment", reply_to=root_comment).exists()

        mock_log.assert_called_once_with("comment_create", mocker.ANY, user, source="web")

        trigger = json.loads(response["HX-Trigger"])
        assert "commentsUpdated" in trigger

    def test_missing_reply_to_creates_root_comment(self, client, user_factory, post_factory):
        """Если reply_to не указан, создается корневой комментарий."""
        user = user_factory()
        client.force_login(user)
        post = post_factory()

        url = reverse(
            "posts:comment_child_create", kwargs={"post_pk": post.pk, "post_slug": post.slug}
        )
        data = {"content": "No reply to"}
        response = client.post(url, data, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        assert Comment.objects.filter(
            content="No reply to", post=post, reply_to__isnull=True
        ).exists()

        trigger = json.loads(response["HX-Trigger"])
        assert "commentsUpdated" in trigger

    def test_invalid_reply_to_triggers_refresh(self, client, user_factory, post_factory):
        """Некорректный reply_to и невалидная форма вызывают HX-Refresh."""
        user = user_factory()
        client.force_login(user)
        post = post_factory()

        url = reverse(
            "posts:comment_child_create", kwargs={"post_pk": post.pk, "post_slug": post.slug}
        )
        data = {"content": "Test", "reply_to": 99999}
        response = client.post(url, data, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        assert response.get("HX-Refresh") == "true"


@pytest.mark.django_db
class TestCommentUpdateView:
    def test_unauthenticated_redirect(self, assert_login_required, comment_factory):
        """POST-запрос без авторизации перенаправляет на страницу логина."""
        comment = comment_factory()
        kwargs = {
            "post_pk": comment.post.pk,
            "post_slug": comment.post.slug,
            "comment_pk": comment.pk,
        }
        assert_login_required(url_name="posts:comment_update", url_kwargs=kwargs, method="post")

    def test_nonexistent_post_returns_404(self, client, user_factory, assert_not_found):
        """Для несуществующего поста при запросе обновления комментария возвращается 404."""
        client.force_login(user_factory())
        assert_not_found(
            "posts:comment_update",
            url_kwargs={"post_pk": 9999, "post_slug": "none", "comment_pk": 9999},
            method="post",
            is_api=False,
        )

    def test_nonexistent_comment_returns_update_trigger(
        self, client, user_factory, post_factory, assert_not_found
    ):
        """
        Для несуществующего комментария HTMXHandle404CommentMixin возвращает htmx триггер
        обновления комментариев.
        """
        user = user_factory()
        client.force_login(user)
        post = post_factory()

        url = reverse(
            "posts:comment_update",
            kwargs={"post_pk": post.pk, "post_slug": post.slug, "comment_pk": 9999},
        )
        response = client.post(url, {"content": "New"}, HTTP_HX_REQUEST="true")

        # возвращается 200 для корректной работы htmx
        assert response.status_code == 200
        trigger = json.loads(response["HX-Trigger"])
        assert "commentsUpdated" in trigger

    def test_permissions(self, client, user_factory, comment_factory):
        """Возвращает 403, если пользователь не является автором комментария."""
        comment = comment_factory()
        url = reverse(
            "posts:comment_update",
            kwargs={
                "post_pk": comment.post.pk,
                "post_slug": comment.post.slug,
                "comment_pk": comment.pk,
            },
        )

        client.force_login(user_factory())
        assert client.post(url, {"content": "Hack"}, HTTP_HX_REQUEST="true").status_code == 403

    def test_successful_update(self, client, comment_factory, mocker):
        """
        Автор успешно редактирует комментарий, изменения сохраняются, возвращается htmx триггер.
        """
        comment = comment_factory(content="Old content")
        client.force_login(comment.author)
        mock_log = mocker.patch("posts.views.comment_views.log_comment_event")

        url = reverse(
            "posts:comment_update",
            kwargs={
                "post_pk": comment.post.pk,
                "post_slug": comment.post.slug,
                "comment_pk": comment.pk,
            },
        )
        response = client.post(url, {"content": "New content"}, HTTP_HX_REQUEST="true")

        comment.refresh_from_db()
        assert comment.content == "New content"

        mock_log.assert_called_once_with("comment_update", comment, comment.author, source="web")

        trigger = json.loads(response["HX-Trigger"])
        assert "commentUpdateSuccess" in trigger
        assert trigger["commentUpdateSuccess"]["commentId"] == comment.pk

    def test_moderator_can_update_foreign_comment(
        self, client, user_factory, comment_factory, mocker
    ):
        """Модератор с правом posts.moderate_comment может редактировать чужой комментарий."""
        moderator = user_factory(role=User.Role.MODERATOR)
        comment = comment_factory(content="Original")
        client.force_login(moderator)

        mock_log = mocker.patch("posts.views.comment_views.log_comment_event")

        url = reverse(
            "posts:comment_update",
            kwargs={
                "post_pk": comment.post.pk,
                "post_slug": comment.post.slug,
                "comment_pk": comment.pk,
            },
        )

        response = client.post(url, {"content": "Moderated"}, HTTP_HX_REQUEST="true")

        assert response.status_code == 200

        comment.refresh_from_db()
        assert comment.content == "Moderated"

        mock_log.assert_called_once_with("comment_update", comment, moderator, source="web")

        trigger = json.loads(response["HX-Trigger"])
        assert "commentUpdateSuccess" in trigger
        assert trigger["commentUpdateSuccess"]["commentId"] == comment.pk

    def test_invalid_form_returns_error_trigger(self, client, comment_factory):
        """При невалидных данных форма возвращает htmx триггер ошибки с ID комментария."""
        comment = comment_factory(content="Old content")
        client.force_login(comment.author)

        url = reverse(
            "posts:comment_update",
            kwargs={
                "post_pk": comment.post.pk,
                "post_slug": comment.post.slug,
                "comment_pk": comment.pk,
            },
        )
        response = client.post(url, {"content": ""}, HTTP_HX_REQUEST="true")

        trigger = json.loads(response["HX-Trigger"])
        assert "commentUpdateError" in trigger
        assert trigger["commentUpdateError"]["commentId"] == comment.pk


@pytest.mark.django_db
class TestCommentDeleteView:
    def test_unauthenticated_redirect(self, assert_login_required, comment_factory):
        """POST-запрос без авторизации перенаправляет на логин."""
        comment = comment_factory()
        kwargs = {
            "post_pk": comment.post.pk,
            "post_slug": comment.post.slug,
            "comment_pk": comment.pk,
        }
        assert_login_required(url_name="posts:comment_delete", url_kwargs=kwargs, method="post")

    def test_nonexistent_post_returns_404(self, client, user_factory, assert_not_found):
        """Для несуществующего поста при запросе удаления комментария возвращается 404."""
        client.force_login(user_factory())
        assert_not_found(
            "posts:comment_delete",
            url_kwargs={"post_pk": 9999, "post_slug": "none", "comment_pk": 9999},
            method="post",
            is_api=False,
        )

    def test_permissions(self, client, user_factory, comment_factory):
        """Возвращает 403 для пользователя, который не автор комментария."""
        comment = comment_factory()
        url = reverse(
            "posts:comment_delete",
            kwargs={
                "post_pk": comment.post.pk,
                "post_slug": comment.post.slug,
                "comment_pk": comment.pk,
            },
        )

        client.force_login(user_factory())
        assert client.post(url, HTTP_HX_REQUEST="true").status_code == 403

    def test_moderator_can_delete_foreign_comment(
        self, client, user_factory, comment_factory, mocker
    ):
        """Модератор с правом posts.moderate_comment может удалить чужой комментарий."""
        moderator = user_factory(role=User.Role.MODERATOR)
        comment = comment_factory()
        client.force_login(moderator)
        url = reverse(
            "posts:comment_delete",
            kwargs={
                "post_pk": comment.post.pk,
                "post_slug": comment.post.slug,
                "comment_pk": comment.pk,
            },
        )
        mock_log = mocker.patch("posts.views.comment_views.log_comment_event")

        response = client.post(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        assert not Comment.objects.filter(pk=comment.pk).exists()
        mock_log.assert_called_once_with("comment_delete", mocker.ANY, moderator, source="web")
        trigger = json.loads(response["HX-Trigger"])
        assert "commentsUpdated" in trigger

    def test_successful_delete(self, client, comment_factory, mocker):
        """
        Автор успешно удаляет комментарий, вызывается логгер,
        срабатывает htmx триггер обновления комментариев.
        """
        comment = comment_factory()
        client.force_login(comment.author)
        mock_log = mocker.patch("posts.views.comment_views.log_comment_event")

        url = reverse(
            "posts:comment_delete",
            kwargs={
                "post_pk": comment.post.pk,
                "post_slug": comment.post.slug,
                "comment_pk": comment.pk,
            },
        )
        response = client.post(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        assert not Comment.objects.filter(pk=comment.pk).exists()

        mock_log.assert_called_once_with("comment_delete", mocker.ANY, comment.author, source="web")

        trigger = json.loads(response["HX-Trigger"])
        assert "commentsUpdated" in trigger
