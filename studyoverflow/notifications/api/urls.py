from rest_framework.routers import SimpleRouter

from notifications.api import views


app_name = "notifications"


router = SimpleRouter()
router.register("notifications", views.NotificationViewSet, basename="notifications")

urlpatterns = [
    *router.urls,
]
