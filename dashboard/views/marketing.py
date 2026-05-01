import json
import os
import re
import requests
from django.db.models import Q
from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from dashboard.mixins import DashboardAccessMixin, SuperuserRequiredMixin
from products.models import Product, Category, Brand
from core.models import SiteSettings
from accounts.models import UserActivity


PLATFORM_PROMPTS = {
    'facebook': {
        'ar': 'اكتب منشور فيسبوك تسويقي احترافي باللغة العربية',
        'en': 'Write a professional Facebook marketing post in English',
        'max_length': 'up to 300 words',
    },
    'instagram': {
        'ar': 'اكتب وصف انستغرام تسويقي احترافي باللغة العربية مع هاشتاقات مناسبة',
        'en': 'Write a professional Instagram caption in English with relevant hashtags',
        'max_length': 'up to 200 words with 10-15 hashtags',
    },
    'linkedin': {
        'ar': 'اكتب منشور لينكد إن تسويقي احترافي باللغة العربية',
        'en': 'Write a professional LinkedIn marketing post in English',
        'max_length': 'up to 250 words, professional tone',
    },
    'twitter': {
        'ar': 'اكتب تغريدة تسويقية احترافية باللغة العربية',
        'en': 'Write a professional marketing tweet in English',
        'max_length': 'under 280 characters',
    },
    'whatsapp': {
        'ar': 'اكتب رسالة واتساب تسويقية احترافية باللغة العربية',
        'en': 'Write a professional WhatsApp marketing message in English',
        'max_length': 'up to 150 words, casual but professional',
    },
}

CONTENT_TYPES = {
    'promotion': {
        'ar': 'عرض ترويجي أو خصم',
        'en': 'Promotional offer or discount',
    },
    'new_arrival': {
        'ar': 'منتج جديد وصل حديثاً',
        'en': 'New product arrival announcement',
    },
    'feature': {
        'ar': 'تسليط الضوء على مميزات المنتج',
        'en': 'Product feature highlight',
    },
    'testimonial': {
        'ar': 'شهادة عميل أو مراجعة',
        'en': 'Customer testimonial or review style',
    },
    'educational': {
        'ar': 'محتوى تعليمي عن المنتج واستخداماته',
        'en': 'Educational content about the product and its uses',
    },
    'brand_story': {
        'ar': 'قصة العلامة التجارية',
        'en': 'Brand story and heritage',
    },
}


DEFAULT_MODEL = 'openrouter/free'

FREE_MODELS = [
    {'id': 'openrouter/free', 'name': 'Auto (Best Free Model)'},
    {'id': 'nvidia/nemotron-3-super-120b-a12b:free', 'name': 'NVIDIA Nemotron 3 Super 120B (Free)'},
    {'id': 'nvidia/nemotron-3-nano-30b-a3b:free', 'name': 'NVIDIA Nemotron 3 Nano 30B (Free)'},
    {'id': 'google/gemma-4-31b-it:free', 'name': 'Google Gemma 4 31B (Free)'},
    {'id': 'google/gemma-4-26b-a4b-it:free', 'name': 'Google Gemma 4 26B (Free)'},
    {'id': 'minimax/minimax-m2.5:free', 'name': 'MiniMax M2.5 (Free)'},
    {'id': 'arcee-ai/trinity-large-preview:free', 'name': 'Arcee Trinity Large (Free)'},
]


def _get_marketing_settings():
    try:
        site = SiteSettings.get_settings()
        api_key = getattr(site, 'gemini_api_key', '') or ''
        model = getattr(site, 'marketing_model', '') or DEFAULT_MODEL
        return api_key, model
    except Exception:
        return '', DEFAULT_MODEL


def _build_product_context(product):
    ctx = {
        'name_ar': product.name,
        'name_en': product.name_en or product.name,
        'category': product.category.name if product.category else '',
        'category_en': getattr(product.category, 'name_en', '') if product.category else '',
        'brand': product.brand.name if product.brand else '',
        'brand_en': getattr(product.brand, 'name_en', '') if product.brand else '',
        'description': product.short_description or (product.description or '')[:300],
        'price': str(product.base_price) if product.base_price else '',
        'sku': product.sku,
    }
    if product.specifications:
        specs = product.specifications
        if isinstance(specs, str):
            try:
                specs = json.loads(specs)
            except Exception:
                pass
        ctx['specifications'] = specs
    if product.features:
        ctx['features'] = product.features
    return ctx


def _build_category_context(category):
    return {
        'name_ar': category.name,
        'name_en': category.name_en or category.name,
        'description': category.description or '',
        'products_count': category.products.count(),
    }


def _build_brand_context(brand):
    return {
        'name_ar': brand.name,
        'name_en': brand.name_en or brand.name,
        'description': brand.description or '',
        'country': brand.country or '',
        'website': brand.website or '',
        'products_count': brand.products.count(),
    }


