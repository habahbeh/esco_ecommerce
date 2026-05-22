import logging

logger = logging.getLogger(__name__)


class MeilisearchSearcher:

    def __init__(self):
        from .client import get_index
        self.index = get_index()

    def search(self, query, filters=None, sort=None, page=1, per_page=20):
        if not self.index:
            return None
        try:
            params = {
                'limit': per_page,
                'offset': (page - 1) * per_page,
                'attributesToHighlight': ['name', 'name_en', 'short_description'],
                'highlightPreTag': '<mark>',
                'highlightPostTag': '</mark>',
            }
            if filters:
                params['filter'] = filters
            if sort:
                params['sort'] = sort

            result = self.index.search(query, params)
            return {
                'hits': result.get('hits', []),
                'total': result.get('estimatedTotalHits', 0),
                'query': result.get('query', query),
                'processing_time_ms': result.get('processingTimeMs', 0),
            }
        except Exception as e:
            logger.warning(f"Meilisearch search failed: {e}")
            return None

    def suggest(self, query, limit=5, storefront_only=True):
        if not self.index:
            return None
        try:
            params = {
                'limit': limit,
                'attributesToRetrieve': [
                    'id', 'name', 'name_en', 'sku', 'base_price',
                    'image_url', 'category_name', 'category_name_en',
                    'brand_name', 'brand_name_en',
                ],
                'attributesToHighlight': ['name', 'name_en'],
                'highlightPreTag': '<mark>',
                'highlightPostTag': '</mark>',
            }
            if storefront_only:
                params['filter'] = ['is_active = true', 'status = "published"']

            result = self.index.search(query, params)
            return result.get('hits', [])
        except Exception as e:
            logger.warning(f"Meilisearch suggest failed: {e}")
            return None

    def did_you_mean(self, query, storefront_only=True):
        if not self.index:
            return None
        try:
            params = {
                'limit': 1,
                'attributesToRetrieve': ['id'],
            }
            if storefront_only:
                params['filter'] = ['is_active = true', 'status = "published"']

            result = self.index.search(query, params)
            total = result.get('estimatedTotalHits', 0)
            if total > 0:
                return None

            # Try partial query (first 3 chars) to find alternatives
            partial = query[:3] if len(query) > 3 else query
            params['limit'] = 5
            params['attributesToRetrieve'] = ['name', 'name_en']
            alt_result = self.index.search(partial, params)
            alt_hits = alt_result.get('hits', [])
            if alt_hits:
                suggestions = []
                for hit in alt_hits:
                    name = hit.get('name', '')
                    name_en = hit.get('name_en', '')
                    if name:
                        suggestions.append(name)
                    if name_en:
                        suggestions.append(name_en)
                return list(dict.fromkeys(suggestions))[:3]
            return None
        except Exception as e:
            logger.warning(f"Meilisearch did_you_mean failed: {e}")
            return None

    def dashboard_search(self, query, filters=None, sort=None, page=1, per_page=25):
        if not self.index:
            return None
        try:
            params = {
                'limit': per_page,
                'offset': (page - 1) * per_page,
            }
            if filters:
                params['filter'] = filters
            if sort:
                params['sort'] = sort

            result = self.index.search(query, params)
            return {
                'hits': result.get('hits', []),
                'total': result.get('estimatedTotalHits', 0),
            }
        except Exception as e:
            logger.warning(f"Meilisearch dashboard search failed: {e}")
            return None
