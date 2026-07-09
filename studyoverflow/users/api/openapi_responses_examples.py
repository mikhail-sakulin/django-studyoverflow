from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from users.api.serializers import DetailSerializer


LOGIN_REQUEST_EXAMPLES = [
    OpenApiExample(
        name="Вход по username",
        value={"username": "example_username", "password": "password123"},
        request_only=True,
    ),
    OpenApiExample(
        name="Вход по email",
        value={"username": "user@example.com", "password": "password123"},
        request_only=True,
    ),
]


OpenApiLoginFailed401Response = OpenApiResponse(
    description="Ошибка аутентификации" "(неверные данные или аккаунт заблокирован).",
    response=DetailSerializer,
    examples=[
        OpenApiExample(
            name="Неверные учетные данные",
            value={"detail": "Неверные учетные данные."},
            response_only=True,
        ),
        OpenApiExample(
            name="Аккаунт заблокирован",
            value={"detail": "Ваш аккаунт заблокирован."},
            response_only=True,
        ),
    ],
)


OpenApiUnauthenticated401Response = OpenApiResponse(
    response=DetailSerializer,
    description="Пользователь не аутентифицирован никаким из способов. "
    "Требуется передать токен или сессию.",
    examples=[
        OpenApiExample(
            name="Учетные данные не были предоставлены.",
            value={"detail": "Учетные данные не были предоставлены."},
            response_only=True,
        ),
        OpenApiExample(
            name="JWT access токен истек.",
            value={
                "detail": "Given token not valid for any token type",
                "code": "token_not_valid",
                "messages": [
                    {
                        "token_class": "AccessToken",
                        "token_type": "access",
                        "message": "Token is expired",
                    }
                ],
            },
            response_only=True,
        ),
    ],
)


PASSWORD_NEW_ERRORS_EXAMPLES = [
    OpenApiExample(
        name="Короткий пароль.",
        value={
            "password_new": [
                "Этот пароль слишком короткий. Он должен содержать не менее 8 символов."
            ]
        },
        response_only=True,
    ),
    OpenApiExample(
        name="Несовпадение паролей.",
        value={"password_new_confirm": ["Пароли не совпадают."]},
        response_only=True,
    ),
]


UserNotFoundOpenApiResponse = OpenApiResponse(
    description="Пользователь с указанным username не найден.",
    response=DetailSerializer,
    examples=[
        OpenApiExample(
            name="Пользователь не найден.",
            value={"detail": "No User matches the given query."},
            response_only=True,
        )
    ],
)
