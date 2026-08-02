import json

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestToggleLikePostView:
    def test_unauthenticated_htmx_request(self, client, post_factory):
        """Неавторизованный HTMX-запрос перехватывается миксином и возвращает сообщение."""
        post = post_factory()
        url = reverse("posts:toggle_like_post", kwargs={"post_pk": post.pk, "post_slug": post.slug})
        response = client.post(url, HTTP_HX_REQUEST="true")

        # LoginRequiredHTMXMixin возвращает сообщение вместо редиректа
        assert response.status_code == 200

        trigger = json.loads(response["HX-Trigger"])
        assert "showMessage" in trigger
        assert trigger["showMessage"]["text"] == "Сначала войдите в аккаунт."
        assert trigger["showMessage"]["type"] == "info"

    def test_post_not_found_returns_404_with_trigger(self, client, user_factory):
        """Запрос к несуществующему посту возвращает 404 и htmx триггер reloadPage."""
        client.force_login(user_factory())
        url = reverse("posts:toggle_like_post", kwargs={"post_pk": 9999, "post_slug": "not-found"})
        response = client.post(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 404
        trigger = json.loads(response["HX-Trigger"])
        assert trigger.get("reloadPage") is True

    def test_toggle_like_add_success(self, client, user_factory, post_factory, mocker):
        """
        Успешное добавление лайка возвращает success-сообщение и рендерит кнопку с новыми данными.
        """
        user = user_factory()
        client.force_login(user)
        post = post_factory(likes_count=10)

        # Не мокается posts.services.perform_toggle_like, чтобы лайк создался и
        # обновилось число лайков у связанного объекта.

        url = reverse("posts:toggle_like_post", kwargs={"post_pk": post.pk, "post_slug": post.slug})
        response = client.post(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        assert response.templates[0].name == "posts/likes/_like-button.html"

        # Проверка контекста, переданного в шаблон
        assert response.context["user_has_liked"] is True
        assert response.context["likes_count"] == 11
        assert response.context["liked_object"] == post
        assert "toggle_like_url" in response.context

        # Проверка HTMX триггера
        trigger = json.loads(response["HX-Trigger"])
        assert "showMessage" in trigger
        assert trigger["showMessage"]["type"] == "success"
        assert trigger["showMessage"]["text"] == "Лайк добавлен."

    def test_toggle_like_remove_success(self, client, user_factory, post_factory, mocker):
        """
        Успешное удаление лайка возвращает info-сообщение и и рендерит кнопку с новыми данными.
        """
        user = user_factory()
        client.force_login(user)
        post = post_factory(likes_count=4)

        # Создается лайк поста пользователем, сейчас 4 + 1 = 5 лайков
        post.likes.create(user=user)

        # Не мокается posts.services.perform_toggle_like, чтобы лайк удалился и
        # обновилось число лайков у связанного объекта.

        url = reverse("posts:toggle_like_post", kwargs={"post_pk": post.pk, "post_slug": post.slug})
        response = client.post(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 200

        # Проверка контекста, переданного в шаблон
        assert response.context["user_has_liked"] is False
        assert response.context["likes_count"] == 4
        assert response.context["liked_object"] == post
        assert "toggle_like_url" in response.context

        trigger = json.loads(response["HX-Trigger"])
        assert "showMessage" in trigger
        assert trigger["showMessage"]["type"] == "info"
        assert trigger["showMessage"]["text"] == "Лайк удален."


@pytest.mark.django_db
class TestToggleLikeCommentView:
    def test_unauthenticated_htmx_request(self, client, comment_factory):
        """Неавторизованный HTMX-запрос перехватывается миксином и возвращает сообщение."""
        comment = comment_factory()
        url = reverse(
            "posts:toggle_like_comment",
            kwargs={
                "post_pk": comment.post.pk,
                "post_slug": comment.post.slug,
                "comment_pk": comment.pk,
            },
        )
        response = client.post(url, HTTP_HX_REQUEST="true")

        # LoginRequiredHTMXMixin возвращает сообщение вместо редиректа
        assert response.status_code == 200

        trigger = json.loads(response["HX-Trigger"])
        assert "showMessage" in trigger
        assert trigger["showMessage"]["text"] == "Сначала войдите в аккаунт."
        assert trigger["showMessage"]["type"] == "info"

    def test_comment_not_found_returns_404_with_trigger(self, client, user_factory, post_factory):
        """Запрос к несуществующему комментарию возвращает 404 и htmx триггер reloadPage."""
        client.force_login(user_factory())
        post = post_factory()
        url = reverse(
            "posts:toggle_like_comment",
            kwargs={"post_pk": post.pk, "post_slug": post.slug, "comment_pk": 9999},
        )
        response = client.post(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 404
        trigger = json.loads(response["HX-Trigger"])
        assert trigger.get("reloadPage") is True

    def test_toggle_like_add_success(self, client, user_factory, comment_factory):
        """
        Успешное добавление лайка возвращает success-сообщение и рендерит кнопку с новыми данными.
        """
        user = user_factory()
        client.force_login(user)
        comment = comment_factory(likes_count=10)

        # Не мокается posts.services.perform_toggle_like, чтобы лайк создался и
        # обновилось число лайков у связанного объекта.

        url = reverse(
            "posts:toggle_like_comment",
            kwargs={
                "post_pk": comment.post.pk,
                "post_slug": comment.post.slug,
                "comment_pk": comment.pk,
            },
        )
        response = client.post(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        assert response.templates[0].name == "posts/likes/_like-button.html"

        # Проверка контекста, переданного в шаблон
        assert response.context["user_has_liked"] is True
        assert response.context["likes_count"] == 11
        assert response.context["liked_object"] == comment
        assert "toggle_like_url" in response.context

        # Проверка HTMX триггера
        trigger = json.loads(response["HX-Trigger"])
        assert "showMessage" in trigger
        assert trigger["showMessage"]["type"] == "success"
        assert trigger["showMessage"]["text"] == "Лайк добавлен."

    def test_toggle_like_remove_success(self, client, user_factory, comment_factory):
        """
        Успешное удаление лайка возвращает info-сообщение и рендерит кнопку с новыми данными.
        """
        user = user_factory()
        client.force_login(user)
        comment = comment_factory(likes_count=4)

        # Создается лайк комментария пользователем, сейчас 4 + 1 = 5 лайков
        comment.likes.create(user=user)

        # Не мокается posts.services.perform_toggle_like, чтобы лайк удалился и
        # обновилось число лайков у связанного объекта.

        url = reverse(
            "posts:toggle_like_comment",
            kwargs={
                "post_pk": comment.post.pk,
                "post_slug": comment.post.slug,
                "comment_pk": comment.pk,
            },
        )
        response = client.post(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 200

        # Проверка контекста, переданного в шаблон
        assert response.context["user_has_liked"] is False
        assert response.context["likes_count"] == 4
        assert response.context["liked_object"] == comment
        assert "toggle_like_url" in response.context

        trigger = json.loads(response["HX-Trigger"])
        assert "showMessage" in trigger
        assert trigger["showMessage"]["type"] == "info"
        assert trigger["showMessage"]["text"] == "Лайк удален."
