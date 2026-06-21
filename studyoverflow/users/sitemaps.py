from django.contrib.auth import get_user_model
from django.contrib.sitemaps import Sitemap


User = get_user_model()


class UserSitemap(Sitemap):
    """Профили пользователей."""

    changefreq = "daily"
    priority = 0.7

    def items(self):
        return User.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.date_joined
