from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from notifications.api.openapi_responses import NotificationNotFoundOpenApiResponse
from notifications.api.serializers import DetailSerializer, NotificationSerializer
from notifications.mixins import NotificationOptimizeMixin
from notifications.models import Notification
from notifications.tasks import send_channel_notify_event
from users.api.openapi_responses_examples import OpenApiUnauthenticated401Response


@extend_schema_view(
    list=extend_schema(
        summary="Получить список уведомлений текущего аутентифицированного пользователя.",
        description=(
            "Возвращает список уведомлений для аутентифицированного пользователя.\n\n"
            "**Фильтрация (GET):**\n"
            "- `is_read`: Фильтр по статусу прочтения (`true` / `false`). Если параметр "
            "не передан, возвращаются все уведомления пользователя."
        ),
        parameters=[
            OpenApiParameter(
                name="is_read",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Фильтрация уведомлений по статусу прочтения (true - прочитанные, "
                "false - непрочитанные).",
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Список уведомлений успешно получен.",
                response=NotificationSerializer(many=True),
            ),
            401: OpenApiUnauthenticated401Response,
        },
    ),
    retrieve=extend_schema(
        summary="Просмотр конкретного уведомления пользователя.",
        description="Возвращает детальную информацию по конкретному уведомлению. Доступно "
        "только получателю уведомления, чужие просматривать нельзя (фильтрация по пользователю).",
        responses={
            200: OpenApiResponse(
                description="Детали уведомления успешно получены.", response=NotificationSerializer
            ),
            401: OpenApiUnauthenticated401Response,
            404: NotificationNotFoundOpenApiResponse,
        },
    ),
    destroy=extend_schema(
        summary="Удаление уведомления.",
        description="Удаляет уведомление. Доступно только получателю.",
        responses={
            204: OpenApiResponse(description="Уведомление успешно удалено."),
            401: OpenApiUnauthenticated401Response,
            404: NotificationNotFoundOpenApiResponse,
        },
    ),
)
class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    NotificationOptimizeMixin,
    viewsets.GenericViewSet,
):

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)

        # Сортировка по полю is_read, если задан соответствующий GET-параметр
        is_read_param = self.request.query_params.get("is_read")
        if is_read_param is not None:
            is_read = is_read_param.lower() in ["true", "1"]
            queryset = queryset.filter(is_read=is_read)

        return self.optimize_notification_queryset(queryset)

    @extend_schema(
        summary="Получить количество непрочитанных уведомлений текущего пользователя.",
        description="Возвращает число непрочитанных уведомлений текущего пользователя.",
        responses={
            200: OpenApiResponse(
                description="Количество непрочитанных уведомлений успешно получено.",
                response=inline_serializer(
                    name="NotificationUnreadCountSerializer",
                    fields={"unread_count": serializers.IntegerField()},
                ),
            ),
            401: OpenApiUnauthenticated401Response,
        },
    )
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        """Возвращает количество непрочитанных уведомлений."""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"unread_count": count})

    @extend_schema(
        summary="Отметить все уведомления как прочитанные.",
        request=None,
        responses={
            200: OpenApiResponse(
                description="Все уведомления отмечены как прочитанные.",
                response=DetailSerializer,
                examples=[
                    OpenApiExample(
                        name="Все уведомления прочитаны.",
                        value={"detail": "Все уведомления помечены прочитанными."},
                        response_only=True,
                    )
                ],
            ),
            401: OpenApiUnauthenticated401Response,
        },
    )
    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        """
        Помечает все непрочитанные уведомления пользователя прочитанными и создает
        Celery задачу для обновления счетчика непрочитанных уведомлений через Channels WebSocket.
        """
        self.get_queryset().filter(is_read=False).update(is_read=True)

        send_channel_notify_event.delay(user_id=request.user.pk, update_list=False)

        return Response({"detail": "Все уведомления помечены прочитанными."})

    @extend_schema(
        summary="Пометить конкретное уведомление как прочитанное.",
        description="Изменяет статус 'is_read' выбранного уведомления на True. Доступно только "
        "получателю уведомления.",
        request=None,
        responses={
            200: OpenApiResponse(
                description="Уведомление помечено как прочитанное.",
                response=DetailSerializer,
                examples=[
                    OpenApiExample(
                        name="Уведомление прочитано.",
                        value={"detail": "Уведомление изменено на прочитанное."},
                        response_only=True,
                    )
                ],
            ),
            401: OpenApiUnauthenticated401Response,
            404: NotificationNotFoundOpenApiResponse,
        },
    )
    @action(detail=True, methods=["patch"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        """Помечает одно уведомление прочитанным."""
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])
        return Response({"detail": "Уведомление изменено на прочитанное."})

    @extend_schema(
        summary="Удалить все уведомления.",
        description="Удаляет все уведомления текущего аутентифицированного пользователя.",
        responses={
            204: OpenApiResponse(description="Все уведомления успешно удалены."),
            401: OpenApiUnauthenticated401Response,
        },
    )
    @action(detail=False, methods=["delete"], url_path="delete-all")
    def delete_all(self, request):
        """Удаляет все уведомления пользователя"""
        self.get_queryset().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
