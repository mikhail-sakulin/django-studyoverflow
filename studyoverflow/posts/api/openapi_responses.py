from drf_spectacular.utils import OpenApiExample, OpenApiResponse, inline_serializer
from rest_framework import serializers

from posts.api.serializers import DetailSerializer


def create_new_not_found_response(model_name: str = '"Object"') -> OpenApiResponse:
    return OpenApiResponse(
        description=f"{model_name} с указанным id не найден.",
        response=DetailSerializer,
        examples=[
            OpenApiExample(
                name=f"{model_name} не найден.",
                value={"detail": f"No {model_name} matches the given query."},
                response_only=True,
            )
        ],
    )


PaginationErrorOpenApiResponse = OpenApiResponse(
    description="Указана неверная страница (количество объектов недостаточно, "
    "или указано число меньше единицы).",
    response=inline_serializer(
        name="PageIncorrectSerializer",
        fields={"detail": serializers.CharField(default="Неправильная страница")},
    ),
)


PermissionDeniedOpenApiResponse = OpenApiResponse(
    description="Недостаточно прав для выполнения данного действия.",
    response=DetailSerializer,
    examples=[
        OpenApiExample(
            name="Недостаточно прав для выполнения данного действия.",
            value={"detail": "У вас недостаточно прав для выполнения данного действия."},
            response_only=True,
        )
    ],
)


PostFieldErrorValidationOpenApiResponse = OpenApiResponse(
    description="Ошибки валидации данных поста.",
    response=inline_serializer(
        name="PostFieldValidationErrorSerializer",
        fields={"field": serializers.ListField(child=serializers.CharField())},
    ),
    examples=[
        OpenApiExample(
            name="Длина заголовка должна быть не менее 10 символов.",
            value={
                "title": ["Длина заголовка должна быть не менее 10 символов."],
            },
            response_only=True,
        ),
        OpenApiExample(
            name="У поста должен быть хотя бы 1 тег.",
            value={
                "tags": ["Укажите хотя бы 1 тег."],
            },
            response_only=True,
        ),
    ],
)


CommentFieldErrorValidationOpenApiResponse = OpenApiResponse(
    description="Ошибки валидации данных комментария.",
    response=inline_serializer(
        name="CommentFieldValidationErrorSerializer",
        fields={"field": serializers.ListField(child=serializers.CharField())},
    ),
    examples=[
        OpenApiExample(
            name="Пустой комментарий.",
            value={
                "content": ["Это поле не может быть пустым."],
            },
            response_only=True,
        ),
        OpenApiExample(
            name="Пустой комментарий.",
            value={"content": ["Длина комментария не должна превышать 5000 символов."]},
            response_only=True,
        ),
        OpenApiExample(
            name="Недопустимый родительский комментарий.",
            value={
                "parent_comment": [
                    'Недопустимый первичный ключ "comment_id" - объект не существует.'
                ],
            },
            response_only=True,
        ),
    ],
)
