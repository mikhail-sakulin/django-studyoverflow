from allauth.account.signals import user_signed_up
from django.contrib.auth import authenticate, get_user_model, login, logout
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.api.serializers import (
    UserListSerializer,
    UserMyProfileSerializer,
    UserPublicProfileSerializer,
    UserRegisterSerializer,
)
from users.views.mixins import UserOnlineFilterMixin, UserSortMixin


User = get_user_model()


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet для управления аутентификацией.

    Обеспечивает вход (login), выход (logout) и регистрацию пользователей.
    Использует сессионную аутентификацию и отправляет сигнал allauth при регистрации.
    """

    @action(detail=False, methods=["post"])
    def login(self, request):
        """
        Логин через сессию.
        """
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request, username=username, password=password)

        if user and user.is_active:
            login(request, user)
            return Response(UserMyProfileSerializer(user, context={"request": request}).data)

        return Response({"detail": "Неверные учетные данные."}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Выход из системы, удаление сессии.
        """
        logout(request)
        return Response({"detail": "Вы успешно вышли из аккаунта."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def register(self, request):
        """
        Регистрация пользователя.
        """
        serializer = UserRegisterSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        user_signed_up.send(sender=User, request=request, user=user)

        return Response(
            UserMyProfileSerializer(user, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
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
    """

    queryset = User.objects.all()
    lookup_field = "username"
    parser_classes = [MultiPartParser, JSONParser]

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

        Испольует подмену публичного профиля пользователя на личный при просмотре своего аккаунта.
        """
        serializers = {
            "list": UserListSerializer,
            "retrieve": UserPublicProfileSerializer,
            "me": UserMyProfileSerializer,
        }

        # Если пользователь хочет посмотреть свой профиль не через "/users/me/", а
        # через /users/<username>/, то используется UserMyProfileSerializer
        if self.action == "retrieve":
            if (
                self.request.user.is_authenticated
                and self.kwargs.get("username") == self.request.user.username
            ):
                return UserMyProfileSerializer

        return serializers.get(self.action, UserPublicProfileSerializer)

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
