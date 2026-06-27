import json
from django.http import JsonResponse, HttpResponse
from django.views import View

from .models import SiteSettings


class TrafficAdviceView(View):
    """Serve /.well-known/traffic-advice for Chrome Private Prefetch Proxy probes.

    Empty array means: no special prefetch policy, use defaults.
    See https://github.com/buettner/private-prefetch-proxy/blob/main/traffic-advice.md
    """

    def get(self, request):
        return HttpResponse(
            '[]',
            content_type='application/trafficadvice+json',
        )


class MCPServerCardView(View):

    def get(self, request):
        settings = SiteSettings.get_settings()
        domain = self._get_domain(request, settings)
        site_name = settings.site_name or 'ESCO'

        card = {
            "name": site_name,
            "description": "ESCO - The largest online store for industrial tools, power tools, and hardware in Jordan",
            "url": domain,
            "version": "1.0.0",
            "capabilities": {
                "tools": [
                    {
                        "name": "search_products",
                        "description": "Search for industrial tools, power tools, and hardware products",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query for products"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "browse_categories",
                        "description": "Browse product categories",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            },
            "links": {
                "website": domain,
                "sitemap": f"{domain}/sitemap.xml",
                "robots": f"{domain}/robots.txt"
            },
            "contact": {
                "email": getattr(settings, 'email', '') or '',
                "phone": getattr(settings, 'phone', '') or ''
            }
        }
        return JsonResponse(card)

    def _get_domain(self, request, settings):
        if settings.canonical_domain:
            return settings.canonical_domain.rstrip('/')
        return request.build_absolute_uri('/').rstrip('/')


class A2AAgentCardView(View):

    def get(self, request):
        settings = SiteSettings.get_settings()
        domain = self._get_domain(request, settings)
        site_name = settings.site_name or 'ESCO'

        card = {
            "name": f"{site_name} Agent",
            "description": "ESCO e-commerce agent for browsing and searching industrial tools, power tools, and hardware products in Jordan",
            "url": domain,
            "version": "1.0.0",
            "provider": {
                "organization": site_name,
                "url": domain
            },
            "capabilities": {
                "streaming": False,
                "pushNotifications": False
            },
            "skills": [
                {
                    "id": "product-search",
                    "name": "Product Search",
                    "description": "Search for industrial tools and hardware products by name, brand, or category",
                    "tags": ["search", "products", "tools", "hardware"],
                    "examples": [
                        "Find Bosch power drills",
                        "Search for Makita angle grinders",
                        "Show TOTAL hand tools"
                    ]
                },
                {
                    "id": "browse-catalog",
                    "name": "Browse Catalog",
                    "description": "Browse product categories, brands, new arrivals, best sellers, and special offers",
                    "tags": ["browse", "catalog", "categories", "brands"],
                    "examples": [
                        "Show new arrivals",
                        "List product categories",
                        "Show best selling products"
                    ]
                }
            ],
            "defaultInputModes": ["text/plain"],
            "defaultOutputModes": ["text/plain", "text/html"]
        }
        return JsonResponse(card)

    def _get_domain(self, request, settings):
        if settings.canonical_domain:
            return settings.canonical_domain.rstrip('/')
        return request.build_absolute_uri('/').rstrip('/')


class AgentSkillsView(View):

    def get(self, request):
        settings = SiteSettings.get_settings()
        domain = self._get_domain(request, settings)

        index = {
            "version": "0.2.0",
            "skills": [
                {
                    "id": "product-search",
                    "name": "Product Search",
                    "description": "Search ESCO's catalog of industrial tools, power tools, and hardware products. Supports Arabic and English queries.",
                    "tags": ["search", "e-commerce", "tools", "hardware", "jordan"],
                    "entrypoint": f"{domain}/products/search/?q={{query}}"
                },
                {
                    "id": "browse-categories",
                    "name": "Browse Categories",
                    "description": "Browse product categories including power tools, hand tools, safety equipment, and more.",
                    "tags": ["browse", "categories", "catalog"],
                    "entrypoint": f"{domain}/products/"
                },
                {
                    "id": "new-arrivals",
                    "name": "New Arrivals",
                    "description": "View the latest products added to ESCO's catalog.",
                    "tags": ["new", "latest", "arrivals"],
                    "entrypoint": f"{domain}/products/new/"
                },
                {
                    "id": "best-sellers",
                    "name": "Best Sellers",
                    "description": "View the most popular and best-selling products.",
                    "tags": ["popular", "best-sellers", "trending"],
                    "entrypoint": f"{domain}/products/bestsellers/"
                },
                {
                    "id": "special-offers",
                    "name": "Special Offers",
                    "description": "View current discounts and special offers on tools and hardware.",
                    "tags": ["offers", "discounts", "deals", "sale"],
                    "entrypoint": f"{domain}/products/offers/"
                }
            ]
        }
        return JsonResponse(index)

    def _get_domain(self, request, settings):
        if settings.canonical_domain:
            return settings.canonical_domain.rstrip('/')
        return request.build_absolute_uri('/').rstrip('/')


class APICatalogView(View):

    def get(self, request):
        settings = SiteSettings.get_settings()
        domain = self._get_domain(request, settings)

        catalog = {
            "linkset": [
                {
                    "anchor": domain,
                    "service-doc": [
                        {
                            "href": f"{domain}/products/",
                            "type": "text/html",
                            "title": "Product Catalog"
                        }
                    ],
                    "search": [
                        {
                            "href": f"{domain}/products/search/?q={{query}}",
                            "type": "text/html",
                            "title": "Product Search"
                        }
                    ],
                    "describedby": [
                        {
                            "href": f"{domain}/sitemap.xml",
                            "type": "application/xml",
                            "title": "Sitemap"
                        }
                    ]
                }
            ]
        }
        return JsonResponse(catalog, content_type='application/linkset+json')

    def _get_domain(self, request, settings):
        if settings.canonical_domain:
            return settings.canonical_domain.rstrip('/')
        return request.build_absolute_uri('/').rstrip('/')
