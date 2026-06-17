from django.urls import path
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from users.api import views


router = SimpleRouter()
router.register("users", views.UserViewSet, basename="users")
router.register("auth", views.AuthViewSet, basename="auth")

urlpatterns = [
    *router.urls,
    path("auth/jwt-token-login/", TokenObtainPairView.as_view(), name="jwt-login"),
    path("auth/jwt-token-refresh/", TokenRefreshView.as_view(), name="jwt-refresh"),
    path("auth/jwt-token-verify/", TokenVerifyView.as_view(), name="jwt-verify"),
]
