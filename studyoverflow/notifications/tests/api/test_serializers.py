from types import SimpleNamespace

import pytest
from rest_framework.exceptions import ValidationError

from notifications.api.serializers import NotificationSerializer
from posts.models import Like


class TestNotificationSerializer:
    def test_get_content_object_url_without_request(self):
        """
        Если request не передан в context, возвращается относительный путь
        из метода get_absolute_url целевого объекта.
        """
        target = SimpleNamespace(get_absolute_url=lambda: "/target/123/")
        notification = SimpleNamespace(content_object=target)

        serializer = NotificationSerializer()

        assert serializer.get_content_object_url(notification) == "/target/123/"

    def test_get_content_object_url_with_request(self, mocker):
        """
        Если request передан, возвращается абсолютный URL с доменом,
        сформированный через build_absolute_uri.
        """
        target = SimpleNamespace(get_absolute_url=lambda: "/target/123/")
        notification = SimpleNamespace(content_object=target)

        mock_request = mocker.Mock()
        mock_request.build_absolute_uri.return_value = "https://example.com/target/123/"

        serializer = NotificationSerializer(context={"request": mock_request})

        assert serializer.get_content_object_url(notification) == "https://example.com/target/123/"

    @pytest.mark.django_db
    def test_get_content_object_url_for_like_object(self, post_factory, user_factory):
        """
        Если целевой объект - это Like, то URL формируется для объекта,
        к которому этот Like относится (объект из content_object лайка).
        """
        post_target = post_factory()

        user = user_factory()

        like = Like.objects.create(user=user, content_object=post_target)

        notification = SimpleNamespace(content_object=like)
        serializer = NotificationSerializer()

        assert serializer.get_content_object_url(notification) == post_target.get_absolute_url()

    def test_get_content_object_url_returns_none(self):
        """
        Если целевой объект отсутствует, удален или не имеет метода get_absolute_url,
        возвращается None.
        """
        serializer = NotificationSerializer()

        # 1) content_object == None
        notification_no_target = SimpleNamespace(content_object=None)
        assert serializer.get_content_object_url(notification_no_target) is None

        # 2) content_object не имеет get_absolute_url
        notification_no_url_method = SimpleNamespace(content_object=SimpleNamespace())
        assert serializer.get_content_object_url(notification_no_url_method) is None

    def test_validate_is_read(self):
        """
        Поле is_read можно изменить только на True. Передача False вызывает ValidationError.
        """
        serializer = NotificationSerializer()

        # 1) True разрешено
        assert serializer.validate_is_read(True) is True

        # 2) False запрещено
        with pytest.raises(ValidationError) as exc:
            serializer.validate_is_read(False)

        assert "Вернуть is_read на False нельзя" in str(exc.value)
