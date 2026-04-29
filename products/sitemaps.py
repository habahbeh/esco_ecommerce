from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Category, Brand


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8
    protocol = 'https'

    def items(self):
        return Product.objects.filter(
            is_active=True, status='published'
        ).select_related('category').order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('products:product_detail', kwargs={'slug': obj.slug})


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7
    protocol = 'https'

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

    def items(self):
        return Brand.objects.filter(is_active=True).order_by('name')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('products:brand_products', kwargs={'brand_slug': obj.slug})
