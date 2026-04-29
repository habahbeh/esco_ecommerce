from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


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
