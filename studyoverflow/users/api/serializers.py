from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from rest_framework import serializers
from users.services import is_user_online


User = get_user_model()


class UserPublicProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для публичного профиля пользователя.

    Предоставляет общую информацию, доступную всем посетителям, включая
    статус "онлайн" и ссылки на различные размеры аватара.
    """

    avatar_urls = serializers.SerializerMethodField()
    online_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "online_status",
            "avatar_urls",
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

    def get_avatar_urls(self, user):
        """Возвращает словарь ссылок на оригинал и миниатюры аватара."""
        return {
            "avatar_original": user.avatar.url,
            "size1": user.avatar_small_size1_url,
            "size2": user.avatar_small_size2_url,
            "size3": user.avatar_small_size3_url,
        }

    def get_online_status(self, user):
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
            "avatar": {"write_only": True},
        }
        read_only_fields = [
            "id",
            "avatar_urls",
            "reputation",
            "posts_count",
            "comments_count",
            "date_joined",
            "last_seen",
            "is_social",
            "role",
            "is_blocked",
        ]


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

    avatar_url = serializers.CharField(source="avatar_small_size2_url")
    online_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "role",
            "online_status",
            "avatar_url",
            "reputation",
            "posts_count",
            "comments_count",
            "last_seen",
        ]
        read_only_fields = fields

    def get_online_status(self, user):
        """
        Определяет статус онлайн на основе списка ID, полученного из контекста из Redis во ViewSet.
        """
        online_ids = self.context.get("online_ids", set())
        return user.id in online_ids


class UserPasswordChangeSerializer(serializers.ModelSerializer):
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

    class Meta:
        model = User
        fields = ["password_old", "password_new", "password_new_confirm"]

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
        user.save()
        return user
