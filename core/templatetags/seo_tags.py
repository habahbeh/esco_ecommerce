import json
from django import template
from django.db.models import Avg
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.translation import get_language
from django.conf import settings

register = template.Library()


@register.simple_tag(takes_context=True)
def canonical_url(context):
    request = context.get('request')
    if not request:
        return ''
    site_settings = context.get('site_settings')
    domain = ''
    if site_settings and site_settings.canonical_domain:
        domain = site_settings.canonical_domain.rstrip('/')
    else:
        domain = f"{request.scheme}://{request.get_host()}"
    path = request.path
    return mark_safe(f'<link rel="canonical" href="{escape(domain)}{escape(path)}">')


@register.simple_tag(takes_context=True)
def hreflang_tags(context):
    request = context.get('request')
    if not request:
        return ''
    site_settings = context.get('site_settings')
    if site_settings and site_settings.canonical_domain:
        domain = site_settings.canonical_domain.rstrip('/')
    else:
        domain = f"{request.scheme}://{request.get_host()}"
    path = request.path
    ar_path = path
    if path.startswith('/en/'):
        ar_path = path[3:] or '/'
    en_path = f'/en{path}' if not path.startswith('/en/') else path
    tags = [
        f'<link rel="alternate" hreflang="ar" href="{escape(domain)}{escape(ar_path)}">',
        f'<link rel="alternate" hreflang="en" href="{escape(domain)}{escape(en_path)}">',
        f'<link rel="alternate" hreflang="x-default" href="{escape(domain)}{escape(ar_path)}">',
    ]
    return mark_safe('\n    '.join(tags))


@register.simple_tag(takes_context=True)
def og_meta_tags(context, title='', description='', image='', obj_type='website', url=''):
    request = context.get('request')
    site_settings = context.get('site_settings')
    if not request:
        return ''

    domain = ''
    if site_settings and site_settings.canonical_domain:
        domain = site_settings.canonical_domain.rstrip('/')
    else:
        domain = f"{request.scheme}://{request.get_host()}"

    og_title = title or (getattr(site_settings, 'seo_title', '') or '') or (getattr(site_settings, 'site_name', '') or 'ESCO')
    og_desc = description or (getattr(site_settings, 'seo_description', '') or '') or (getattr(site_settings, 'site_description', '') or '')
    og_url = url or f"{domain}{request.path}"
    og_image = image
    if not og_image and site_settings:
        if hasattr(site_settings, 'og_image') and site_settings.og_image:
            try:
                og_image = f"{domain}{site_settings.og_image.url}"
            except ValueError:
                pass
        if not og_image and site_settings.logo:
            try:
                og_image = f"{domain}{site_settings.logo.url}"
            except ValueError:
                pass

    site_name = getattr(site_settings, 'site_name', '') or 'ESCO'

    tags = [
        f'<meta property="og:type" content="{escape(obj_type)}">',
        f'<meta property="og:title" content="{escape(og_title)}">',
        f'<meta property="og:description" content="{escape(og_desc)}">',
        f'<meta property="og:url" content="{escape(og_url)}">',
        f'<meta property="og:site_name" content="{escape(site_name)}">',
        f'<meta property="og:locale" content="ar_JO">',
        f'<meta property="og:locale:alternate" content="en_US">',
    ]
    if og_image:
        tags.append(f'<meta property="og:image" content="{escape(og_image)}">')
        tags.append(f'<meta property="og:image:width" content="1200">')
        tags.append(f'<meta property="og:image:height" content="630">')

    tags.extend([
        f'<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{escape(og_title)}">',
        f'<meta name="twitter:description" content="{escape(og_desc)}">',
    ])
    if og_image:
        tags.append(f'<meta name="twitter:image" content="{escape(og_image)}">')

    return mark_safe('\n    '.join(tags))


