import logging
import time
from django.conf import settings

logger = logging.getLogger(__name__)

_client = None
_available = None
_last_check = 0
_CHECK_INTERVAL = 300


def get_client():
    global _client, _last_check
    if _client is not None:
        return _client
    now = time.monotonic()
    if now - _last_check < _CHECK_INTERVAL:
        return None
    _last_check = now
    try:
        import meilisearch
        url = getattr(settings, 'MEILISEARCH_URL', 'http://127.0.0.1:7700')
        key = getattr(settings, 'MEILISEARCH_MASTER_KEY', '')
        _client = meilisearch.Client(url, key, timeout=2)
        _client.health()
        return _client
    except Exception as e:
        logger.warning(f"Meilisearch unavailable: {e}")
        _client = None
        return None


def is_available():
    return get_client() is not None


def reset_client():
    global _client, _available, _last_check
    _client = None
    _available = None
    _last_check = 0


def get_index(name=None):
    client = get_client()
    if client is None:
        return None
    prefix = getattr(settings, 'MEILISEARCH_INDEX_PREFIX', 'esco_')
    index_name = name or f'{prefix}products'
    return client.index(index_name)
