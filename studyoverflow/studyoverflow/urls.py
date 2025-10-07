import posts.views
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from studyoverflow import settings


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("navigation.urls")),
    path("posts/", include("posts.urls")),
    path("users/", include("users.urls")),
    path("favicon.ico", RedirectView.as_view(url=settings.STATIC_URL + "img/favicon.ico")),
]
