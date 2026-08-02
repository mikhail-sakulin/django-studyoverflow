import socket

from . import *


# Фиксирует доменное имя компьютера как localhost,
# чтобы избежать задержек DNS (например, при активном VPN).
#
# Используется для теста users/tests/views/test_user_views.py::TestPasswordResetViews,
# так как для формирования заголовка Message-ID при отправке письма вызывается socket.getfqdn(),
# который (например, при активном VPN) может инициировать реальный DNS-запрос во внешнюю сеть
# для поиска имени локальной машины.
socket.getfqdn = lambda name="": "localhost"


CACHES = {
    "default": {
        # Во время тестов кеш сохраняется в оперативную память
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        # Имя области в оперативной памяти под кеш
        "LOCATION": "studyoverflow-test-cache",
    }
}

# Во время тестов отправка писем имитируется в ОЗУ (django.core.mail.outbox) для их проверки,
# отправленные письма помещаются в список django.core.mail.outbox
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Быстрый хешер паролей для тестов, в проде для защиты специально используется
# более медленный по умолчанию
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Заставляет Celery выполнять задачи синхронно в текущем процессе, не отправляя их в брокер,
# после .delay() задача сразу выполняется
CELERY_TASK_ALWAYS_EAGER = True

# Перенаправляет все исключения из задач в тест, тест упадет, если в задаче ошибка
CELERY_TASK_EAGER_PROPAGATES = True

# Файловое хранилище для медиа (аватарки пользователей) в оперативной памяти
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Стандартный Channel Layer, который сохраняет сообщения и группы в оперативной памяти
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}
