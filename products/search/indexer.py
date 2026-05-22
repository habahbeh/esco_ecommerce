import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

SEARCHABLE_ATTRIBUTES = [
    'sku', 'barcode', 'variant_skus', 'name', 'name_en',
    'variant_names', 'short_description', 'search_keywords',
    'category_name', 'category_name_en',
    'brand_name', 'brand_name_en',
    'tags', 'description',
]

FILTERABLE_ATTRIBUTES = [
    'category_id', 'brand_id', 'base_price',
    'stock_status', 'is_active', 'status',
    'is_featured', 'is_new',
]

SORTABLE_ATTRIBUTES = [
    'base_price', 'sales_count', 'views_count', 'created_at',
]


class MeilisearchIndexer:

    def __init__(self):
        from .client import get_index
        self.index = get_index()

    def setup_index(self):
        if not self.index:
            return False
        try:
            self.index.update_searchable_attributes(SEARCHABLE_ATTRIBUTES)
            self.index.update_filterable_attributes(FILTERABLE_ATTRIBUTES)
            self.index.update_sortable_attributes(SORTABLE_ATTRIBUTES)
            self.index.update_typo_tolerance({
                'enabled': True,
                'minWordSizeForTypos': {'oneTypo': 3, 'twoTypos': 6},
                'disableOnAttributes': ['sku', 'barcode', 'variant_skus'],
            })
            self.index.update_pagination({'maxTotalHits': 5000})
            self._push_synonyms()
            logger.info("Meilisearch index configured")
            return True
        except Exception as e:
            logger.error(f"Failed to configure Meilisearch index: {e}")
            return False

    def _push_synonyms(self):
        try:
            from products.models import SearchSynonym
            synonyms = {}
            for syn in SearchSynonym.objects.filter(is_active=True):
                terms = [t.strip().lower() for t in syn.terms.split(',') if t.strip()]
                for term in terms:
                    synonyms[term] = [t for t in terms if t != term]
            if synonyms:
                self.index.update_synonyms(synonyms)
                logger.info(f"Pushed {len(synonyms)} synonym mappings")
        except Exception as e:
            logger.warning(f"Could not push synonyms: {e}")

    def product_to_document(self, product):
        default_image = settings.STATIC_URL + 'images/no-image.png'
        image_url = default_image
        try:
            all_images = list(product.images.all())
            if all_images:
                primary = next((img for img in all_images if img.is_primary), None)
                img = primary or all_images[0]
                if img and img.image and os.path.isfile(img.image.path):
                    image_url = img.image.url
        except Exception:
            pass

        tags = []
        try:
            tags = list(product.tags.values_list('name', flat=True))
        except Exception:
            pass

        variant_skus = []
        variant_names = []
        try:
            for v in product.variants.filter(is_active=True):
                if v.sku:
                    variant_skus.append(v.sku)
                if v.name:
                    variant_names.append(v.name)
        except Exception:
            pass

        return {
            'id': product.id,
            'name': product.name or '',
            'name_en': product.name_en or '',
            'sku': product.sku or '',
            'barcode': product.barcode or '',
            'description': (product.description or '')[:500],
            'short_description': product.short_description or '',
            'search_keywords': product.search_keywords or '',
            'category_id': product.category_id,
            'category_name': product.category.name if product.category else '',
            'category_name_en': product.category.name_en if product.category and hasattr(product.category, 'name_en') else '',
            'brand_id': product.brand_id,
            'brand_name': product.brand.name if product.brand else '',
            'brand_name_en': product.brand.name_en if product.brand and hasattr(product.brand, 'name_en') else '',
            'tags': tags,
            'variant_skus': variant_skus,
            'variant_names': variant_names,
            'base_price': float(product.base_price or 0),
            'stock_status': product.stock_status or 'in_stock',
            'is_active': product.is_active,
            'status': product.status,
            'is_featured': product.is_featured,
            'is_new': getattr(product, 'is_new', False),
            'sales_count': product.sales_count or 0,
            'views_count': product.views_count or 0,
            'created_at': product.created_at.timestamp() if product.created_at else 0,
            'image_url': image_url,
        }

    def index_product(self, product):
        if not self.index:
            return
        try:
            doc = self.product_to_document(product)
            self.index.add_documents([doc], primary_key='id')
        except Exception as e:
            logger.warning(f"Failed to index product {product.id}: {e}")

    def delete_product(self, product_id):
        if not self.index:
            return
        try:
            self.index.delete_document(product_id)
        except Exception as e:
            logger.warning(f"Failed to delete product {product_id}: {e}")

    def index_all_products(self, batch_size=500):
        if not self.index:
            return 0
        from products.models import Product
        product_ids = list(Product.objects.values_list('id', flat=True))

        total = 0
        for i in range(0, len(product_ids), batch_size):
            chunk_ids = product_ids[i:i + batch_size]
            products = Product.objects.filter(id__in=chunk_ids).select_related(
                'category', 'brand'
            ).prefetch_related('images', 'tags', 'variants')
            batch = [self.product_to_document(p) for p in products]
            if batch:
                self.index.add_documents(batch, primary_key='id')
                total += len(batch)

        logger.info(f"Indexed {total} products in Meilisearch")
        return total

    def clear_index(self):
        if not self.index:
            return
        self.index.delete_all_documents()
        logger.info("Cleared Meilisearch index")
