from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from studyoverflow import settings


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("navigation.urls")),
    path("posts/", include("posts.urls")),
    path("users/", include("users.urls")),
    path("notifications/", include("notifications.urls")),
    path("__debug__", include(debug_toolbar_urls())),
    path(
        "favicon.ico",
        RedirectView.as_view(url=settings.STATIC_URL + "img/favicon.ico"),
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
