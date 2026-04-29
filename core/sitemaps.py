from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5
    protocol = 'https'

    def items(self):
        return ['core:home', 'core:about', 'core:contact', 'core:terms', 'core:privacy']

    def location(self, item):
        return reverse(item)
