from django.contrib.sitemaps import Sitemap
from posts.models import Post


class PostSitemap(Sitemap):
    """Детальное представление постов."""

    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Post.objects.all()

    def lastmod(self, obj):
        return obj.time_update
