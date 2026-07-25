from drf_spectacular.utils import OpenApiExample, OpenApiResponse

from notifications.api.serializers import DetailSerializer


NotificationNotFoundOpenApiResponse = OpenApiResponse(
    description="Уведомление с указанным id для текущего пользователя не найдено.",
    response=DetailSerializer,
    examples=[
        OpenApiExample(
            name="Уведомление не найдено.",
            value={"detail": "No Notification matches the given query."},
            response_only=True,
        )
    ],
)
