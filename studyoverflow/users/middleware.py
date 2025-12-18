from django_redis import get_redis_connection
from users.services.infrastructure import set_user_online


class OnlineStatusMiddleware:
    """
    Middleware обновляет статус "online" пользователя в Redis при каждом HTTP-запросе.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.redis = get_redis_connection("default")

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            set_user_online(request.user.id)

        return response
