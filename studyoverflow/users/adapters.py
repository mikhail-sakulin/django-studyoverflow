from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from users.services import SOCIAL_HANDLERS
from users.tasks import download_and_set_avatar


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Кастомный social адаптер django-allauth, отвечающий за OAuth-аутентификацию,
    создание и первичную инициализацию аккаунтов пользователей через социальные сети.

    Не используется для других способов аутентификации.
    """

    def populate_user(self, request, sociallogin, data):
        """
        Заполняет базовые поля пользователя на основе данных OAuth.

        Логика:
        - Вызывает стандартный метод.
        - Если username отсутствует:
            - Берёт часть email до @.
            - Если email отсутствует — для username использует provider_uid.
        - Если email отсутствует — создаёт технический email.
        """
        user = super().populate_user(request, sociallogin, data)

        # Если у пользователя еще нет username
        if not user.username:
            email = data.get("email")
            if email:
                # Берется часть до @
                user.username = email.split("@")[0]
            else:
                # Если почты нет, используется ID провайдера
                user.username = f"{sociallogin.account.provider}_{sociallogin.account.uid}"

        if not user.email:
            # Создается уникальный технический email
            user.email = f"{sociallogin.account.uid}@noemail{sociallogin.account.provider}.local"

        return user

    def save_user(self, request, sociallogin, form=None):
        """
        Сохраняет пользователя после успешной OAuth-аутентификации.

        Логика:
        - Вызывает стандартный метод сохранения.
        - Устанавливает флаг is_social для пользователя.
        - Определяет OAuth-провайдера.
        - Вызывает соответствующий провайдеру SOCIAL_HANDLER
          для обработки first_name, last_name и avatar_url.
        - Сохраняет обновлённого пользователя.
        - Если получен avatar_url — запускает асинхронную Celery задачу для загрузки аватара.

        Загрузка аватара выполняется через Celery после выполнения транзакции.
        """
        user = super().save_user(request, sociallogin, form)

        user.is_social = True

        avatar_url = None

        provider = sociallogin.account.provider
        data = sociallogin.account.extra_data
        handler = SOCIAL_HANDLERS.get(provider)

        if handler:
            avatar_url = handler(user, data)

        user.save()

        if avatar_url:
            transaction.on_commit(lambda: download_and_set_avatar.delay(user.pk, avatar_url))

        return user

    def pre_social_login(self, request, sociallogin):
        """
        Выполняется перед входом пользователя через соцсеть.

        Запрещает вход через соцсеть заблокированным пользователям.
        """
        user = sociallogin.user

        if getattr(user, "is_blocked", False):
            if user.blocked_at:
                local_date_block = timezone.localtime(user.blocked_at)
                date_str = local_date_block.strftime("%d.%m.%Y г. %H:%M")
            else:
                date_str = '"неизвестно"'

            messages.error(request, f"Ваш аккаунт заблокирован {date_str}.")

            raise ImmediateHttpResponse(redirect("home"))


class AllauthMessageAdapter(DefaultAccountAdapter):
    """
    Кастомный default account адаптер django-allauth.

    В данном проекте используется исключительно для кастомизации
    приветственного сообщения при логине через соцсеть с помощью django-allauth.

    Не используется для других способов аутентификации.
    """

    def add_message(
        self,
        request,
        level,
        message_template=None,
        message_context=None,
        extra_tags="",
        message=None,
    ):
        """
        Переопределяет стандартное сообщение django-allauth при входе.
        """
        if message_template == "account/messages/logged_in.txt":
            user = message_context.get("user") if message_context else None

            if user:
                message = f"Добро пожаловать, {user.get_username()}!"
                message_template = None

        return super().add_message(
            request, level, message_template, message_context, extra_tags, message
        )
