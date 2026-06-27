from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from django.db.models import Max
from .models import BlogPost, BlogCategory


class BlogPostSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7
    protocol = 'https'
    i18n = True

    def items(self):
        return BlogPost.objects.filter(status='published', published_at__lte=timezone.now())

    def lastmod(self, obj):
        return obj.updated_at


class BlogCategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6
    protocol = 'https'
    i18n = True

    def items(self):
        return BlogCategory.objects.filter(is_active=True).annotate(
            latest_post=Max('posts__updated_at')
        )

    def lastmod(self, obj):
        return obj.latest_post
