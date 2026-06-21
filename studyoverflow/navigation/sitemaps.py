from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class HomeSitemap(Sitemap):
    """Главная страница."""

    priority = 1.0
    changefreq = "monthly"

    def items(self):
        return ["home"]

    def location(self, item):
        return reverse(item)


class PostListSitemap(Sitemap):
    """Список последних постов."""

    changefreq = "hourly"
    priority = 0.9

    def items(self):
        return ["posts:list"]

    def location(self, item):
        return reverse(item)


class UserListSitemap(Sitemap):
    """Список наиболее авторитетных пользователей."""

    changefreq = "daily"
    priority = 0.8

    def items(self):
        return ["users:list"]

    def location(self, item):
        return reverse(item)
