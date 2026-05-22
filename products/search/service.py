import logging

logger = logging.getLogger(__name__)


class SearchService:

    def __init__(self):
        self._meilisearch = None
        self._fallback = None

    @property
    def meilisearch(self):
        if self._meilisearch is None:
            from .client import is_available
            if is_available():
                from .searcher import MeilisearchSearcher
                self._meilisearch = MeilisearchSearcher()
        return self._meilisearch

    @property
    def fallback(self):
        if self._fallback is None:
            from .fallback import DjangoORMSearcher
            self._fallback = DjangoORMSearcher()
        return self._fallback

    def search(self, query, filters=None, sort=None, page=1, per_page=20, storefront_only=True):
        if storefront_only:
            ms_filters = filters or []
            if isinstance(ms_filters, list):
                ms_filters = ms_filters + ['is_active = true', 'status = "published"']
            else:
                ms_filters = [ms_filters, 'is_active = true', 'status = "published"']
        else:
            ms_filters = filters

        # Try Meilisearch first
        if self.meilisearch:
            result = self.meilisearch.search(query, filters=ms_filters, sort=sort, page=page, per_page=per_page)
            if result is not None:
                return result

        # Fallback to Django ORM
        return self.fallback.search(query, sort=sort, page=page, per_page=per_page)

    def suggest(self, query, limit=5, storefront_only=True):
        if self.meilisearch:
            result = self.meilisearch.suggest(query, limit=limit, storefront_only=storefront_only)
            if result is not None:
                return result
        return self.fallback.suggest(query, limit=limit, storefront_only=storefront_only)

    def did_you_mean(self, query, storefront_only=True):
        if self.meilisearch:
            result = self.meilisearch.did_you_mean(query, storefront_only=storefront_only)
            if result is not None:
                return result
        return self.fallback.did_you_mean(query, storefront_only=storefront_only)

    def dashboard_search(self, query, filters=None, sort=None, page=1, per_page=25):
        if self.meilisearch:
            result = self.meilisearch.dashboard_search(query, filters=filters, sort=sort, page=page, per_page=per_page)
            if result is not None:
                return result
        return self.fallback.search(query, sort=sort, page=page, per_page=per_page)


_service = None


def get_service():
    global _service
    if _service is None:
        _service = SearchService()
    return _service


def search_products(query, **kwargs):
    return get_service().search(query, **kwargs)


def get_suggestions(query, limit=5, storefront_only=True):
    return get_service().suggest(query, limit=limit, storefront_only=storefront_only)