def _generate_content(api_key, model, item_context, platform, content_type, language, custom_instructions=''):
    platform_info = PLATFORM_PROMPTS.get(platform, PLATFORM_PROMPTS['facebook'])
    type_info = CONTENT_TYPES.get(content_type, CONTENT_TYPES['promotion'])

    lang_key = language if language in ('ar', 'en') else 'ar'

    prompt = f"""You are a real social media manager at ESCO, an industrial equipment and supplies company in Jordan (esco.jo).
Write as a real person would — natural, conversational, and authentic. NOT robotic or AI-generated.

{platform_info[lang_key]}

Content type: {type_info[lang_key]}
Platform: {platform}
Length: {platform_info['max_length']}

Product/Item Information:
{json.dumps(item_context, ensure_ascii=False, indent=2)}

Important rules:
- Write ONLY in {'Arabic' if lang_key == 'ar' else 'English'}
- Sound like a real human wrote this, not AI — use casual professional tone, vary sentence length, be genuine
- DO NOT use any markdown formatting — no **, no ##, no *, no bullet points with dashes. Write plain text only
- Include a call to action naturally (not forced)
- Use relevant emojis sparingly and naturally
- Company name: "ESCO" or "إسكو"
- Website: esco.jo
- Avoid generic filler phrases like "Don't miss out!", "Hurry up!", "Act now!" — be creative instead
{"- " + custom_instructions if custom_instructions else ""}

Write the post content only. Plain text, no formatting, no labels, no explanations."""

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://esco.jo",
        "X-Title": "ESCO Marketing",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 1024,
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
    except requests.exceptions.Timeout:
        return {'success': False, 'error': str(_('انتهت مهلة الاتصال بالخادم. حاول مرة أخرى.'))}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': str(_('خطأ في الاتصال. تحقق من الاتصال بالإنترنت.'))}
    except requests.exceptions.RequestException:
        return {'success': False, 'error': str(_('خطأ غير متوقع في الاتصال.'))}

    try:
        data = resp.json()
    except ValueError:
        return {'success': False, 'error': str(_('رد غير صالح من الخادم.'))}

    if resp.status_code != 200:
        error_msg = data.get('error', {}).get('message', str(_('خطأ غير معروف')))
        return {'success': False, 'error': error_msg}

    try:
        text = data['choices'][0]['message']['content']
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\-\•]\s+', '', text, flags=re.MULTILINE)
        return {'success': True, 'content': text.strip()}
    except (KeyError, IndexError):
        return {'success': False, 'error': str(_('لم يتم إنشاء محتوى. حاول مرة أخرى.'))}


class MarketingDashboardView(DashboardAccessMixin, View):
    def get(self, request):
        categories = Category.objects.filter(
            is_active=True, parent=None
        ).order_by('sort_order', 'name')

        brands = Brand.objects.filter(is_active=True).order_by('name')

        api_key, current_model = _get_marketing_settings()

        context = {
            'categories': categories,
            'brands': brands,
            'platforms': PLATFORM_PROMPTS,
            'content_types': CONTENT_TYPES,
            'has_api_key': bool(api_key),
            'free_models': FREE_MODELS,
            'current_model': current_model,
            'page_title': _('التسويق'),
        }
        return render(request, 'dashboard/marketing/index.html', context)


