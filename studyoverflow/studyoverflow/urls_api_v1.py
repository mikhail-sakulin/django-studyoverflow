from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


urlpatterns = [
    path("", include("posts.api.urls")),
    path("", include("notifications.api.urls")),
    path("", include("users.api.urls")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema")),
]
