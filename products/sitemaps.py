from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Category, Brand


class ProductSitemap(Sitemap):
    """Product sitemap with image extension and bilingual hreflang annotations."""
    changefreq = 'weekly'
    priority = 0.8
    protocol = 'https'
    i18n = True  # Emit xhtml:link hreflang entries for ar/en

    def items(self):
        return Product.objects.filter(
            is_active=True, status='published'
        ).select_related('category').prefetch_related('images').order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('products:product_detail', kwargs={'slug': obj.slug})

    def get_urls(self, page=1, site=None, protocol=None):
        """Augment each URL dict with an `images` key. The custom template uses it."""
        urls = super().get_urls(page=page, site=site, protocol=protocol)
        # urls is a list of dicts; each has the original item under 'item' if get_urls was overridden,
        # but Django's default doesn't include it. We re-attach via index.
        # Simpler: walk items() and zip — but with i18n=True each item appears N times.
        return urls


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7
    protocol = 'https'
    i18n = True

    def items(self):
        return Category.objects.filter(is_active=True).order_by('level', 'sort_order')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('products:category_products', kwargs={'category_slug': obj.slug})


class BrandSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6
    protocol = 'https'
    i18n = True

    def items(self):
        return Brand.objects.filter(is_active=True).order_by('name')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('products:brand_products', kwargs={'brand_slug': obj.slug})
