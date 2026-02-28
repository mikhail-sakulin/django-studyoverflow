from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from navigation.views import (
    bad_request,
    page_not_found,
    permission_denied,
    server_error,
)

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
    path("social-auth/", include("users.socialaccount_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = bad_request
handler403 = permission_denied
handler404 = page_not_found
handler500 = server_error


admin.site.site_header = "Панель администрирования"
admin.site.index_title = "Администрирование StudyOverflow"
