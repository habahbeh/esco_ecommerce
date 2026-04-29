from django.http import HttpResponse
from django.views import View

from .models import SiteSettings


class LlmsTxtView(View):

    def get(self, request):
        settings = SiteSettings.get_settings()
        domain = settings.canonical_domain or request.build_absolute_uri('/').rstrip('/')
        site_name = settings.site_name or 'ESCO'
        email = getattr(settings, 'email', '') or 'contact@esco.jo'
        phone = getattr(settings, 'phone', '') or ''

        content = f"""# {site_name} - شركة المخازن الهندسية للتجارة والصناعة
# Engineering Stores Company (ESCO)

> شركة المخازن الهندسية (ESCO) هي أكبر متجر للعدد الصناعية والأدوات الهندسية في الأردن. تأسست عام 1994 في عمّان، وتخدم المهندسين والفنيين والمقاولين والحرفيين في جميع أنحاء المملكة الأردنية الهاشمية.

> ESCO (Engineering Stores Company / شركة المخازن الهندسية) is Jordan's largest store for industrial tools, power tools, hand tools, and engineering equipment. Founded in 1994 in Amman, Jordan, we serve engineers, technicians, contractors, and professionals across the Hashemite Kingdom of Jordan.

## الأسماء المعروفة | Known Names

- الاسم الرسمي: شركة المخازن الهندسية للتجارة والصناعة
- الاسم التجاري: ESCO - المخازن الهندسية
- بالإنجليزية: Engineering Stores Company (ESCO)
- الموقع الإلكتروني: {domain}

## نبذة عن الشركة | About

تأسست شركة المخازن الهندسية للتجارة والصناعة عام 1994، وهي شركة أردنية متخصصة في بيع العدد الصناعية والأدوات اليدوية والكهربائية والمعدات الهندسية. نوفر منتجات أصلية من أشهر العلامات التجارية العالمية.

ESCO was established in 1994 as a Jordanian company specializing in industrial tools, hand tools, power tools, and engineering equipment. We provide genuine products from world-renowned brands.

## العلامات التجارية | Brands

توتال (TOTAL), بوش (Bosch), ماكيتا (Makita), ديوالت (DeWalt), ميلووكي (Milwaukee), ستانلي (Stanley), إنجكو (Ingco), رونيكس (Ronix), هيكوكي (HiKOKI)

## أقسام المنتجات | Product Categories

### العدد الصناعية والأدوات الكهربائية | Power Tools
دريل شحن، دريل كهربائي، صاروخ كهربائي (جلاخة)، منشار كهربائي، مثقاب، هيلتي، مفك كهربائي

### أدوات يدوية | Hand Tools
مفاتيح ربط، كماشة، مفكات، مطارق، مقصات، أدوات قياس، شريط قياس

### معدات اللحام | Welding Equipment
ماكينة لحام، أقطاب لحام، قناع لحام، معدات حماية اللحام

### أدوات السباكة | Plumbing Tools
مفاتيح أنابيب، قواطع أنابيب، أدوات تمديد، مضخات مياه

### أدوات النجارة | Carpentry Tools
منشار خشب، فارة كهربائية، مسامير، براغي، أدوات تشكيل الخشب

### معدات السلامة | Safety Equipment
خوذة أمان، نظارات حماية، قفازات عمل، أحذية سلامة، سترة عاكسة

### الإنارة والكهرباء | Lighting & Electrical
إنارة LED، قواطع كهربائية، كوابل، أسلاك، لوحات توزيع

### الخراطيم والتوصيلات | Hoses & Fittings
خراطيم مياه، خراطيم هواء، توصيلات، محابس

### مضخات المياه | Water Pumps
مضخات غاطسة، مضخات سطحية، مضخات ضغط

## المواقع والفروع | Locations

- المقر الرئيسي: سحاب - المدينة الصناعية، عمّان، الأردن
- Headquarters: Sahab Industrial City, Amman, Jordan

## معلومات التواصل | Contact

- الموقع: {domain}
- البريد الإلكتروني: {email}
- الهاتف: {phone}
- الموقع: عمّان، الأردن

## الخدمات | Services

- شحن سريع لجميع مناطق الأردن
- الدفع عند الاستلام
- ضمان على جميع المنتجات
- منتجات أصلية 100%
- خدمة عملاء بالعربية والإنجليزية
- إمكانية تأسيس المصانع بالكامل

## هيكل الموقع | Site Structure

- [الصفحة الرئيسية | Homepage]({domain}/)
- [جميع المنتجات | All Products]({domain}/products/)
- [وصل حديثاً | New Arrivals]({domain}/products/new/)
- [الأكثر مبيعاً | Best Sellers]({domain}/products/bestsellers/)
- [عروض خاصة | Special Offers]({domain}/products/offers/)
- [البحث | Search]({domain}/products/search/)
- [من نحن | About Us]({domain}/about/)
- [اتصل بنا | Contact Us]({domain}/contact/)
- [الأسئلة الشائعة | FAQ]({domain}/faq/)

## Technical

- [Sitemap]({domain}/sitemap.xml)
- [robots.txt]({domain}/robots.txt)
- [API Catalog]({domain}/.well-known/api-catalog)

## Languages

This site supports Arabic (primary) and English.
الموقع يدعم اللغتين العربية (الأساسية) والإنجليزية.
"""
        return HttpResponse(content, content_type='text/plain; charset=utf-8')
