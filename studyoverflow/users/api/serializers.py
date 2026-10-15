from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core import exceptions
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from users.services.online import is_user_online
from users.services.validators import validate_email_unique


User = get_user_model()


class AvatarSerializer(serializers.Serializer):
    """
    Универсальный сериализатор для отображения всех вариантов аватара пользователя.

    Предоставляет ссылки на оригинал и сгенерированные миниатюры разного размера.
    Использует свойства модели User (avatar_small_sizeX_url), которые возвращают
    ссылку на оригинал, если миниатюры еще не сгенерированы Celery.
    """

    original = serializers.URLField(source="avatar.url")
    size1 = serializers.URLField(source="avatar_small_size1_url")
    size2 = serializers.URLField(source="avatar_small_size2_url")
    size3 = serializers.URLField(source="avatar_small_size3_url")


class UserPublicProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для публичного профиля пользователя.

    Предоставляет общую информацию, доступную всем посетителям, включая
    статус "онлайн" и ссылки на различные размеры аватара.
    """

    avatars = AvatarSerializer(source="*", read_only=True)
    online_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "online_status",
            "avatars",
            "first_name",
            "last_name",
            "bio",
            "reputation",
            "posts_count",
            "comments_count",
            "date_birth",
            "date_joined",
            "last_seen",
            "is_blocked",
        ]
        read_only_fields = fields
        extra_kwargs = {
            "is_blocked": {"default": False},
        }

    def get_online_status(self, user) -> bool:
        """Проверяет текущий статус активности пользователя в Redis."""
        return is_user_online(user.pk)


class UserMyProfileSerializer(UserPublicProfileSerializer):
    """
    Сериализатор для профиля текущего авторизованного пользователя.

    Расширяет публичный профиль приватными полями и возможностью загрузки аватара.
    """

    class Meta(UserPublicProfileSerializer.Meta):
        fields = UserPublicProfileSerializer.Meta.fields + ["is_social", "avatar"]
        extra_kwargs = {
            "is_blocked": {"default": False},
            "is_social": {"default": False},
            # "allow_null": True позволяет сбрасывать аватар на дефолтный при отправке null,
            # в самой модели задано дефолтное значение, а null=False.
            "avatar": {"write_only": True, "allow_null": True},
        }
        read_only_fields = [
            "id",
            "reputation",
            "posts_count",
            "comments_count",
            "date_joined",
            "last_seen",
            "is_social",
            "role",
            "is_blocked",
        ]

    def validate_username(self, value):
        """Проверка уникальности имени пользователя без учета регистра."""
        queryset = User.objects.filter(username__iexact=value)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Пользователь с таким именем (в любом регистре) уже существует."
            )
        return value

    def validate_email(self, value):
        """Проверка уникальности email без учета регистра."""
        if value:
            try:
                validate_email_unique(value, instance=self.instance)
            except exceptions.ValidationError as e:
                raise serializers.ValidationError(e.messages)
        return value

    def update(self, instance, validated_data):
        """Сохраняет только переданные поля, не перезаписывая поля-счётчики и поле last_seen."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=list(validated_data))
        return instance


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации новых пользователей.

    Включает валидацию пароля и username.
    """

    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password", "password_confirm")

    def validate_username(self, value):
        """Проверка уникальности имени пользователя без учета регистра."""
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким именем (в любом регистре) уже существует."
            )
        return value

    def validate_email(self, value):
        """Проверка уникальности email без учета регистра."""
        if value:
            try:
                validate_email_unique(value, instance=None)
            except exceptions.ValidationError as e:
                raise serializers.ValidationError(e.messages)
        return value

    def validate(self, attrs):
        """
        Валидация пароля и совпадения паролей.
        """
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Пароли не совпадают."})

        user_data = attrs.copy()
        user_data.pop("password_confirm", None)

        user = User(**user_data)
        password = attrs.get("password")
        try:
            validate_password(password, user)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        """Создание пользователя с использованием UserManager для хеширования пароля."""
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)


class UserListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткого отображения списка пользователей.
    """

    avatars = AvatarSerializer(source="*", read_only=True)
    online_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "role",
            "online_status",
            "avatars",
            "reputation",
            "posts_count",
            "comments_count",
            "last_seen",
        ]
        read_only_fields = fields

    def get_online_status(self, user) -> bool:
        """
        Определяет статус онлайн на основе множества ID, переданного
        в context сериализатора в UserViewSet.
        """
        return user.id in self.context["online_ids"]


