"""
Модуль конфигурации URL для социальной аутентификации.

Содержит маршруты для OAuth2-аутентификации через социальные провайдеры:
- GitHub;
- Google;
- Yandex;
- VK.
"""

from allauth.account import views as account_views
from allauth.socialaccount import views as social_views
from allauth.socialaccount.providers.github.provider import GitHubProvider
from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns as oauth2_urlpatterns
from allauth.socialaccount.providers.vk.provider import VKProvider
from allauth.socialaccount.providers.yandex.provider import YandexProvider
from django.urls import include, path


urlpatterns = [
    path("", include(oauth2_urlpatterns(GitHubProvider))),
    path("", include(oauth2_urlpatterns(GoogleProvider))),
    path("", include(oauth2_urlpatterns(YandexProvider))),
    path("", include(oauth2_urlpatterns(VKProvider))),
    path(
        "accounts/signup/",
        social_views.SignupView.as_view(template_name="users/socialaccount_signup.html"),
        name="socialaccount_signup",
    ),
    path("confirm-email/<str:key>/", account_views.confirm_email, name="account_confirm_email"),
    path(
        "confirm-email/",
        account_views.email_verification_sent,
        name="account_email_verification_sent",
    ),
    path("login/error/", social_views.login_error, name="socialaccount_login_error"),
    path("login/cancelled/", social_views.login_cancelled, name="socialaccount_login_cancelled"),
]
