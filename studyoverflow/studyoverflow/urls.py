from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.decorators.cache import cache_page

from navigation.sitemaps import HomeSitemap, PostListSitemap, UserListSitemap
from navigation.views import (
    bad_request,
    page_not_found,
    permission_denied,
    server_error,
)
from posts.sitemaps import PostSitemap
from studyoverflow import settings
from users.sitemaps import UserSitemap


sitemaps = {
    "home": HomeSitemap,
    "posts": PostSitemap,
    "users": UserSitemap,
    "post_list": PostListSitemap,
    "user_list": UserListSitemap,
}


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("navigation.urls")),
    path("posts/", include("posts.urls")),
    path("users/", include("users.urls")),
    path("notifications/", include("notifications.urls")),
    path("social-auth/", include("users.urls_socialaccount")),
    path("api/v1/", include("studyoverflow.urls_api_v1", namespace="api")),
    path(
        "sitemap.xml",
        # Кеш 12 часов
        cache_page(12 * 60 * 60)(sitemap),
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    # Файл robots.txt отдается через nginx как статика
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path("__debug__", include(debug_toolbar_urls()))]

handler400 = bad_request
handler403 = permission_denied
handler404 = page_not_found
handler500 = server_error


admin.site.site_header = "Панель администрирования"
admin.site.index_title = "Администрирование StudyOverflow"