class MarketingGenerateView(DashboardAccessMixin, View):
    def post(self, request):
        api_key, model = _get_marketing_settings()
        if not api_key:
            return JsonResponse({
                'success': False,
                'error': str(_('مفتاح API غير مُعد. الرجاء إضافته من إعدادات التسويق.'))
            })

        item_type = request.POST.get('item_type', 'product')
        item_id = request.POST.get('item_id', '').strip()
        platform = request.POST.get('platform', 'facebook')
        content_type = request.POST.get('content_type', 'promotion')
        language = request.POST.get('language', 'ar')
        custom_instructions = request.POST.get('custom_instructions', '')[:500]
        selected_model = request.POST.get('model', '').strip()
        if selected_model:
            model = selected_model

        if not item_id:
            return JsonResponse({'success': False, 'error': str(_('يرجى اختيار عنصر أولاً'))})

        if platform not in PLATFORM_PROMPTS:
            platform = 'facebook'
        if content_type not in CONTENT_TYPES:
            content_type = 'promotion'

        image_url = ''
        item_name = ''

        if item_type == 'product':
            try:
                item = Product.objects.select_related('category', 'brand').prefetch_related('images').get(pk=item_id)
                item_context = _build_product_context(item)
                item_name = item.name
                primary_img = item.images.filter(is_primary=True).first() or item.images.first()
                if primary_img and primary_img.image:
                    image_url = primary_img.image.url
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'error': str(_('المنتج غير موجود'))})

        elif item_type == 'category':
            try:
                item = Category.objects.get(pk=item_id)
                item_context = _build_category_context(item)
                item_name = item.name
                if item.image:
                    image_url = item.image.url
            except Category.DoesNotExist:
                return JsonResponse({'success': False, 'error': str(_('الفئة غير موجودة'))})

        elif item_type == 'brand':
            try:
                item = Brand.objects.get(pk=item_id)
                item_context = _build_brand_context(item)
                item_name = item.name
                if item.logo:
                    image_url = item.logo.url
            except Brand.DoesNotExist:
                return JsonResponse({'success': False, 'error': str(_('العلامة التجارية غير موجودة'))})
        else:
            return JsonResponse({'success': False, 'error': str(_('نوع العنصر غير صالح'))})

        result = _generate_content(
            api_key, model, item_context, platform, content_type, language, custom_instructions
        )
        if result.get('success'):
            if image_url:
                full_url = request.build_absolute_uri(image_url)
                relative_path = image_url.replace(settings.MEDIA_URL, '', 1).replace('/', os.sep)
                if settings.DEBUG and not os.path.exists(
                    os.path.join(settings.MEDIA_ROOT, relative_path)
                ):
                    full_url = f"https://esco.jo{image_url}"
                result['image_url'] = full_url
            else:
                result['image_url'] = ''
            result['item_name'] = item_name
            UserActivity.objects.create(
                user=request.user,
                activity_type='marketing_generate',
                description=f'Generated {content_type} content for {platform} - {item_type}: {item_name}',
                object_id=str(item_id),
                content_type=f'products.{item_type}',
                ip_address=request.META.get('REMOTE_ADDR'),
            )
        return JsonResponse(result)


class MarketingSettingsView(SuperuserRequiredMixin, View):
    def get(self, request):
        api_key, current_model = _get_marketing_settings()
        context = {
            'api_key': api_key,
            'api_key_masked': ('*' * (len(api_key) - 4) + api_key[-4:]) if len(api_key) > 4 else '',
            'current_model': current_model,
            'free_models': FREE_MODELS,
            'page_title': _('إعدادات التسويق'),
        }
        return render(request, 'dashboard/marketing/settings.html', context)

    def post(self, request):
        api_key = request.POST.get('api_key', '').strip()
        model = request.POST.get('marketing_model', '').strip() or DEFAULT_MODEL
        try:
            site = SiteSettings.get_settings()
            site.gemini_api_key = api_key
            site.marketing_model = model
            site.save(update_fields=['gemini_api_key', 'marketing_model'])
            return JsonResponse({'success': True, 'message': str(_('تم حفظ الإعدادات بنجاح'))})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class MarketingTestConnectionView(SuperuserRequiredMixin, View):
    def post(self, request):
        api_key = request.POST.get('api_key', '').strip()
        model = request.POST.get('model', '').strip() or DEFAULT_MODEL

        if not api_key:
            return JsonResponse({'success': False, 'error': str(_('يرجى إدخال مفتاح API'))})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://esco.jo",
            "X-Title": "ESCO Marketing",
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Say 'Connection successful' in one line."}],
            "max_tokens": 50,
        }

        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload, headers=headers, timeout=30
            )
        except requests.exceptions.RequestException:
            return JsonResponse({'success': False, 'error': str(_('خطأ في الاتصال بالخادم'))})

        try:
            data = resp.json()
        except ValueError:
            return JsonResponse({'success': False, 'error': str(_('رد غير صالح من الخادم'))})

        if resp.status_code != 200:
            error_msg = data.get('error', {}).get('message', str(_('خطأ غير معروف')))
            return JsonResponse({'success': False, 'error': error_msg})

        return JsonResponse({'success': True, 'message': str(_('الاتصال ناجح!'))})


class MarketingProductSearchView(DashboardAccessMixin, View):
    def get(self, request):
        q = request.GET.get('q', '').strip()
        if len(q) < 2:
            return JsonResponse({'results': []})

        products = Product.objects.filter(
            is_active=True,
            status='published',
        ).filter(
            Q(name__icontains=q) |
            Q(name_en__icontains=q) |
            Q(sku__icontains=q)
        ).select_related('category', 'brand').prefetch_related('images')[:10]

        results = []
        for p in products:
            img_url = ''
            first_img = p.images.first()
            if first_img and first_img.image:
                img_url = first_img.image.url
            results.append({
                'id': str(p.pk),
                'name': p.name,
                'name_en': p.name_en or '',
                'sku': p.sku,
                'category': p.category.name if p.category else '',
                'brand': p.brand.name if p.brand else '',
                'image': img_url,
            })

        return JsonResponse({'results': results})