@register.simple_tag(takes_context=True)
def jsonld_organization(context):
    site_settings = context.get('site_settings')
    request = context.get('request')
    if not site_settings or not request:
        return ''
    if site_settings and hasattr(site_settings, 'enable_structured_data') and not site_settings.enable_structured_data:
        return ''

    domain = ''
    if site_settings.canonical_domain:
        domain = site_settings.canonical_domain.rstrip('/')
    else:
        domain = f"{request.scheme}://{request.get_host()}"

    data = {
        "@context": "https://schema.org",
        "@type": ["HardwareStore", "Organization"],
        "name": site_settings.site_name or "ESCO",
        "alternateName": [
            "شركة المخازن الهندسية",
            "المخازن الهندسية",
            "شركة المخازن الهندسية للتجارة والصناعة",
            "Engineering Stores Company",
            "ESCO Jordan",
        ],
        "url": domain,
        "description": site_settings.site_description or (
            "Engineering Stores Company (ESCO) - Jordan's largest industrial tools and hardware store"
            if get_language() == 'en' else
            "شركة المخازن الهندسية (ESCO) - أكبر متجر للعدد الصناعية والأدوات الهندسية في الأردن"
        ),
        "foundingDate": "1994",
        "currenciesAccepted": "JOD",
        "paymentAccepted": "Cash, Credit Card",
        "priceRange": "$$",
        "knowsLanguage": ["ar", "en"],
    }
    if site_settings.logo:
        data["logo"] = f"{domain}{site_settings.logo.url}"
    contact = {}
    if site_settings.phone:
        contact["telephone"] = site_settings.phone
    if site_settings.email:
        contact["email"] = site_settings.email
    if contact:
        contact["@type"] = "ContactPoint"
        contact["contactType"] = "customer service"
        contact["availableLanguage"] = ["Arabic", "English"]
        data["contactPoint"] = contact
    if site_settings.address:
        data["address"] = {
            "@type": "PostalAddress",
            "addressLocality": "Amman",
            "addressRegion": "Amman",
            "addressCountry": "JO",
            "streetAddress": site_settings.address,
        }
        data["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": "31.9539",
            "longitude": "35.9106",
        }
        data["areaServed"] = {
            "@type": "Country",
            "name": "Jordan",
        }
    social = []
    for field in ['facebook', 'twitter', 'instagram', 'linkedin']:
        url = getattr(site_settings, field, '')
        if url:
            social.append(url)
    if social:
        data["sameAs"] = social

    return mark_safe(f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>')


@register.simple_tag(takes_context=True)
def jsonld_product(context, product):
    site_settings = context.get('site_settings')
    request = context.get('request')
    if not product or not request:
        return ''
    if site_settings and hasattr(site_settings, 'enable_structured_data') and not site_settings.enable_structured_data:
        return ''

    domain = ''
    if site_settings and site_settings.canonical_domain:
        domain = site_settings.canonical_domain.rstrip('/')
    else:
        domain = f"{request.scheme}://{request.get_host()}"

    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "url": f"{domain}{product.get_absolute_url()}",
    }
    if product.description:
        from django.utils.html import strip_tags
        data["description"] = strip_tags(product.description)[:500]
    if product.sku:
        data["sku"] = product.sku
    if product.brand:
        data["brand"] = {"@type": "Brand", "name": product.brand.name}

    images = []
    if hasattr(product, 'images'):
        for img in product.images.all()[:5]:
            images.append(f"{domain}{img.image.url}")
    if images:
        data["image"] = images

    if product.base_price:
        offer = {
            "@type": "Offer",
            "priceCurrency": "JOD",
            "price": str(product.get_final_price() if hasattr(product, 'get_final_price') else product.base_price),
            "url": f"{domain}{product.get_absolute_url()}",
            "itemCondition": "https://schema.org/NewCondition",
        }
        if product.stock_quantity and product.stock_quantity > 0:
            offer["availability"] = "https://schema.org/InStock"
        else:
            offer["availability"] = "https://schema.org/OutOfStock"
        data["offers"] = offer

    if product.category:
        data["category"] = product.category.name

    if hasattr(product, 'reviews'):
        reviews = product.reviews.filter(is_approved=True) if hasattr(product.reviews, 'filter') else []
        if reviews:
            avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
            if avg_rating:
                data["aggregateRating"] = {
                    "@type": "AggregateRating",
                    "ratingValue": str(round(avg_rating, 1)),
                    "reviewCount": str(reviews.count()),
                }

    return mark_safe(f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>')


@register.simple_tag(takes_context=True)
def jsonld_breadcrumb(context, breadcrumbs):
    request = context.get('request')
    site_settings = context.get('site_settings')
    if not breadcrumbs or not request:
        return ''
    if site_settings and hasattr(site_settings, 'enable_structured_data') and not site_settings.enable_structured_data:
        return ''

    domain = ''
    if site_settings and site_settings.canonical_domain:
        domain = site_settings.canonical_domain.rstrip('/')
    else:
        domain = f"{request.scheme}://{request.get_host()}"

    items = []
    for i, crumb in enumerate(breadcrumbs, 1):
        item = {
            "@type": "ListItem",
            "position": i,
            "name": crumb.get('name', ''),
        }
        if crumb.get('url'):
            item["item"] = f"{domain}{crumb['url']}"
        items.append(item)

    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }
    return mark_safe(f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>')


@register.simple_tag(takes_context=True)
def jsonld_website(context):
    site_settings = context.get('site_settings')
    request = context.get('request')
    if not site_settings or not request:
        return ''
    if hasattr(site_settings, 'enable_structured_data') and not site_settings.enable_structured_data:
        return ''

    domain = ''
    if site_settings.canonical_domain:
        domain = site_settings.canonical_domain.rstrip('/')
    else:
        domain = f"{request.scheme}://{request.get_host()}"

    data = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": site_settings.site_name or "ESCO",
        "url": domain,
        "inLanguage": ["ar", "en"],
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{domain}/products/search/?q={{search_term_string}}",
            },
            "query-input": "required name=search_term_string",
        },
    }
    return mark_safe(f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>')


@register.simple_tag(takes_context=True)
def jsonld_local_business(context):
    site_settings = context.get('site_settings')
    request = context.get('request')
    if not site_settings or not request:
        return ''
    if hasattr(site_settings, 'enable_structured_data') and not site_settings.enable_structured_data:
        return ''

    from django.core.cache import cache as _cache
    lang = get_language() or 'ar'
    cache_key = f'jsonld_local_business_{lang}'
    cached = _cache.get(cache_key)
    if cached is not None:
        return mark_safe(cached)

    domain = ''
    if site_settings.canonical_domain:
        domain = site_settings.canonical_domain.rstrip('/')
    else:
        domain = f"{request.scheme}://{request.get_host()}"

    from core.models import Branch
    branches = list(Branch.objects.filter(is_active=True))
    if not branches:
        _cache.set(cache_key, '', 600)
        return ''

    city_name = "Amman" if lang == 'en' else "عمان"
    locations = []
    for branch in branches:
        loc = {
            "@type": "HardwareStore",
            "name": f"ESCO - {branch.name}",
            "telephone": branch.phone or (site_settings.phone if site_settings else ''),
            "address": {
                "@type": "PostalAddress",
                "streetAddress": branch.address,
                "addressLocality": city_name,
                "addressRegion": city_name,
                "addressCountry": "JO",
            },
            "geo": {
                "@type": "GeoCoordinates",
                "latitude": "31.9539",
                "longitude": "35.9106",
            },
            "url": domain,
            "priceRange": "$$",
            "currenciesAccepted": "JOD",
            "paymentAccepted": "Cash, Credit Card, Bank Transfer",
        }
        if branch.working_hours:
            loc["openingHours"] = branch.working_hours
        if site_settings and site_settings.logo:
            loc["image"] = f"{domain}{site_settings.logo.url}"
        locations.append(loc)

    if len(locations) == 1:
        data = locations[0]
        data["@context"] = "https://schema.org"
    else:
        data = {
            "@context": "https://schema.org",
            "@type": "HardwareStore",
            "name": site_settings.site_name or "ESCO",
            "url": domain,
            "department": locations,
        }

    html = f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'
    _cache.set(cache_key, html, 600)
    return mark_safe(html)


@register.simple_tag(takes_context=True)
def google_analytics(context):
    site_settings = context.get('site_settings')
    if not site_settings or not hasattr(site_settings, 'google_analytics_id'):
        return ''
    ga_id = site_settings.google_analytics_id
    if not ga_id:
        return ''
    script = f'''<script async src="https://www.googletagmanager.com/gtag/js?id={escape(ga_id)}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{escape(ga_id)}');</script>'''
    return mark_safe(script)


@register.simple_tag(takes_context=True)
def google_search_console(context):
    site_settings = context.get('site_settings')
    if not site_settings or not hasattr(site_settings, 'google_search_console_code'):
        return ''
    code = site_settings.google_search_console_code
    if not code:
        return ''
    return mark_safe(f'<meta name="google-site-verification" content="{escape(code)}">')
