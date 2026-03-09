from notifications.api import views
from rest_framework.routers import SimpleRouter


router = SimpleRouter()
router.register("notifications", views.NotificationViewSet, basename="notifications")

urlpatterns = [
    *router.urls,
]
