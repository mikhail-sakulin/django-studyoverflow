from django.urls import include, path
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from users.api import views


router = SimpleRouter()
router.register("users", views.UserViewSet, basename="users")
router.register("auth", views.AuthViewSet, basename="auth")

urlpatterns = [
    *router.urls,
    path("auth/jwt-token-login/", TokenObtainPairView.as_view(), name="jwt_login"),
    path("auth/jwt-token-refresh/", TokenRefreshView.as_view(), name="jwt_refresh"),
    path("auth/jwt-token-verify/", TokenVerifyView.as_view(), name="jwt_verify"),
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/google/", views.GoogleLoginAPI.as_view(), name="google_api_jwt"),
    path("auth/github/", views.GitHubLoginAPI.as_view(), name="github_api_jwt"),
    path("auth/vk/", views.VKLoginAPI.as_view(), name="vk_api_jwt"),
    path("auth/yandex/", views.YandexLoginAPI.as_view(), name="yandex_api_jwt"),
]
