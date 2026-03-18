from rest_framework.routers import SimpleRouter
from users.api import views


router = SimpleRouter()
router.register("users", views.UserViewSet, basename="users")
router.register("auth", views.AuthViewSet, basename="auth")

urlpatterns = [
    *router.urls,
]
