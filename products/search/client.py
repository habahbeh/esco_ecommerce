import logging
from django.conf import settings

logger = logging.getLogger(__name__)

_client = None
_available = None


def get_client():
    global _client
    if _client is not None:
        return _client
    try:
        import meilisearch
        url = getattr(settings, 'MEILISEARCH_URL', 'http://127.0.0.1:7700')
        key = getattr(settings, 'MEILISEARCH_MASTER_KEY', '')
        _client = meilisearch.Client(url, key)
        _client.health()
        return _client
    except Exception as e:
        logger.warning(f"Meilisearch unavailable: {e}")
        _client = None
        return None


def is_available():
    return get_client() is not None


def reset_client():
    global _client, _available
    _client = None
    _available = None


def get_index(name=None):
    client = get_client()
    if client is None:
        return None
    prefix = getattr(settings, 'MEILISEARCH_INDEX_PREFIX', 'esco_')
    index_name = name or f'{prefix}products'
    return client.index(index_name)
