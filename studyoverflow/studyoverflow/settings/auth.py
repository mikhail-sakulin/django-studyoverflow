from .base import env


# ----------------------------------------
# Модель пользователя (User)
# ----------------------------------------

# Кастомная модель пользователя
AUTH_USER_MODEL = "users.User"


# ----------------------------------------
# Редиректы после логина/логаута
# ----------------------------------------

# URL страницы для логина
LOGIN_URL = "/users/login/"

# URL для редиректа после успешного логина
LOGIN_REDIRECT_URL = "home"

# URL для редиректа после логаута
LOGOUT_REDIRECT_URL = "home"


# ----------------------------------------
# Валидация паролей
# ----------------------------------------

# Стандартные валидаторы Django
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ----------------------------------------
# Allauth настройки
# ----------------------------------------

# Бэкенды аутентификации
AUTHENTICATION_BACKENDS = [
    # Позволяет логин через стандартный ModelBackend (для админки)
    "django.contrib.auth.backends.ModelBackend",
    # Позволяет логин через allauth (email, соцсети)
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Методы логина для allauth (можно через username или email)
ACCOUNT_LOGIN_METHODS = {"username", "email"}

# Кастомные адаптеры
SOCIALACCOUNT_ADAPTER = "users.adapters.CustomSocialAccountAdapter"
ACCOUNT_ADAPTER = "users.adapters.AllauthMessageAdapter"

# Поля, обязательные при регистрации через allauth
ACCOUNT_SIGNUP_FIELDS = ["username*", "email*", "password1*", "password2*"]

# Отключение верификации email (можно включить по необходимости)
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"

# Автоматическая регистрация пользователя при первом входе через социальный аккаунт
SOCIALACCOUNT_AUTO_SIGNUP = True


# ----------------------------------------
# Социальные провайдеры
# ----------------------------------------

# Настройки для OAuth-провайдеров
SOCIALACCOUNT_PROVIDERS = {
    "github": {
        "APPS": [
            {
                "client_id": env("SOCIAL_AUTH_GITHUB_ID"),
                "secret": env("SOCIAL_AUTH_GITHUB_SECRET"),
            },
        ],
        "SCOPE": [
            "read:user",
            "user:email",
        ],
    },
    "google": {
        "APPS": [
            {
                "client_id": env("SOCIAL_AUTH_GOOGLE_ID"),
                "secret": env("SOCIAL_AUTH_GOOGLE_SECRET"),
                "key": "",
            },
        ],
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
        "OAUTH_PKCE_ENABLED": True,
    },
    "yandex": {
        "APPS": [
            {
                "client_id": env("SOCIAL_AUTH_YANDEX_ID"),
                "secret": env("SOCIAL_AUTH_YANDEX_SECRET"),
            }
        ],
        "SCOPE": [
            "login:info",
            "login:avatar",
        ],
    },
    "vk": {
        "APPS": [
            {
                "client_id": env("SOCIAL_AUTH_VK_ID"),
                "secret": env("SOCIAL_AUTH_VK_SECRET"),
            }
        ],
        "SCOPE": ["email", "public_profile"],
        "VERSION": "5.131",
    },
}
