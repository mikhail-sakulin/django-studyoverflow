"""
Модуль конфигурации URL для социальной аутентификации.

Содержит маршруты для OAuth2-аутентификации через социальные провайдеры:
- Yandex;
- VK;
- GitHub (отключено);
- Google (отключено).

В соответствии с ФЗ №149 авторизация через сервисы GitHub и Google недоступна.
"""

from allauth.socialaccount import views as social_views
from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns as oauth2_urlpatterns
from allauth.socialaccount.providers.vk.provider import VKProvider
from allauth.socialaccount.providers.yandex.provider import YandexProvider
from django.urls import include, path


urlpatterns = [
    # Подключает 2 эндпоинта для каждого провайдера:
    # - yandex/login/: инициирует OAuth - редиректит пользователя на страницу авторизации Yandex
    # - yandex/login/callback/: Yandex редиректит на этот url пользователя с code.
    #   Затем code обменивается на access_token, через который бекенд получает от соцсети
    #   данные пользователя.
    path("", include(oauth2_urlpatterns(YandexProvider))),
    # Аналогично для VK: vk/login/ и vk/login/callback/.
    path("", include(oauth2_urlpatterns(VKProvider))),
    #
    # В соответствии с ФЗ №149 авторизация через сервисы GitHub и Google недоступна.
    # path("", include(oauth2_urlpatterns(GitHubProvider))),
    # path("", include(oauth2_urlpatterns(GoogleProvider))),
    #
    # Эндпоинт формы уточнения данных, если после OAuth невозможно создать аккаунт из полученных
    # данных пользователя, например, когда данных недостаточно или есть конфликты, например,
    # аккаунта с полученным email уже существует.
    path(
        "accounts/signup/",
        social_views.SignupView.as_view(template_name="users/socialaccount_signup.html"),
        name="socialaccount_signup",
    ),
    # Эндпоинт для редиректа, когда OAuth авторизация завершилась с ошибкой на стороне провайдера
    # или django-allauth.
    path("login/error/", social_views.login_error, name="socialaccount_login_error"),
    # Эндпоинт для редиректа, когда пользователь нажал на кнопку запрета доступа на
    # стороне провайдера.
    path("login/cancelled/", social_views.login_cancelled, name="socialaccount_login_cancelled"),
]
