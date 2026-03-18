from django.urls import include, path


urlpatterns = [
    path("", include("posts.api.urls")),
    path("", include("notifications.api.urls")),
    path("", include("users.api.urls")),
]
