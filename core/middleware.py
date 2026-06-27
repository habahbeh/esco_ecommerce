import logging
import os
import re

from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


_GEOIP_READER = None
_GEOIP_INITIALIZED = False
_GEOIP_DB_PATHS = (
    '/usr/share/GeoIP/GeoLite2-City.mmdb',
    '/usr/local/share/GeoIP/GeoLite2-City.mmdb',
)


def _get_geoip_reader():
    global _GEOIP_READER, _GEOIP_INITIALIZED
    if _GEOIP_INITIALIZED:
        return _GEOIP_READER
    _GEOIP_INITIALIZED = True
    try:
        import geoip2.database
        for path in _GEOIP_DB_PATHS:
            if os.path.exists(path):
                _GEOIP_READER = geoip2.database.Reader(path)
                logger.info('GeoIP database loaded from %s', path)
                return _GEOIP_READER
    except Exception:
        logger.debug('GeoIP reader could not be initialized', exc_info=True)
    return None


def _lookup_geo(ip):
    if not ip:
        return '', ''
    reader = _get_geoip_reader()
    if reader is None:
        return '', ''
    try:
        resp = reader.city(ip)
        country = (resp.country.name or '')[:100]
        city = (resp.city.name or '')[:100]
        return country, city
    except Exception:
        return '', ''


BOT_PATTERNS = re.compile(
    r'bot|crawl|spider|slurp|bingpreview|mediapartners|facebookexternalhit'
    r'|googlebot|yandex|baidu|duckduckbot|semrush|ahrefs|mj12bot|dotbot'
    r'|petalbot|bytespider|gptbot|claudebot|anthropic',
    re.IGNORECASE,
)

SKIP_PATHS = re.compile(
    r'^/(static|media|admin|dashboard|__debug__|favicon\.ico|robots\.txt|sitemap\.xml|api/)'
)
SKIP_EXTENSIONS = re.compile(r'\.(css|js|png|jpg|jpeg|gif|svg|ico|woff2?|ttf|map|webp)$', re.IGNORECASE)


def _parse_user_agent(ua):
    ua_lower = ua.lower()

    is_bot = bool(BOT_PATTERNS.search(ua_lower))

    if is_bot:
        device_type = 'bot'
    elif any(k in ua_lower for k in ('mobile', 'android', 'iphone', 'ipod')):
        device_type = 'mobile'
    elif any(k in ua_lower for k in ('ipad', 'tablet')):
        device_type = 'tablet'
    else:
        device_type = 'desktop'

    browser = ''
    if 'edg' in ua_lower:
        browser = 'Edge'
    elif 'opr' in ua_lower or 'opera' in ua_lower:
        browser = 'Opera'
    elif 'chrome' in ua_lower and 'safari' in ua_lower:
        browser = 'Chrome'
    elif 'firefox' in ua_lower:
        browser = 'Firefox'
    elif 'safari' in ua_lower:
        browser = 'Safari'
    elif is_bot:
        browser = 'Bot'

    os_name = ''
    if 'windows' in ua_lower:
        os_name = 'Windows'
    elif 'macintosh' in ua_lower or 'mac os' in ua_lower:
        os_name = 'macOS'
    elif 'android' in ua_lower:
        os_name = 'Android'
    elif 'iphone' in ua_lower or 'ipad' in ua_lower:
        os_name = 'iOS'
    elif 'linux' in ua_lower:
        os_name = 'Linux'

    return is_bot, device_type, browser, os_name


class PageViewTrackingMiddleware(MiddlewareMixin):

    def process_response(self, request, response):
        path = request.path

        if SKIP_PATHS.match(path) or SKIP_EXTENSIONS.search(path):
            return response

        if response.status_code < 200 or response.status_code >= 400:
            return response

        content_type = response.get('Content-Type', '')
        if 'text/html' not in content_type:
            return response

        try:
            from core.models import PageView

            ua = request.META.get('HTTP_USER_AGENT', '')
            is_bot, device_type, browser, os_name = _parse_user_agent(ua)

            ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            if not ip:
                ip = request.META.get('REMOTE_ADDR', '')

            user = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user

            session_key = ''
            if hasattr(request, 'session') and request.session.session_key:
                session_key = request.session.session_key

            country, city = _lookup_geo(ip) if not is_bot else ('', '')

            PageView.objects.create(
                path=path[:500],
                full_url=request.build_absolute_uri()[:1000],
                ip_address=ip or None,
                user_agent=ua[:2000],
                referrer=request.META.get('HTTP_REFERER', '')[:1000],
                user=user,
                session_key=session_key,
                country=country,
                city=city,
                device_type=device_type,
                browser=browser,
                os=os_name,
                is_bot=is_bot,
            )
        except Exception:
            logger.debug('Failed to save page view', exc_info=True)

        return response


class AgentReadyMiddleware(MiddlewareMixin):

    def process_request(self, request):
        accept = request.META.get('HTTP_ACCEPT', '')
        if 'text/markdown' in accept:
            return self._markdown_response(request)
        return None

    def process_response(self, request, response):
        response['Content-Signal'] = 'ai-train=no, search=yes, ai-input=yes'
        if request.path in ('/', '/en/', '/ar/'):
            domain = request.build_absolute_uri('/').rstrip('/')
            links = [
                f'<{domain}/.well-known/api-catalog>; rel="api-catalog"',
                f'<{domain}/products/>; rel="service-doc"',
                f'<{domain}/sitemap.xml>; rel="describedby"',
            ]
            response['Link'] = ', '.join(links)
        return response

    def _markdown_response(self, request):
        from core.models import SiteSettings
        settings = SiteSettings.get_settings()

        domain = request.build_absolute_uri('/').rstrip('/')
        site_name = settings.site_name or 'ESCO'

        md = f"""# {site_name}

> {getattr(settings, 'seo_description_ar', '') or 'أكبر متجر إلكتروني للعدد والأدوات الصناعية في الأردن'}

{getattr(settings, 'seo_description_en', '') or 'The largest online store for industrial tools and hardware in Jordan'}

## Navigation

- [Products]({domain}/products/)
- [New Arrivals]({domain}/products/new/)
- [Best Sellers]({domain}/products/bestsellers/)
- [Special Offers]({domain}/products/offers/)
- [About Us]({domain}/about/)
- [Contact]({domain}/contact/)
- [FAQ]({domain}/faq/)

## Contact

- **Phone**: {getattr(settings, 'phone', '') or ''}
- **Email**: {getattr(settings, 'email', '') or ''}
- **Address**: {getattr(settings, 'address_ar', '') or getattr(settings, 'address_en', '') or ''}

## Resources

- [XML Sitemap]({domain}/sitemap.xml)
- [robots.txt]({domain}/robots.txt)
"""
        response = HttpResponse(md, content_type='text/markdown; charset=utf-8')
        response['x-markdown-tokens'] = str(len(md.split()))
        return response