class UserPasswordChangeSerializer(serializers.Serializer):
    """
    Сериализатор для смены пароля авторизованного пользователя.

    Проверяет корректность старого пароля и валидирует новый пароль.
    """

    password_old = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )
    password_new = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )
    password_new_confirm = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )

    def validate_password_old(self, value):
        """Проверка правильности введенного старого пароля."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль введен неверно.")
        return value

    def validate(self, attrs):
        """Валидация новых паролей и их совпадения."""
        if attrs["password_new"] != attrs["password_new_confirm"]:
            raise serializers.ValidationError({"password_new_confirm": "Пароли не совпадают."})

        user = self.context["request"].user
        try:
            validate_password(attrs["password_new"], user)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({"password_new": list(e.messages)})

        return attrs

    def save(self):
        """Хеширует и сохраняет новый пароль."""
        user = self.context["request"].user
        user.set_password(self.validated_data["password_new"])
        user.save(update_fields=["password"])
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Сериализатор для запроса на восстановление пароля.

    Принимает email пользователя, на который будет отправлена ссылка со сбросом.
    """

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Сериализатор для подтверждения сброса пароля.

    Использует уникальный идентификатор (uidb64) и токен безопасности для
    проверки прав на смену пароля без аутентификации (по ссылке из письма).
    """

    uidb64 = serializers.CharField()
    token = serializers.CharField()
    password_new = serializers.CharField(write_only=True, min_length=8)
    password_new_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """
        Проверка токена, UID и валидация нового пароля.
        """
        # Валидация совпаения паролей
        if attrs["password_new"] != attrs["password_new_confirm"]:
            raise serializers.ValidationError({"password_new_confirm": "Пароли не совпадают."})

        # Поиск пользователя по закодированному id
        try:
            uid = urlsafe_base64_decode(attrs["uidb64"]).decode()
            self.user = User.objects.get(pk=int(uid))
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uidb64": "Неверный идентификатор пользователя."})

        # Валидация токена
        if not default_token_generator.check_token(self.user, attrs["token"]):
            raise serializers.ValidationError({"token": "Ссылка устарела или неверна."})

        # Пользователи, зарегистрированные через социальные сети, не могут изменять пароль
        if self.user.is_social:
            raise serializers.ValidationError(
                {
                    "detail": "Пользователи, зарегистрированные через социальные сети, "
                    "не могут изменять пароль."
                }
            )

        # Валидация пароля - проверка сложности
        try:
            validate_password(attrs["password_new"], self.user)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({"password_new": list(e.messages)})

        return attrs

    def save(self):
        """Хеширует и сохраняет новый пароль."""
        self.user.set_password(self.validated_data["password_new"])
        self.user.save(update_fields=["password"])
        return self.user


class UserBlockResponseSerializer(serializers.Serializer):
    """
    Сериализатор для ответа после блокировки/разблокировки.

    Поля:
        message - сообщение о результате операции
        is_blocked - новый статус блокировки пользователя
    """

    message = serializers.CharField(read_only=True)
    is_blocked = serializers.BooleanField(read_only=True)


class LoginSerializer(serializers.Serializer):
    """Сериализатор для аутентификации пользователя. Используется username или email."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class RefreshJWTBlacklistSerializer(serializers.Serializer):
    """Сериализатор для отзыва (отправка в Blacklist) refresh JWT токена."""

    refresh = serializers.CharField()
