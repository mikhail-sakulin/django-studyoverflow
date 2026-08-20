from django.conf import settings
from django.contrib.sites.models import Site


def sync_site_domain(sender, **kwargs):
    """
    Обработчик сигнала post_migrate: синхронизирует текущий Site
    с доменом из переменной окружения SITE_DOMAIN.
    """
    site, _ = Site.objects.get_or_create(pk=settings.SITE_ID)
    domain = settings.SITE_DOMAIN

    if site.domain != domain or site.name != domain:
        site.domain = domain
        site.name = domain
        site.save(update_fields=["domain", "name"])
