from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


app_name = "api"


urlpatterns = [
    path("", include("posts.api.urls", namespace="posts")),
    path("", include("notifications.api.urls", namespace="notifications")),
    path("", include("users.api.urls", namespace="users")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema")),
]
