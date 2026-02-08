from pathlib import Path

import environ
from django.contrib.messages import constants as messages


# Путь к корню проекта с manage.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# --- Инициализация переменных окружения (.env) -------------------------------

env = environ.Env()

# Путь к файлу .env
env_file = BASE_DIR.parent / ".env"

# Загрузка переменных окружения
environ.Env.read_env(env_file)


# --- Настройки безопасности --------------------------------------------------

# Секретный ключ Django
SECRET_KEY = env("DJANGO_SECRET_KEY")

# Режим отладки
DEBUG = env.bool("DEBUG", default=False)

# Список разрешённых хостов, с которых Django разрешает принимать запросы
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost"])

# IP-адреса для debug_toolbar (показывается панель, если IP клиента из INTERNAL_IPS)
INTERNAL_IPS = [
    "127.0.0.1",  # localhost
    "172.18.0.1",  # IP хоста, видимый из Docker-контейнера
]


# --- Установленные приложения ------------------------------------------------

INSTALLED_APPS = [
    # Указывается первым, чтобы django runserver работал через ASGI
    "daphne",
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Сторонние библиотеки
    "django_extensions",  # management-команды, shell_plus и т.д.
    "storages",  # backend для S3 и других хранилищ
    "widget_tweaks",  # функционал для работы с формами в шаблонах
    "channels",  # WebSocket + async Django
    "debug_toolbar",  # панель отладки
    "allauth",  # система аутентификации
    "allauth.account",
    "allauth.socialaccount",
    # Социальные провайдеры
    "allauth.socialaccount.providers.github",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.vk",
    "allauth.socialaccount.providers.yandex",
    # Локальные приложения проекта
    "navigation.apps.NavigationConfig",
    "posts.apps.PostsConfig",
    "users.apps.UsersConfig",
    "notifications.apps.NotificationsConfig",
]


# --- Middleware --------------------------------------------------------------

MIDDLEWARE = [
    # Безопасность
    "django.middleware.security.SecurityMiddleware",
    # Статика через WhiteNoise
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # Сессии
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Локализация (язык, формат дат)
    "django.middleware.locale.LocaleMiddleware",
    # Общие middleware
    "django.middleware.common.CommonMiddleware",
    # CSRF защита
    "django.middleware.csrf.CsrfViewMiddleware",
    # Аутентификация
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Сообщения
    "django.contrib.messages.middleware.MessageMiddleware",
    # Кастомные middleware проекта
    "users.middleware.BlockedUserMiddleware",
    "users.middleware.OnlineStatusMiddleware",
    "navigation.middleware.UserActivityMiddleware",
    # allauth
    "allauth.account.middleware.AccountMiddleware",
    # Защита от clickjacking
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    #  Debug toolbar
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]


# --- Роутинг (urls) + Templates ---------------------------------------------------------

# Файл с конфигурацией роутинга (urls) проекта для маршрутизации
ROOT_URLCONF = "studyoverflow.urls"

# Настройки шаблонов
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# --- WSGI / ASGI -------------------------------------------------------------

# WSGI: точка входа для стандартных синхронных серверов (gunicorn)
WSGI_APPLICATION = "studyoverflow.wsgi.application"

# ASGI: точка входа для асинхронных серверов и WebSocket (daphne, uvicorn, channels)
ASGI_APPLICATION = "studyoverflow.asgi.application"


# --- Email -------------------------------------------------------------------

# Бэкенд для отправки почты через SMTP
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Параметры SMTP
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_SSL = env("EMAIL_USE_SSL")

# Email по умолчанию для исходящих писем с сайта
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Email, с которого Django шлёт системные уведомления
SERVER_EMAIL = EMAIL_HOST_USER

# Список администраторов, которые получают письма об ошибках
ADMINS = [EMAIL_HOST_USER]


# --- Локализация -------------------------------------------------------------

LANGUAGE_CODE = "ru-RU"
TIME_ZONE = "Europe/Moscow"

USE_I18N = True
USE_TZ = True


# --- Прочие базовые настройки проекта ----------------------------------------

# ID сайта (для allauth и django.contrib.sites)
SITE_ID = 1

# Тип primary key по умолчанию
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Кастомная страница ошибки CSRF
CSRF_FAILURE_VIEW = "navigation.views.csrf_failure"

# CSS-классы для сообщений Django
MESSAGE_TAGS = {
    messages.SUCCESS: "success",
    messages.INFO: "info",
    messages.ERROR: "danger",
}
