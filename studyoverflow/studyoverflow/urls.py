from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
from navigation.sitemaps import HomeSitemap, PostListSitemap, UserListSitemap
from navigation.views import (
    bad_request,
    page_not_found,
    permission_denied,
    server_error,
)
from posts.sitemaps import PostSitemap
from users.sitemaps import UserSitemap

from studyoverflow import settings


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
    path("api/v1/", include("studyoverflow.urls_api_v1")),
    path(
        "sitemap.xml",
        cache_page(2)(sitemap),  # кеш 2 сек, чтобы данные быстро обновлялись для наглядности
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path(
        "robots.txt",
        cache_page(2)(
            TemplateView.as_view(  # кеш 2 сек, чтобы данные быстро обновлялись для наглядности
                template_name="robots.txt", content_type="text/plain"
            )
        ),
    ),
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
