from rest_framework.routers import SimpleRouter
from users.api import views


router = SimpleRouter()
router.register("users", views.UserViewSet, basename="users")

urlpatterns = [
    *router.urls,
]
