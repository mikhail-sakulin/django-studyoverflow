import logging

from allauth.account.signals import user_signed_up
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.vk.views import VKOAuth2Adapter
from allauth.socialaccount.providers.yandex.views import YandexOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.serializers import JWTSerializer
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.db import transaction
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
    TokenVerifySerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from posts.api.openapi_responses import PaginationErrorOpenApiResponse
from users.api.openapi_responses_examples import (
    LOGIN_REQUEST_EXAMPLES,
    PASSWORD_NEW_ERRORS_EXAMPLES,
    OpenApiLoginFailed401Response,
    OpenApiUnauthenticated401Response,
    UserNotFoundOpenApiResponse,
)
from users.api.permissions import CanBlockUserPermission, UserPasswordNotSocialPermission
from users.api.serializers import (
    DetailSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RefreshJWTBlacklistSerializer,
    UserBlockResponseSerializer,
    UserListSerializer,
    UserMyProfileSerializer,
    UserPasswordChangeSerializer,
    UserPublicProfileSerializer,
    UserRegisterSerializer,
)
from users.mixins import UserOnlineFilterMixin, UserSortMixin
from users.services import block_user_service, unblock_user_service
from users.tasks import send_password_reset_email_task


User = get_user_model()

logger = logging.getLogger(__name__)


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet для управления аутентификацией.

    Обеспечивает вход (login), выход (logout), регистрацию пользователей,
    смену и восстановление пароля.
    Поддерживает 3 вида аутентификации:
    - сессия;
    - DRF токен;
    - JWT токен.
    """

    serializer_class = UserMyProfileSerializer

    def get_serializer_class(self):
        """
        Выбор сериализатора в зависимости от действия.
        """
        serializers = {
            "session_login": UserMyProfileSerializer,
            "drf_token_login": UserMyProfileSerializer,
            "register": UserRegisterSerializer,
            "password_change": UserPasswordChangeSerializer,
            "password_reset": PasswordResetRequestSerializer,
            "password_reset_confirm": PasswordResetConfirmSerializer,
        }

        return serializers.get(self.action, self.serializer_class)

    @extend_schema(
        summary="Аутентификация для создания сессии.",
        auth=[],
        request=LoginSerializer,
        examples=LOGIN_REQUEST_EXAMPLES,
        responses={
            200: UserMyProfileSerializer,
            401: OpenApiLoginFailed401Response,
        },
    )
    @action(detail=False, methods=["post"], url_path="session-login")
    def session_login(self, request):
        """
        Аутентификация для создания сессии.
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        return Response({"detail": "Неверные учетные данные."}, status=status.HTTP_401_UNAUTHORIZED)

    @extend_schema(
        summary="Удаление сессии.",
        request=None,
        responses={
            200: OpenApiResponse(
                response=DetailSerializer, description="Успешный выход. Сессия удалена."
            ),
            400: OpenApiResponse(
                response=DetailSerializer, description="У пользователя не было активной сессии."
            ),
            401: OpenApiUnauthenticated401Response,
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="session-logout",
    )
    def session_logout(self, request):
        """
        Удаление сессии.
        """
        if not request.session.session_key:
            return Response(
                {"detail": "У вас нет активной сессии."}, status=status.HTTP_400_BAD_REQUEST
            )

        logout(request)
        return Response({"detail": "Сессия удалена."}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Аутентификация для создания DRF token.",
        auth=[],
        request=LoginSerializer,
        examples=LOGIN_REQUEST_EXAMPLES,
        responses={
            200: OpenApiResponse(
                description="Успешный вход. Возвращает токен и данные профиля.",
                response=inline_serializer(
                    name="DrfTokenLoginSerializer",
                    fields={
                        "drf_token": serializers.CharField(),
                        "user": UserMyProfileSerializer(),
                    },
                ),
            ),
            401: OpenApiLoginFailed401Response,
        },
    )
    @action(detail=False, methods=["post"], url_path="drf-token-login")
    def drf_token_login(self, request):
        """
        Аутентификация для создания DRF token.
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=username, password=password)

        if user:
            token, created = Token.objects.get_or_create(user=user)

            serializer = self.get_serializer(user)

            return Response(
                {"drf_token": token.key, "user": serializer.data}, status=status.HTTP_200_OK
            )

        return Response({"detail": "Неверные учетные данные."}, status=status.HTTP_401_UNAUTHORIZED)

    @extend_schema(
        summary="Удаление DRF token.",
        request=None,
        responses={
            200: OpenApiResponse(
                response=DetailSerializer, description="Успешный выход. DRF токен удален."
            ),
            400: OpenApiResponse(
                response=DetailSerializer,
                description="У пользователя не было активного DRF токена.",
            ),
            401: OpenApiUnauthenticated401Response,
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="drf-token-logout",
    )
    def drf_token_logout(self, request):
        """
        Удаление DRF token.
        """
        token = getattr(request.user, "auth_token", None)

        if token:
            token.delete()

            return Response({"detail": "DRF token удален."}, status=status.HTTP_200_OK)

        return Response({"detail": "Нет активного DRF token."}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Блокирует JWT refresh токен (blacklist).",
        request=RefreshJWTBlacklistSerializer,
        responses={
            200: OpenApiResponse(
                response=DetailSerializer, description="JWT refresh токен теперь заблокирован."
            ),
            400: OpenApiResponse(
                response=DetailSerializer,
                description="Не передан или передан невалидный refresh токен.",
            ),
            401: OpenApiUnauthenticated401Response,
            500: OpenApiResponse(
                response=DetailSerializer, description="Ошибка обработки JWT refresh токена."
            ),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="jwt-token-logout",
    )
    def jwt_token_logout(self, request):
        """
        Блокирует JWT refresh токен текущего клиента (помещает его в blacklist).
        """
        refresh = request.data.get("refresh")

        if not refresh:
            return Response(
                {"detail": "Не передан refresh токен."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh)
            token.blacklist()
            return Response(
                {"detail": "JWT refresh токен теперь заблокирован."}, status=status.HTTP_200_OK
            )

        except TokenError:
            return Response(
                {"detail": "Передан неверный или просроченный JWT refresh токен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as error:
            logger.error(
                f"Ошибка обработки JWT refresh токена: {error}.",
                extra={"error": str(error), "refresh_token": refresh},
            )
            return Response(
                {"detail": "Ошибка обработки JWT refresh токена."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Удаляет токены пользователя и сессию для текущего клиента.",
        request=RefreshJWTBlacklistSerializer,
        responses={
            200: OpenApiResponse(
                response=DetailSerializer,
                description="Удаление всех токенов и сессии для текущего клиента.",
            ),
            400: OpenApiResponse(
                response=DetailSerializer,
                description="Передан неверный или просроченный refresh токен.",
            ),
            401: OpenApiUnauthenticated401Response,
            500: OpenApiResponse(
                response=DetailSerializer, description="Ошибка обработки JWT refresh токена."
            ),
        },
    )
    @action(
        detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path="logout-all"
    )
    def logout_all_methods(self, request):
        """
        Выход из системы текущего клиента,
        удаляет токены пользователя и сессию для текущего клиента.
        """
        # Удаление DRF токена, строго перед logout,
        # чтобы у request был объект user (не AnonymousUser)
        Token.objects.filter(user=request.user).delete()

        # Удаление текущей сессии
        logout(request)

        # Блокировка переданного JWT refresh токена
        refresh = request.data.get("refresh")

        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()

            except TokenError:
                return Response(
                    {"detail": "Передан неверный или просроченный JWT refresh токен."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            except Exception as error:
                logger.error(
                    f"Ошибка обработки JWT refresh токена: {error}.",
                    extra={"error": str(error), "refresh_token": refresh},
                )
                return Response(
                    {"detail": "Ошибка обработки JWT refresh токена."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(
            {
                "detail": "Вы успешно вышли из системы,"
                "все сессии и токены для текущего устройства удалены."
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        auth=[],
        summary="Регистрация нового пользователя.",
        request=UserRegisterSerializer,
        responses={
            201: OpenApiResponse(
                description="Новый пользователь создан.",
                response=UserMyProfileSerializer,
            ),
            400: OpenApiResponse(
                description="Ошибка валидации данных: несовпадение паролей,"
                "занятый username или email, слабый пароль и так далее.",
                response=inline_serializer(
                    name="RegistryErrorSerializer",
                    fields={"field": serializers.ListField(child=serializers.CharField())},
                ),
                examples=[
                    OpenApiExample(
                        name="Пользователь с таким именем уже существует.",
                        value={"username": ["Пользователь с таким именем уже существует."]},
                        response_only=True,
                    ),
                    OpenApiExample(
                        name="Несовпадение паролей.",
                        value={"password_confirm": ["Пароли не совпадают."]},
                        response_only=True,
                    ),
                    OpenApiExample(
                        name="Короткий пароль.",
                        value={
                            "password": [
                                "Этот пароль слишком короткий. Он должен содержать "
                                "не менее 8 символов."
                            ]
                        },
                        response_only=True,
                    ),
                ],
            ),
        },
    )
    @action(detail=False, methods=["post"])
    def register(self, request):
        """
        Регистрация пользователя.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        user_signed_up.send(sender=User, request=request, user=user)

        return Response(
            UserMyProfileSerializer(user, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Смена пароля.",
        request=UserPasswordChangeSerializer,
        responses={
            200: OpenApiResponse(
                description="Пароль успешно изменен.",
                response=inline_serializer(
                    name="PasswordChangeSuccessSerializer",
                    fields={
                        "detail": serializers.CharField(default="Пароль успешно изменен."),
                    },
                ),
            ),
            400: OpenApiResponse(
                description="Ошибки валидации пароля: несовпадение паролей, "
                "слабый пароль и так далее.",
                response=inline_serializer(
                    name="RegistryErrorResponse",
                    fields={"field": serializers.ListField(child=serializers.CharField())},
                ),
                examples=[
                    OpenApiExample(
                        name="Текущий пароль введен неверно.",
                        value={"password_old": ["Текущий пароль введен неверно."]},
                        response_only=True,
                    ),
                    *PASSWORD_NEW_ERRORS_EXAMPLES,
                ],
            ),
            401: OpenApiUnauthenticated401Response,
            403: OpenApiResponse(
                description="Пользователи, аутентифицированные через социальные сети (OAuth), "
                "не могут изменять пароль.",
                response=inline_serializer(
                    name="SocialUserForbiddenSerializer",
                    fields={
                        "detail": serializers.CharField(
                            default="Пользователи, зарегистрированные через социальные сети, "
                            "не могут изменять пароль."
                        )
                    },
                ),
            ),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, UserPasswordNotSocialPermission],
        url_path="password-change",
    )
    def password_change(self, request):
        """
        Смена пароля текущего авторизованного пользователя.
        """
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        # Обновление сессии, чтобы пользователя не разлогинило из системы после смены пароля
        update_session_auth_hash(request, user)

        logger.info(
            f"Пользователь {user.username} успешно сменил пароль.",
            extra={
                "username": user.username,
                "user_id": user.id,
                "event_type": "user_password_change_success",
                "source": getattr(self.request, "source_for_logging", "api"),
            },
        )

        return Response({"detail": "Пароль успешно изменен."}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Запрос на восстановление пароля.",
        auth=[],
        request=PasswordResetRequestSerializer,
        responses={
            200: OpenApiResponse(
                description="Письмо отправлено, если email существует.",
                response=inline_serializer(
                    name="PasswordResetSuccessSerializer",
                    fields={
                        "detail": serializers.CharField(
                            default="Если введенный email зарегистрирован в системе, "
                            "на него отправлена инструкция по восстановлению пароля."
                        )
                    },
                ),
            ),
            400: OpenApiResponse(
                description="Неверный формат email.",
                response=inline_serializer(
                    name="PasswordResetValidationErrorSerializer",
                    fields={
                        "email": serializers.ListField(
                            child=serializers.CharField(
                                default="Введите правильный адрес электронной почты."
                            )
                        )
                    },
                ),
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="password-reset")
    def password_reset(self, request):
        """
        Запрос на восстановление пароля (отправка письма).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        domain = request.get_host()
        use_https = request.is_secure()

        # отправка письма после подтверждения транзакции
        transaction.on_commit(
            lambda: send_password_reset_email_task.delay(
                email=email,
                domain=domain,
                use_https=use_https,
            )
        )

        return Response(
            {
                "detail": "Если введенный email зарегистрирован в системе, "
                "на него отправлена инструкция по восстановлению пароля."
            }
        )

    @extend_schema(
        summary="Сброс пароля, установка нового пароля после получения email.",
        auth=[],
        request=PasswordResetConfirmSerializer,
        responses={
            200: OpenApiResponse(
                description="Пароль успешно изменен.",
                response=inline_serializer(
                    name="PasswordResetConfirmSuccess",
                    fields={"detail": serializers.CharField(default="Пароль успешно изменен.")},
                ),
            ),
            400: OpenApiResponse(
                description="Ошибки валидации пароля, uidb64 и токена.",
                response=inline_serializer(
                    name="PasswordResetConfirmValidationErrorSerializer",
                    fields={"field": serializers.ListField(child=serializers.CharField())},
                ),
                examples=[
                    OpenApiExample(
                        name="Неверный идентификатор пользователя.",
                        value={"uidb64": ["Неверный идентификатор пользователя."]},
                        response_only=True,
                    ),
                    OpenApiExample(
                        name="Ссылка устарела или неверна.",
                        value={"token": ["Ссылка устарела или неверна."]},
                        response_only=True,
                    ),
                    *PASSWORD_NEW_ERRORS_EXAMPLES,
                    OpenApiExample(
                        name="Смена пароля при OAuth запрещена.",
                        value={
                            "detail": [
                                "Пользователи, зарегистрированные через социальные сети, "
                                "не могут изменять пароль."
                            ]
                        },
                        response_only=True,
                    ),
                ],
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="password-reset-confirm")
    def password_reset_confirm(self, request):
        """
        Установка нового пароля по токену.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        logger.info(
            f"Пользователь {user.username} успешно восстановил пароль через email.",
            extra={
                "username": user.username,
                "user_id": user.pk,
                "event_type": "password_reset_success",
                "source": getattr(self.request, "source_for_logging", "api"),
            },
        )

        return Response({"detail": "Пароль успешно изменен."})


@extend_schema_view(
    post=extend_schema(
        auth=[],
        request=LoginSerializer,
        examples=LOGIN_REQUEST_EXAMPLES,
        summary="Аутентификация для создания JWT-токенов: access и refresh.",
        responses={
            200: TokenObtainPairSerializer,
            401: OpenApiLoginFailed401Response,
        },
    )
)
class CustomTokenObtainPairView(TokenObtainPairView):
    pass


@extend_schema_view(
    post=extend_schema(
        summary="Обновление JWT access-токена через refresh токен.",
        auth=[],
        responses={
            200: TokenRefreshSerializer,
            401: OpenApiResponse(
                description="Прислан невалидный refresh токен.",
                response=inline_serializer(
                    name="TokenVerifyErrorSerializer",
                    fields={
                        "detail": serializers.CharField(default="Token is invalid or expired"),
                        "code": serializers.CharField(default="token_not_valid"),
                    },
                ),
            ),
        },
    )
)
class CustomTokenRefreshView(TokenRefreshView):
    pass


@extend_schema_view(
    post=extend_schema(
        summary="Проверка JWT-токена.",
        auth=[],
        responses={
            200: TokenVerifySerializer,
            400: OpenApiResponse(
                description='Обязательное поле "token".',
                response=inline_serializer(
                    name="TokenRequiredFieldErrorSerializer",
                    fields={
                        "token": serializers.ListField(
                            child=serializers.CharField(default="Обязательное поле.")
                        )
                    },
                ),
            ),
            401: OpenApiResponse(
                description="Прислан невалидный JWT токен.",
                response=inline_serializer(
                    name="TokenVerifyErrorSerializer",
                    fields={
                        "detail": serializers.CharField(default="Token is invalid"),
                        "code": serializers.CharField(default="token_not_valid"),
                    },
                ),
            ),
        },
    )
)
class CustomTokenVerifyView(TokenVerifyView):
    pass


def extend_social_login_schema(provider_name: str):
    """
    Фабрика декораторов для swagger для API эндпоинтов социальной аутентификации OAuth.
    """
    return extend_schema_view(
        post=extend_schema(
            summary=f"API OAuth аутентификация через {provider_name}.",
            description=(
                "Сейчас эндпоинт недоступен (выдаст 400 ответ), поскольку не реализован фронтенд "
                "для API, а у callback_url прописан url фронтенда (теоретического). "
                "Для тестирования этого OAuth эндпоинта нужно задать другой callback_url, "
                "который прописан в настройках приложения у соцсети (сейчас там прописан url "
                "от django-allauth стандартный для данной соцсети).\n\n"
                f"Принимает код авторизации ('code'), полученный пользователем от {provider_name}."
                " Через него и client_id и client_secret бекенд получает access_token от соцсети "
                "для получения данных пользователя. Если пользователь заходит впервые, "
                "создается аккаунт. При успешной аутентификации возвращаются JWT access и refresh "
                "токены и данные пользователя."
            ),
            auth=[],
            request=inline_serializer(
                name=f"{provider_name}CodeTokenSerializer",
                fields={
                    "code": serializers.CharField(),
                },
            ),
            responses={
                200: OpenApiResponse(
                    response=JWTSerializer,
                    description="Успешная аутентификация. Возвращаются JWT-токены access и refresh"
                    "и данные пользователя.",
                ),
                400: OpenApiResponse(
                    description="Ошибка валидации: код устарел, уже использован или "
                    "задан неверный callback_url.",
                    response=inline_serializer(
                        name=f"{provider_name}SocialLoginValidationErrorSerializer",
                        fields={
                            "non_field_errors": serializers.ListField(
                                child=serializers.CharField(
                                    default="Failed to exchange code for access token"
                                ),
                            )
                        },
                    ),
                ),
            },
        )
    )


@extend_social_login_schema("Google")
class GoogleLoginAPI(SocialLoginView):
    """
    API эндпоинт для аутентификации пользователя через OAuth через Google.

    Используется dj-rest-auth вместе с django-allauth (OAuth2.0) и simplejwt (JWT) библиотеками:
    - django-allauth - общение со сторонними сервисами (соцсети),
      отсюда используются классы-адаптеры и OAuth2Client для обмена кодами и запросом
      данных пользователя;
    - simplejwt - генерация JWT токенов при успешной аутентификации (если "USE_JWT": True);
    - dj-rest-auth - интеграция django-allauth с simplejwt для API, JSON-обертка.
    """

    # Класс-адаптер для конкретной соцсети (Google), "знает" необходимые google-эндпоинты
    # и формат, в котором Google передает данные пользователя.
    adapter_class = GoogleOAuth2Adapter

    # Стандартный клиент для реализации HTTP-запросов от бекенда к соцсети,
    # используется для отправки code, полученного от клиента, и client_id и client_secret
    # (для соцсети из .env) для получения access_token,
    # используется также для последующего получения данных пользователя от соцсети
    # через access_token.
    client_class = OAuth2Client

    # Редирект, который задается в соцсети при регистрации приложения (бекенда),
    # значения должны совпасть. На этот url соцсеть редиректит пользователя GET-запросом с code.
    # Сейчас задан url фронтенда, для тестирования без фронтенда
    # можно использовать url тест-эндпоинта бекенда, например
    # http://127.0.0.1:8000/api/v1/dev/google-callback/ для получения code из GET-параметров.
    callback_url = "http://localhost:3000/oauth-callback/google/"


@extend_social_login_schema("GitHub")
class GitHubLoginAPI(SocialLoginView):
    """
    API эндпоинт для аутентификации пользователя через OAuth через GitHub.

    Документация текущего класса аналогична документации класса GoogleLoginAPI.
    """

    adapter_class = GitHubOAuth2Adapter
    client_class = OAuth2Client
    callback_url = "http://localhost:3000/oauth-callback/github/"


@extend_social_login_schema("VK")
class VKLoginAPI(SocialLoginView):
    """
    API эндпоинт для аутентификации пользователя через OAuth через VKLoginAPI.

    Документация текущего класса аналогична документации класса GoogleLoginAPI.
    """

    adapter_class = VKOAuth2Adapter
    client_class = OAuth2Client
    callback_url = "http://localhost:3000/oauth-callback/vk/"


@extend_social_login_schema("Yandex")
class YandexLoginAPI(SocialLoginView):
    """
    API эндпоинт для аутентификации пользователя через OAuth через YandexLoginAPI.

    Документация текущего класса аналогична документации класса GoogleLoginAPI.
    """

    adapter_class = YandexOAuth2Adapter
    client_class = OAuth2Client
    callback_url = "http://localhost:3000/oauth-callback/yandex/"


@extend_schema_view(
    retrieve=extend_schema(
        summary="Просмотр профиля конкретного пользователя.",
        description="Возвращает профиль пользователя по его уникальному username. "
        "Если текущий авторизованный пользователь указывает свой username, "
        "то возвращаются его расширенные данные через другой сериализатор.",
        auth=[],
        responses={
            200: OpenApiResponse(
                description="Профиль пользователя успешно получен.",
                # Полиморфный прокси для отображения нескольких сериализаторов в Swagger
                response=PolymorphicProxySerializer(
                    component_name="UserProfileResponse",
                    serializers={
                        "public_profile": UserPublicProfileSerializer,
                        "my_profile": UserMyProfileSerializer,
                    },
                    resource_type_field_name=None,
                ),
            ),
            404: UserNotFoundOpenApiResponse,
        },
    )
)
class UserViewSet(
    UserSortMixin,
    UserOnlineFilterMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet для работы с данными пользователей.

    Реализует получение списка пользователей, просмотр профилей и управление
    личным аккаунтом (me). Поддерживает фильтрацию по статусу "онлайн",
    сортировку пользователей и загрузку медиафайлов (аватарок).
    Также реализует действия блокировки и разблокировки пользователей для модераторов.
    """

    queryset = User.objects.all()
    lookup_field = "username"
    parser_classes = [MultiPartParser, JSONParser]
    serializer_class = UserPublicProfileSerializer

    def get_queryset(self):
        """
        Переопределение для фильтрации и сортировки списка пользователей.
        """
        queryset = super().get_queryset()

        if self.action == "list":
            queryset = self.filter_by_online(queryset)
            queryset = self.apply_sorting(queryset)

        return queryset

    def get_serializer_class(self):
        """
        Выбор сериализатора в зависимости от действия.

        Использует подмену публичного профиля пользователя на личный при просмотре своего аккаунта.
        """
        serializers = {
            "list": UserListSerializer,
            "retrieve": UserPublicProfileSerializer,
            "me": UserMyProfileSerializer,
            "block": UserBlockResponseSerializer,
            "unblock": UserBlockResponseSerializer,
        }

        # Если пользователь хочет посмотреть свой профиль не через "/users/me/", а
        # через /users/<username>/, то используется UserMyProfileSerializer
        if self.action == "retrieve":
            if (
                self.request.user.is_authenticated
                and self.kwargs.get("username") == self.request.user.username
            ):
                return UserMyProfileSerializer

        return serializers.get(self.action, self.serializer_class)

    @extend_schema(
        summary="Список пользователей.",
        auth=[],
        responses={
            200: OpenApiResponse(
                description="Список пользователей успешно получен.",
                response=UserListSerializer(many=True),
            ),
            404: PaginationErrorOpenApiResponse,
        },
    )
    def list(self, request, *args, **kwargs):  # noqa: A003
        """
        Список пользователей.
        """
        online_ids = set(self.get_online_ids())

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        serializer = self.get_serializer(
            page,
            many=True,
            context={
                **self.get_serializer_context(),
                "online_ids": online_ids,
            },
        )

        return self.get_paginated_response(serializer.data)

    @extend_schema(
        methods=["get"],
        summary="Получение профиля текущего аутентифицированного пользователя.",
        responses={
            200: OpenApiResponse(
                description="Данные личного профиля текущего пользователя.",
                response=UserMyProfileSerializer,
            ),
            401: OpenApiUnauthenticated401Response,
        },
    )
    @extend_schema(
        methods=["patch"],
        summary="Частичное обновление профиля текущего пользователя.",
        request={"multipart/form-data": UserMyProfileSerializer},
        responses={
            200: OpenApiResponse(
                description="Профиль успешно обновлен.",
                response=UserMyProfileSerializer,
            ),
            400: OpenApiResponse(
                description="Ошибки валидации данных при обновлении профиля.",
                response=inline_serializer(
                    name="UserProfileUpdateErrorSerializer",
                    fields={"field": serializers.ListField(child=serializers.CharField())},
                ),
                examples=[
                    OpenApiExample(
                        name="Пользователь с таким email уже существует.",
                        value={
                            "email": [
                                "Пользователь с таким email (в любом регистре) уже существует."
                            ]
                        },
                        response_only=True,
                    ),
                    OpenApiExample(
                        name="Пользователь с таким именем уже существует.",
                        value={"username": ["Пользователь с таким именем уже существует."]},
                        response_only=True,
                    ),
                ],
            ),
            401: OpenApiUnauthenticated401Response,
        },
    )
    @extend_schema(
        methods=["delete"],
        summary="Удаление аккаунта текущего пользователя.",
        responses={
            204: OpenApiResponse(
                description="Аккаунт успешно удален, сессия удалена.",
            ),
            401: OpenApiUnauthenticated401Response,
        },
    )
    @action(detail=False, methods=["get", "patch", "delete"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Профиль текущего пользователя.
        """
        if request.method == "PATCH":
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        if request.method == "DELETE":
            user = request.user
            logout(request)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="Получение оригинального аватара (не миниатюра) пользователя.",
        auth=[],
        responses={
            200: OpenApiResponse(
                description="Адрес URL оригинального аватара.",
                response=inline_serializer(
                    name="UserAvatarFullSerializer",
                    fields={
                        "username": serializers.CharField(),
                        "full_avatar_url": serializers.URLField(),
                    },
                ),
            ),
            404: UserNotFoundOpenApiResponse,
        },
    )
    @action(detail=True, methods=["get"], url_path="avatar-full")
    def avatar_full(self, request, username=None):
        """
        Возвращает URL оригинального аватара пользователя.
        """
        user = self.get_object()

        if not user.avatar:
            return Response(
                {"detail": "У пользователя нет аватара."}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "username": user.username,
                "full_avatar_url": request.build_absolute_uri(user.avatar.url),
            }
        )

    @extend_schema(
        summary="Блокировка пользователя модератором.",
        request=None,
        responses={
            200: OpenApiResponse(
                description="Пользователь успешно заблокирован.",
                response=UserBlockResponseSerializer,
            ),
            400: OpenApiResponse(
                description="Пользователь уже заблокирован.",
                response=UserBlockResponseSerializer,
                examples=[
                    OpenApiExample(
                        name="Пользователь уже заблокирован.",
                        value={
                            "message": "Пользователь user_test уже заблокирован.",
                            "is_blocked": True,
                        },
                        response_only=True,
                    )
                ],
            ),
            401: OpenApiUnauthenticated401Response,
            403: OpenApiResponse(
                description="Недостаточно прав для блокировки: попытка заблокировать пользователя "
                "с равной или более высокой ролью или самого себя.",
                response=DetailSerializer,
                examples=[
                    OpenApiExample(
                        name="Недостаточно прав для блокировки.",
                        value={
                            "message": (
                                "Нельзя модерировать пользователя с равной или более "
                                "высокой ролью. / Нельзя модерировать самого себя."
                            ),
                        },
                        response_only=True,
                    )
                ],
            ),
            404: UserNotFoundOpenApiResponse,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, CanBlockUserPermission],
        url_path="block",
    )
    def block(self, request, username=None):
        """
        Блокирует пользователя при наличии у модератора на это прав.
        """
        target_user = self.get_object()
        source = getattr(request, "source_for_logging", "api")

        success, message = block_user_service(
            moderator=request.user, target_user=target_user, source=source
        )

        serializer = self.get_serializer({"message": message, "is_blocked": target_user.is_blocked})

        status_code = status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST
        return Response(serializer.data, status=status_code)

    @extend_schema(
        summary="Разблокировка пользователя модератором.",
        request=None,
        responses={
            200: OpenApiResponse(
                description="Пользователь успешно разблокирован.",
                response=UserBlockResponseSerializer,
            ),
            400: OpenApiResponse(
                description="Пользователь уже разблокирован.",
                response=UserBlockResponseSerializer,
                examples=[
                    OpenApiExample(
                        name="Пользователь уже разблокирован.",
                        value={
                            "message": "Пользователь user_test уже разблокирован.",
                            "is_blocked": False,
                        },
                        response_only=True,
                    )
                ],
            ),
            401: OpenApiUnauthenticated401Response,
            403: OpenApiResponse(
                description="Недостаточно прав для разблокировки: попытка разблокировать "
                "пользователя с равной или более высокой ролью или самого себя.",
                response=DetailSerializer,
                examples=[
                    OpenApiExample(
                        name="Недостаточно прав для разблокировки.",
                        value={
                            "message": (
                                "Нельзя модерировать пользователя с равной или более "
                                "высокой ролью. / "
                                "Нельзя модерировать самого себя."
                            ),
                        },
                        response_only=True,
                    )
                ],
            ),
            404: UserNotFoundOpenApiResponse,
        },
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, CanBlockUserPermission],
        url_path="unblock",
    )
    def unblock(self, request, username=None):
        """
        Разблокирует пользователя при наличии у модератора на это прав.
        """
        target_user = self.get_object()

        source = getattr(request, "source_for_logging", "api")

        success, message = unblock_user_service(
            moderator=request.user, target_user=target_user, source=source
        )

        serializer = self.get_serializer({"message": message, "is_blocked": target_user.is_blocked})

        status_code = status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST
        return Response(serializer.data, status=status_code)
