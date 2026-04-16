"""
Seed dummy data for homepage slider, brands, categories, products, variants, images.
Idempotent: re-running wipes previously seeded dummy records (by DUM- marker) and recreates them.
Run:  python manage.py seed_dummy_data
"""
import io
import random
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify

from PIL import Image, ImageDraw, ImageFont

from core.models import SliderItem
from products.models import (
    Brand, Category, Product, ProductImage, ProductVariant,
)

User = get_user_model()

DUMMY_SKU_PREFIX = "DUM-"
DUMMY_SLUG_PREFIX = "dum-"


# ---------- image generation ----------
PALETTE = [
    (230, 57, 70), (29, 53, 87), (69, 123, 157), (168, 218, 220),
    (244, 162, 97), (42, 157, 143), (233, 196, 106), (231, 111, 81),
    (38, 70, 83), (106, 76, 147), (52, 152, 219), (22, 160, 133),
]


def _font(size):
    for path in ("arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def make_image(text, w=800, h=800, seed=0):
    rnd = random.Random(seed)
    bg = rnd.choice(PALETTE)
    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)
    # diagonal stripes for visual interest
    stripe = tuple(min(255, c + 25) for c in bg)
    for i in range(-h, w, 60):
        draw.polygon([(i, 0), (i + 30, 0), (i + 30 + h, h), (i + h, h)], fill=stripe)
    font_size = max(28, min(w, h) // 10)
    font = _font(font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.rectangle([(w // 2 - tw // 2 - 20, h // 2 - th // 2 - 12),
                    (w // 2 + tw // 2 + 20, h // 2 + th // 2 + 12)],
                   fill=(0, 0, 0, 180))
    draw.text((w // 2 - tw // 2, h // 2 - th // 2), text, font=font, fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def img_file(name, text, w=800, h=800, seed=0):
    return ContentFile(make_image(text, w, h, seed), name=f"{name}.jpg")


# ---------- static catalog data ----------
SLIDES = [
    # (title_ar, subtitle_ar, description_ar, title_en, subtitle_en, description_en, btn_ar, btn_en, url)
    ("عروض الربيع 2026", "أسعار لا تُقاوم", "خصومات تصل إلى 40% على مختارات من المنتجات",
     "Spring Deals 2026", "Unbeatable Prices", "Up to 40% off on selected products",
     "تسوق الآن", "Shop Now", "/products/"),
    ("أدوات كهربائية", "للمحترفين والهواة", "أدوات احترافية بجودة عالية وضمان سنتين",
     "Power Tools", "For Pros & Hobbyists", "Professional-grade tools with a 2-year warranty",
     "اكتشف", "Explore", "/products/?category=power-tools"),
    ("أجهزة منزلية", "كل ما يحتاجه منزلك", "تشكيلة واسعة من أفضل العلامات العالمية",
     "Home Appliances", "Everything Your Home Needs", "Wide selection from top global brands",
     "تصفح", "Browse", "/products/?category=home-appliances"),
    ("إضاءة LED", "أضئ منزلك بكفاءة", "توفير في الطاقة يصل إلى 80% مع LED",
     "LED Lighting", "Light Up Efficiently", "Save up to 80% on energy with LED",
     "تسوق الآن", "Shop Now", "/products/?category=lighting"),
    ("أدوات المطبخ", "جودة عالية، أسعار منافسة", "كل ما يلزم لمطبخ عصري ومتكامل",
     "Kitchen Essentials", "High Quality, Great Prices", "Everything for a modern, complete kitchen",
     "اكتشف", "Discover", "/products/?category=kitchen"),
]

BRANDS = [
    ("بوش", "Bosch", "ألمانيا", "Germany"),
    ("بلاك آند ديكر", "Black & Decker", "الولايات المتحدة", "USA"),
    ("فيليبس", "Philips", "هولندا", "Netherlands"),
    ("سامسونج", "Samsung", "كوريا الجنوبية", "South Korea"),
    ("ال جي", "LG", "كوريا الجنوبية", "South Korea"),
    ("ماكيتا", "Makita", "اليابان", "Japan"),
    ("ديوالت", "DeWalt", "الولايات المتحدة", "USA"),
    ("تيفال", "Tefal", "فرنسا", "France"),
]

# (name_ar, name_en, [(sub_ar, sub_en), ...])
CATEGORIES = [
    ("أدوات كهربائية", "Power Tools", [("مثاقب", "Drills"), ("مناشير", "Saws"), ("صنفرة", "Sanders")]),
    ("أجهزة منزلية", "Home Appliances", [("غسالات", "Washers"), ("ثلاجات", "Refrigerators")]),
    ("أدوات المطبخ", "Kitchen", [("خلاطات", "Blenders"), ("أفران", "Ovens"), ("غلايات", "Kettles")]),
    ("صوتيات", "Audio", [("سماعات", "Headphones"), ("مكبرات", "Speakers")]),
    ("إضاءة", "Lighting", [("LED", "LED Bulbs"), ("ثريات", "Chandeliers")]),
    ("حدائق", "Garden", [("قصافات", "Trimmers"), ("خراطيم", "Hoses")]),
]

# (name_ar, name_en, cat_slug_en, brand_idx, base_price, short_ar, short_en, variants)
# variants: list of (name_ar, name_en, attrs, price_delta) or None
PRODUCTS = [
    ("مثقاب لاسلكي 18 فولت", "Cordless Drill 18V", "drills", 0, 129.00,
     "مثقاب قوي بعزم دوران عالي", "Powerful drill with high torque",
     [("أزرق", "Blue", {"color": "blue"}, 0), ("أحمر", "Red", {"color": "red"}, 5)]),
    ("منشار دائري 7\"", "Circular Saw 7\"", "saws", 6, 189.50,
     "منشار محترف للقطع الدقيق", "Professional saw for precise cuts", None),
    ("صنفرة مدارية", "Orbital Sander", "sanders", 5, 89.00,
     "صنفرة عالية الأداء", "High-performance sander", None),
    ("غسالة أوتوماتيك 8 كغم", "Washing Machine 8kg", "washers", 3, 329.00,
     "غسالة موفرة للطاقة", "Energy-efficient washer",
     [("أبيض", "White", {"color": "white"}, 0), ("فضي", "Silver", {"color": "silver"}, 20)]),
    ("ثلاجة بابين 450 لتر", "Double-Door Fridge 450L", "refrigerators", 4, 549.00,
     "ثلاجة بسعة كبيرة", "Large-capacity refrigerator", None),
    ("خلاط كهربائي 600 واط", "Blender 600W", "blenders", 7, 45.00,
     "خلاط متعدد السرعات", "Multi-speed blender",
     [("أسود", "Black", {"color": "black"}, 0), ("أبيض", "White", {"color": "white"}, 0)]),
    ("فرن كهربائي 45 لتر", "Electric Oven 45L", "ovens", 7, 79.00,
     "فرن مع شواية", "Oven with grill", None),
    ("غلاية كهربائية 1.7 لتر", "Electric Kettle 1.7L", "kettles", 2, 22.50,
     "غلاية سريعة الغليان", "Fast-boil kettle", None),
    ("سماعات بلوتوث لاسلكية", "Wireless Bluetooth Headphones", "headphones", 3, 49.99,
     "صوت نقي وبطارية تدوم طويلاً", "Crisp sound, long battery",
     [("أسود", "Black", {"color": "black"}, 0),
      ("أبيض", "White", {"color": "white"}, 0),
      ("أحمر", "Red", {"color": "red"}, 3)]),
    ("مكبر صوت محمول", "Portable Speaker", "speakers", 2, 39.00,
     "مكبر صوت مقاوم للماء", "Water-resistant speaker", None),
    ("مصباح LED 9 واط", "LED Bulb 9W", "led-bulbs", 2, 3.50,
     "موفر للطاقة", "Energy-saving",
     [("أبيض بارد", "Cool White", {"temp": "6500K"}, 0),
      ("أبيض دافئ", "Warm White", {"temp": "3000K"}, 0)]),
    ("ثريا حديثة", "Modern Chandelier", "chandeliers", 2, 145.00,
     "تصميم عصري أنيق", "Modern elegant design", None),
    ("قصافة عشب كهربائية", "Electric Grass Trimmer", "trimmers", 1, 65.00,
     "قصافة خفيفة الوزن", "Lightweight trimmer", None),
    ("خرطوم حديقة 20م", "Garden Hose 20m", "hoses", 1, 18.00,
     "خرطوم مرن ومقاوم", "Flexible, durable hose", None),
    ("مثقاب صدم 850 واط", "Impact Drill 850W", "drills", 0, 95.00,
     "للاستخدام الشاق", "Heavy-duty use", None),
    ("منشار تخريم", "Jigsaw", "saws", 5, 72.00,
     "منشار دقيق للقطع المنحني", "Precision jigsaw for curves", None),
    ("مكيف سبليت 1 طن", "Split AC 1-Ton", "refrigerators", 4, 399.00,
     "تبريد سريع وهادئ", "Fast, quiet cooling", None),
    ("مكواة بخار", "Steam Iron", "kettles", 2, 28.00,
     "مكواة قوية بالبخار", "Powerful steam iron", None),
    ("محمصة خبز", "Toaster", "blenders", 7, 32.00,
     "محمصة بشريحتين", "Two-slice toaster",
     [("فضي", "Silver", {"color": "silver"}, 0), ("أسود", "Black", {"color": "black"}, 2)]),
    ("سماعات رياضية", "Sport Earbuds", "headphones", 3, 29.99,
     "مقاومة للعرق", "Sweat-resistant", None),
]


class Command(BaseCommand):
    help = "Seed dummy catalog data (sliders, brands, categories, products, variants, images)."

    def add_arguments(self, parser):
        parser.add_argument("--keep", action="store_true", help="Do not wipe existing dummy data first.")

    @transaction.atomic
    def handle(self, *args, **opts):
        if not opts["keep"]:
            self._wipe()

        admin = self._get_admin()
        self._seed_sliders()
        brands = self._seed_brands()
        cats = self._seed_categories()
        self._seed_products(cats, brands, admin)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded: {SliderItem.objects.count()} slides, "
            f"{Brand.objects.count()} brands, {Category.objects.count()} categories, "
            f"{Product.objects.count()} products, {ProductVariant.objects.count()} variants, "
            f"{ProductImage.objects.count()} images."
        ))

    # ---------- wipe ----------
    def _wipe(self):
        self.stdout.write("Wiping existing dummy records...")
        ProductImage.objects.filter(product__sku__startswith=DUMMY_SKU_PREFIX).delete()
        ProductVariant.objects.filter(product__sku__startswith=DUMMY_SKU_PREFIX).delete()
        Product.objects.filter(sku__startswith=DUMMY_SKU_PREFIX).delete()
        Brand.objects.filter(slug__startswith=DUMMY_SLUG_PREFIX).delete()
        Category.objects.filter(slug__startswith=DUMMY_SLUG_PREFIX).delete()
        SliderItem.objects.filter(title__startswith="[DUM]").delete()

    def _get_admin(self):
        u = User.objects.filter(is_superuser=True).first()
        if u:
            return u
        u, _ = User.objects.get_or_create(
            email="seed@esco.jo",
            defaults={"first_name": "Seed", "last_name": "Bot", "is_active": True},
        )
        return u

    # ---------- sliders ----------
    def _seed_sliders(self):
        self.stdout.write("Seeding sliders...")
        for i, (t_ar, sub_ar, desc_ar, t_en, sub_en, desc_en, btn_ar, btn_en, url) in enumerate(SLIDES):
            s = SliderItem(
                title=f"[DUM] {t_ar}",
                title_en=f"[DUM] {t_en}",
                subtitle=sub_ar,
                subtitle_en=sub_en,
                description=desc_ar,
                description_en=desc_en,
                primary_button_text=btn_ar,
                primary_button_url=url,
                secondary_button_text=btn_en,
                secondary_button_url=url,
                order=i,
                is_active=True,
            )
            s.image.save(f"slider-{i}.jpg",
                         img_file(f"slider-{i}", t_en, 1600, 600, seed=i + 1), save=False)
            s.save()

    # ---------- brands ----------
    def _seed_brands(self):
        self.stdout.write("Seeding brands...")
        out = []
        for i, (ar, en, c_ar, c_en) in enumerate(BRANDS):
            slug = f"{DUMMY_SLUG_PREFIX}brand-{slugify(en)}"
            b = Brand(
                name=ar, name_en=en, slug=slug,
                description=f"{ar} - {en}",
                country=f"{c_ar} - {c_en}",
                is_active=True, is_featured=(i < 4), sort_order=i,
            )
            b.logo.save(f"{slug}.jpg", img_file(slug, en, 400, 400, seed=10 + i), save=False)
            b.save()
            out.append(b)
        return out

    # ---------- categories ----------
    def _seed_categories(self):
        self.stdout.write("Seeding categories...")
        cats = {}
        for i, (ar, en, subs) in enumerate(CATEGORIES):
            slug_en = slugify(en)
            slug = f"{DUMMY_SLUG_PREFIX}cat-{slug_en}"
            c = Category(
                name=ar, name_en=en, slug=slug,
                description=f"{ar} - {en}",
                is_active=True, is_featured=True, show_in_menu=True, sort_order=i,
            )
            c.image.save(f"{slug}.jpg", img_file(slug, en, 600, 600, seed=100 + i), save=False)
            c.save()
            for j, (sub_ar, sub_en) in enumerate(subs):
                sub_slug_en = slugify(sub_en)
                sub_slug = f"{DUMMY_SLUG_PREFIX}cat-{sub_slug_en}"
                sc = Category(
                    name=sub_ar, name_en=sub_en, slug=sub_slug,
                    parent=c, description=f"{sub_ar} - {sub_en}",
                    is_active=True, show_in_menu=True, sort_order=j,
                )
                sc.image.save(f"{sub_slug}.jpg",
                              img_file(sub_slug, sub_en, 600, 600, seed=200 + i * 10 + j), save=False)
                sc.save()
                cats[sub_slug_en] = sc
            cats[slug_en] = c
        return cats

    # ---------- products ----------
    def _seed_products(self, cats, brands, admin):
        self.stdout.write("Seeding products...")
        for idx, (ar, en, cat_key, brand_idx, price, s_ar, s_en, variants) in enumerate(PRODUCTS):
            cat = cats.get(cat_key)
            if cat is None:
                self.stdout.write(self.style.WARNING(f"  ! missing category {cat_key}, skipping {en}"))
                continue
            sku = f"{DUMMY_SKU_PREFIX}{idx+1:04d}"
            slug = f"{DUMMY_SLUG_PREFIX}prod-{slugify(en)}-{idx}"
            p = Product(
                name=ar, name_en=en, slug=slug, sku=sku,
                category=cat, brand=brands[brand_idx],
                short_description=s_ar,
                description=f"<h3>{ar}</h3><p>{s_ar}</p><hr><h3>{en}</h3><p>{s_en}</p>",
                specifications={"warranty": "12 months", "origin": brands[brand_idx].name_en},
                features=[s_en, "High quality", "Fast shipping"],
                base_price=Decimal(str(price)),
                compare_price=Decimal(str(round(price * 1.2, 2))),
                tax_rate=Decimal("16.00"),
                stock_quantity=random.randint(5, 80),
                stock_status="in_stock",
                track_inventory=True,
                condition="new",
                is_featured=(idx % 4 == 0),
                is_new=(idx % 3 == 0),
                is_best_seller=(idx % 5 == 0),
                requires_shipping=True,
                status="published",
                is_active=True,
                show_price=True,
                allow_reviews=True,
                created_by=admin,
            )
            p.save()

            # images: 3 per product
            for k in range(3):
                pi = ProductImage(
                    product=p,
                    alt_text=en,
                    is_primary=(k == 0),
                    sort_order=k,
                )
                pi.image.save(
                    f"{slug}-{k}.jpg",
                    img_file(f"{slug}-{k}", f"{en}\n#{k+1}", 800, 800, seed=1000 + idx * 10 + k),
                    save=False,
                )
                pi.save()

            # variants
            if variants:
                for vi, (v_ar, v_en, attrs, delta) in enumerate(variants):
                    ProductVariant.objects.create(
                        product=p,
                        name=v_en,
                        sku=f"{sku}-V{vi+1}",
                        attributes=attrs,
                        base_price=Decimal(str(round(price + delta, 2))),
                        stock_quantity=random.randint(3, 30),
                        track_inventory=True,
                        is_active=True,
                        is_default=(vi == 0),
                        sort_order=vi,
                    )
