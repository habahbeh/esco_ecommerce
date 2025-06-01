#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
سكريبت إدخال بيانات ESCO في قاعدة البيانات
لتشغيل السكريبت:
python manage.py shell < import_esco_data.py
أو
python manage.py shell
ثم نسخ ولصق المحتوى
"""

from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

# استيراد جميع النماذج المطلوبة
from products.models import (
    Category, Brand, Product, ProductVariant,
    ProductImage, ProductReview, ProductQuestion,
    ProductDiscount, Wishlist, ProductComparison
)

User = get_user_model()

print("🚀 بدء إدخال بيانات ESCO...")

# إنشاء مستخدمين تجريبيين للتقييمات والأسئلة
try:
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@esco.jo',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()

    support_user, created = User.objects.get_or_create(
        username='support',
        defaults={
            'email': 'support@esco.jo',
            'is_staff': True
        }
    )
    if created:
        support_user.set_password('support123')
        support_user.save()

    # عملاء تجريبيين
    customer1, created = User.objects.get_or_create(
        username='ahmed_ali',
        defaults={'email': 'ahmed@example.com'}
    )
    if created:
        customer1.set_password('customer123')
        customer1.save()

    customer2, created = User.objects.get_or_create(
        username='sara_mohammed',
        defaults={'email': 'sara@example.com'}
    )
    if created:
        customer2.set_password('customer123')
        customer2.save()

    customer3, created = User.objects.get_or_create(
        username='khalid_omar',
        defaults={'email': 'khalid@example.com'}
    )
    if created:
        customer3.set_password('customer123')
        customer3.save()

    print("✅ تم إنشاء المستخدمين")
    print("  📝 بيانات تسجيل الدخول:")
    print("  - Admin: username=admin, password=admin123")
    print("  - Support: username=support, password=support123")
    print("  - Customers: password=customer123")
except Exception as e:
    print(f"❌ خطأ في إنشاء المستخدمين: {e}")

# ==========================================
# 1. إنشاء التصنيفات الهرمية
# ==========================================
print("\n📁 إنشاء التصنيفات...")

try:
    # التصنيف الرئيسي
    hand_tools, created = Category.objects.get_or_create(
        slug="hand-tools",
        defaults={
            'name': "العدد اليدوية",
            'name_en': "Hand Tools",
            'level': 0,
            'icon': "fas fa-tools",
            'is_featured': True,
            'sort_order': 1,
            'description': "جميع أنواع العدد اليدوية للاستخدام المنزلي والمهني"
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {hand_tools.name}")

    # التصنيفات الفرعية - المستوى الأول
    saws, created = Category.objects.get_or_create(
        slug="metal-wood-saws",
        defaults={
            'name': "منشار حديد وخشب",
            'name_en': "Metal and Wood Saws",
            'parent': hand_tools,
            'level': 1,
            'sort_order': 1
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {saws.name}")

    tool_boxes, created = Category.objects.get_or_create(
        slug="tool-boxes",
        defaults={
            'name': "صناديق عدة",
            'name_en': "Tool Boxes",
            'parent': hand_tools,
            'level': 1,
            'sort_order': 2
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {tool_boxes.name}")

    keys_screwdrivers, created = Category.objects.get_or_create(
        slug="keys-screwdrivers",
        defaults={
            'name': "المفاتيح و المفكات",
            'name_en': "Keys and Screwdrivers",
            'parent': hand_tools,
            'level': 1,
            'sort_order': 3
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {keys_screwdrivers.name}")

    # التصنيفات الفرعية - المستوى الثاني
    metal_plastic_boxes, created = Category.objects.get_or_create(
        slug="metal-plastic-tool-boxes",
        defaults={
            'name': "صندوق عدة حديد وبلاستيك",
            'name_en': "Metal and Plastic Tool Boxes",
            'parent': tool_boxes,
            'level': 2,
            'sort_order': 1
        }
    )
    print(f"    {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {metal_plastic_boxes.name}")

    plastic_drawer_boxes, created = Category.objects.get_or_create(
        slug="plastic-drawer-boxes",
        defaults={
            'name': "صندوق جوارير بلاستك",
            'name_en': "Plastic Drawer Boxes",
            'parent': tool_boxes,
            'level': 2,
            'sort_order': 2
        }
    )
    print(f"    {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {plastic_drawer_boxes.name}")

    screwdrivers, created = Category.objects.get_or_create(
        slug="screwdrivers",
        defaults={
            'name': "مفك عادي",
            'name_en': "Screwdrivers",
            'parent': keys_screwdrivers,
            'level': 2,
            'sort_order': 1
        }
    )
    print(f"    {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {screwdrivers.name}")

    spanners, created = Category.objects.get_or_create(
        slug="open-end-spanners",
        defaults={
            'name': "مفتاح شق رنج",
            'name_en': "Open End Spanners",
            'parent': keys_screwdrivers,
            'level': 2,
            'sort_order': 2
        }
    )
    print(f"    {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {spanners.name}")

except Exception as e:
    print(f"❌ خطأ في إنشاء التصنيفات: {e}")

# ==========================================
# 2. إنشاء العلامات التجارية
# ==========================================
print("\n🏷️ إنشاء العلامات التجارية...")

try:
    stanley, created = Brand.objects.get_or_create(
        slug="stanley",
        defaults={
            'name': "Stanley",
            'name_en': "Stanley",
            'country': "الولايات المتحدة",
            'description': "علامة تجارية رائدة في صناعة العدد اليدوية منذ 1843",
            'is_featured': True
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: Stanley")

    total, created = Brand.objects.get_or_create(
        slug="total",
        defaults={
            'name': "Total",
            'name_en': "Total",
            'country': "الصين",
            'description': "عدد يدوية بجودة عالية وأسعار منافسة"
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: Total")

    ingco, created = Brand.objects.get_or_create(
        slug="ingco",
        defaults={
            'name': "Ingco",
            'name_en': "Ingco",
            'country': "الصين",
            'description': "أدوات احترافية للاستخدام الشاق"
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: Ingco")

    dewalt, created = Brand.objects.get_or_create(
        slug="dewalt",
        defaults={
            'name': "DeWalt",
            'name_en': "DeWalt",
            'country': "الولايات المتحدة",
            'description': "عدد احترافية للمهنيين"
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: DeWalt")

except Exception as e:
    print(f"❌ خطأ في إنشاء العلامات التجارية: {e}")

# ==========================================
# 3. إنشاء المنتجات
# ==========================================
print("\n📦 إنشاء المنتجات...")

# منتج 1: منشار يدوي Stanley
try:
    multi_saw, created = Product.objects.get_or_create(
        sku="STAN-SAW-20",
        defaults={
            'name': "منشار يدوي Stanley 20 بوصة",
            'name_en': "Stanley 20 inch Hand Saw",
            'slug': "stanley-20-inch-hand-saw",
            'category': saws,
            'brand': stanley,
            'base_price': Decimal('12.50'),
            'compare_price': Decimal('15.00'),
            'created_by': admin_user,  # إضافة المستخدم الذي أنشأ المنتج
            'description': """منشار يدوي احترافي من Stanley لقطع الخشب والحديد
    - شفرة مصنوعة من الفولاذ المقسى
    - مقبض مريح مضاد للانزلاق
    - طول الشفرة: 20 بوصة (50 سم)
    - مناسب للخشب الصلب واللين""",
            'specifications': {
                "طول الشفرة": "20 بوصة (50 سم)",
                "نوع الأسنان": "7 أسنان لكل بوصة",
                "المادة": "فولاذ مقسى",
                "نوع المقبض": "بلاستيك مقوى",
                "الوزن": "450 جرام"
            },
            'features': [
                "شفرة قابلة للاستبدال",
                "مقبض مريح",
                "مناسب للاستخدام المنزلي والمهني"
            ],
            'stock_quantity': 25,
            'weight': Decimal('0.45'),
            'warranty_period': "سنة واحدة"
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {multi_saw.name}")

    # إضافة صورة للمنتج
    if created:
        ProductImage.objects.create(
            product=multi_saw,
            image="products/saws/stanley-20-inch-main.jpg",
            alt_text="منشار Stanley 20 بوصة",
            is_primary=True,
            sort_order=1
        )
except Exception as e:
    print(f"❌ خطأ في إنشاء منشار Stanley: {e}")

# منتج 2: منشار حديد Total مع متغيرات
try:
    metal_saw, created = Product.objects.get_or_create(
        sku="TOT-HACK",
        defaults={
            'name': "منشار حديد Total",
            'name_en': "Total Metal Hacksaw",
            'slug': "total-metal-hacksaw",
            'category': saws,
            'brand': total,
            'base_price': Decimal('8.00'),
            'created_by': admin_user,  # إضافة المستخدم
            'description': """منشار حديد قابل للتعديل من Total
    - إطار معدني قوي قابل للتعديل
    - يقبل شفرات بطول 10-12 بوصة
    - مقبض مطاطي مريح""",
            'specifications': {
                "المادة": "إطار معدني",
                "نوع المقبض": "مطاط",
                "قابل للتعديل": "نعم"
            },
            'stock_quantity': 0
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {metal_saw.name}")

    # إنشاء المتغيرات
    if created:
        variants_data = [
            {
                'name': "منشار حديد Total - 18 سن",
                'sku': "TOT-HACK-18T",
                'attributes': {
                    "نوع الشفرة": "18 سن/بوصة",
                    "الاستخدام": "للحديد السميك"
                },
                'base_price': Decimal('8.00'),
                'stock_quantity': 30
            },
            {
                'name': "منشار حديد Total - 24 سن",
                'sku': "TOT-HACK-24T",
                'attributes': {
                    "نوع الشفرة": "24 سن/بوصة",
                    "الاستخدام": "للحديد الرقيق والأنابيب"
                },
                'base_price': Decimal('8.50'),
                'stock_quantity': 20
            },
            {
                'name': "منشار حديد Total - طقم كامل",
                'sku': "TOT-HACK-SET",
                'attributes': {
                    "المحتويات": "منشار + 5 شفرات متنوعة",
                    "الشفرات": "2×18 سن + 2×24 سن + 1×32 سن"
                },
                'base_price': Decimal('15.00'),
                'stock_quantity': 15
            }
        ]

        for variant_data in variants_data:
            variant, _ = ProductVariant.objects.get_or_create(
                product=metal_saw,
                sku=variant_data['sku'],
                defaults=variant_data
            )
            print(f"    ✅ متغير: {variant.name}")

except Exception as e:
    print(f"❌ خطأ في إنشاء منشار Total: {e}")

# منتج 3: صندوق عدة DeWalt
try:
    metal_plastic_toolbox, created = Product.objects.get_or_create(
        sku="DEW-TB-19",
        defaults={
            'name': "صندوق عدة DeWalt 19 بوصة",
            'name_en': "DeWalt 19 inch Tool Box",
            'slug': "dewalt-19-inch-toolbox",
            'category': metal_plastic_boxes,
            'brand': dewalt,
            'base_price': Decimal('35.00'),
            'compare_price': Decimal('42.00'),
            'created_by': admin_user,  # إضافة المستخدم
            'description': """صندوق عدة احترافي من DeWalt
    - هيكل معدني قوي مع أجزاء بلاستيكية
    - صينية علوية قابلة للإزالة
    - قفل معدني آمن
    - مقبض مريح قابل للطي""",
            'specifications': {
                "الأبعاد": "19×7.5×7 بوصة",
                "المادة": "حديد + بلاستيك ABS",
                "عدد الأقسام": "صينية علوية + قسم رئيسي",
                "نوع القفل": "معدني بمفتاح",
                "الوزن": "2.5 كجم",
                "اللون": "أصفر وأسود"
            },
            'features': [
                "صينية قابلة للإزالة",
                "قفل أمان",
                "مقاوم للصدأ",
                "ضمان 3 سنوات"
            ],
            'stock_quantity': 18,
            'weight': Decimal('2.5'),
            'warranty_period': "3 سنوات"
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {metal_plastic_toolbox.name}")
except Exception as e:
    print(f"❌ خطأ في إنشاء صندوق DeWalt: {e}")

# منتج 4: صندوق جوارير Ingco مع متغيرات
try:
    drawer_organizer, created = Product.objects.get_or_create(
        sku="ING-ORG",
        defaults={
            'name': "صندوق جوارير Ingco",
            'name_en': "Ingco Drawer Organizer Box",
            'slug': "ingco-drawer-organizer",
            'category': plastic_drawer_boxes,
            'brand': ingco,
            'base_price': Decimal('12.00'),
            'created_by': admin_user,  # إضافة المستخدم
            'description': """صندوق تنظيم متعدد الجوارير من Ingco
    - بلاستيك عالي الجودة
    - جوارير شفافة لسهولة الرؤية
    - مثالي لتنظيم البراغي والمسامير""",
            'specifications': {
                "المادة": "بلاستيك PP",
                "شفاف": "نعم",
                "قابل للتعليق": "نعم"
            }
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {drawer_organizer.name}")

    # إنشاء المتغيرات
    if created:
        drawer_variants = [
            {
                'name': "صندوق جوارير Ingco - 12 جارور",
                'sku': "ING-ORG-12",
                'attributes': {
                    "عدد الجوارير": "12",
                    "الأبعاد": "30×15×5 سم",
                    "حجم الجارور": "7×5×4 سم"
                },
                'base_price': Decimal('12.00'),
                'stock_quantity': 40,
                'weight': Decimal('0.8')
            },
            {
                'name': "صندوق جوارير Ingco - 24 جارور",
                'sku': "ING-ORG-24",
                'attributes': {
                    "عدد الجوارير": "24",
                    "الأبعاد": "38×16×6 سم",
                    "حجم الجارور": "5×4×5 سم"
                },
                'base_price': Decimal('18.00'),
                'stock_quantity': 25,
                'weight': Decimal('1.2')
            },
            {
                'name': "صندوق جوارير Ingco - 39 جارور",
                'sku': "ING-ORG-39",
                'attributes': {
                    "عدد الجوارير": "39",
                    "الأبعاد": "49×16×7 سم",
                    "حجم الجارور": "متنوع (3 أحجام)"
                },
                'base_price': Decimal('28.00'),
                'stock_quantity': 12,
                'weight': Decimal('1.8')
            }
        ]

        for variant_data in drawer_variants:
            variant, _ = ProductVariant.objects.get_or_create(
                product=drawer_organizer,
                sku=variant_data['sku'],
                defaults=variant_data
            )
            print(f"    ✅ متغير: {variant.name}")

except Exception as e:
    print(f"❌ خطأ في إنشاء صندوق Ingco: {e}")

# منتج 5: طقم مفكات Stanley
try:
    screwdriver_set, created = Product.objects.get_or_create(
        sku="STAN-SD-SET6",
        defaults={
            'name': "طقم مفكات Stanley 6 قطع",
            'name_en': "Stanley 6-Piece Screwdriver Set",
            'slug': "stanley-screwdriver-set-6pc",
            'category': screwdrivers,
            'brand': stanley,
            'base_price': Decimal('22.00'),
            'compare_price': Decimal('28.00'),
            'created_by': admin_user,  # إضافة المستخدم
            'description': """طقم مفكات احترافي من Stanley
    - 3 مفكات عادية (صليبة)
    - 3 مفكات مسطحة
    - مقابض مريحة مضادة للانزلاق
    - شفرات من الكروم فاناديوم""",
            'specifications': {
                "عدد القطع": "6",
                "الأحجام": "3 صليبة (PH0, PH1, PH2) + 3 مسطحة (3mm, 5mm, 6mm)",
                "مادة الشفرة": "كروم فاناديوم",
                "مادة المقبض": "بلاستيك مع مطاط",
                "مغناطيسي": "نعم"
            },
            'features': [
                "شفرات مغناطيسية",
                "مقاومة للصدأ",
                "ضمان مدى الحياة"
            ],
            'stock_quantity': 35,
            'weight': Decimal('0.65'),
            'warranty_period': "مدى الحياة"
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {screwdriver_set.name}")
except Exception as e:
    print(f"❌ خطأ في إنشاء طقم المفكات: {e}")

# منتج 6: مفتاح شق رنج Total مع متغيرات
try:
    spanner_wrench, created = Product.objects.get_or_create(
        sku="TOT-SPANNER",
        defaults={
            'name': "مفتاح شق رنج Total",
            'name_en': "Total Open End Ring Spanner",
            'slug': "total-open-end-ring-spanner",
            'category': spanners,
            'brand': total,
            'base_price': Decimal('3.50'),
            'created_by': admin_user,  # إضافة المستخدم
            'description': """مفتاح شق رنج من Total
    - فولاذ كروم فاناديوم عالي الجودة
    - طرف شق وطرف رنج
    - مقاوم للصدأ والتآكل""",
            'specifications': {
                "المادة": "كروم فاناديوم",
                "النوع": "شق من جهة ورنج من جهة",
                "الطلاء": "كروم لامع"
            }
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {spanner_wrench.name}")

    # إنشاء المتغيرات للمقاسات المختلفة
    if created:
        sizes = [
            {"size": "8mm", "price": "3.50", "sku": "TOT-SPAN-8"},
            {"size": "10mm", "price": "3.50", "sku": "TOT-SPAN-10"},
            {"size": "12mm", "price": "4.00", "sku": "TOT-SPAN-12"},
            {"size": "13mm", "price": "4.00", "sku": "TOT-SPAN-13"},
            {"size": "14mm", "price": "4.50", "sku": "TOT-SPAN-14"},
            {"size": "17mm", "price": "5.00", "sku": "TOT-SPAN-17"},
            {"size": "19mm", "price": "5.50", "sku": "TOT-SPAN-19"},
            {"size": "22mm", "price": "6.50", "sku": "TOT-SPAN-22"},
            {"size": "24mm", "price": "7.00", "sku": "TOT-SPAN-24"}
        ]

        for size_info in sizes:
            variant, _ = ProductVariant.objects.get_or_create(
                product=spanner_wrench,
                sku=size_info['sku'],
                defaults={
                    'name': f"مفتاح شق رنج Total - {size_info['size']}",
                    'attributes': {
                        "المقاس": size_info['size'],
                        "الطول": f"{int(size_info['size'][:-2]) * 13}mm"
                    },
                    'base_price': Decimal(size_info['price']),
                    'stock_quantity': 20
                }
            )
            print(f"    ✅ متغير: {variant.name}")

        # طقم كامل
        variant_set, _ = ProductVariant.objects.get_or_create(
            product=spanner_wrench,
            sku="TOT-SPAN-SET8",
            defaults={
                'name': "طقم مفاتيح شق رنج Total - 8 قطع",
                'attributes': {
                    "المحتويات": "8-10-12-13-14-17-19-22mm",
                    "مع حقيبة": "نعم"
                },
                'base_price': Decimal('35.00'),
                'stock_quantity': 10
            }
        )
        print(f"    ✅ متغير: {variant_set.name}")

except Exception as e:
    print(f"❌ خطأ في إنشاء مفتاح شق رنج: {e}")

# ==========================================
# 4. إنشاء العروض والخصومات
# ==========================================
print("\n🎯 إنشاء العروض والخصومات...")

try:
    # خصم على فئة العدد اليدوية
    hand_tools_discount, created = ProductDiscount.objects.get_or_create(
        code="TOOLS20",
        defaults={
            'name': "خصم 20% على العدد اليدوية",
            'discount_type': "percentage",
            'value': Decimal('20'),
            'application_type': "category",
            'category': hand_tools,  # التصنيف الرئيسي
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=7),
            'is_active': True,
            'created_by': admin_user
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: خصم العدد اليدوية 20%")

    # خصم على صناديق العدة (buy 2 get 1)
    toolbox_bogo, created = ProductDiscount.objects.get_or_create(
        code="TOOLBOX_BOGO",
        defaults={
            'name': "اشتري 2 احصل على 1 مجاناً - صناديق العدة",
            'discount_type': "buy_x_get_y",
            'value': Decimal('100'),  # قيمة الخصم (100% للمنتج المجاني)
            'buy_quantity': 2,
            'get_quantity': 1,
            'get_discount_percentage': Decimal('100'),
            'application_type': "category",
            'category': tool_boxes,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'is_active': True,
            'created_by': admin_user
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: عرض اشتري 2 احصل على 1")

    # خصم بحد أدنى للشراء
    min_purchase_discount, created = ProductDiscount.objects.get_or_create(
        code="SAVE50",
        defaults={
            'name': "خصم 15% عند الشراء بـ 50 دينار أو أكثر",
            'discount_type': "percentage",
            'value': Decimal('15'),
            'application_type': "minimum_purchase",
            'min_purchase_amount': Decimal('50.00'),
            'start_date': timezone.now(),
            'is_active': True,
            'created_by': admin_user
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: خصم الحد الأدنى للشراء")

except Exception as e:
    print(f"❌ خطأ في إنشاء العروض: {e}")

# ==========================================
# 5. إنشاء التقييمات
# ==========================================
print("\n⭐ إنشاء التقييمات...")

try:
    # تقييم على منشار Stanley
    review1, created = ProductReview.objects.get_or_create(
        product=multi_saw,
        user=customer1,
        defaults={
            'rating': 5,
            'title': "منشار ممتاز للاستخدام المنزلي",
            'content': "اشتريته قبل شهرين واستخدمته في قص الخشب والأنابيب البلاستيكية. الشفرة حادة جداً والمقبض مريح.",
            'quality_rating': 5,
            'value_rating': 5,
            'is_approved': True,
            'helpful_votes': 8
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: تقييم منشار Stanley")

    # تقييم على صندوق الجوارير
    review2, created = ProductReview.objects.get_or_create(
        product=drawer_organizer,
        user=customer2,  # مستخدم مختلف
        defaults={
            'rating': 4,
            'title': "ممتاز للتنظيم",
            'content': "صندوق ممتاز لتنظيم البراغي والمسامير. الجوارير شفافة وسهل معرفة المحتويات. العيب الوحيد أن البلاستيك رقيق نوعاً ما.",
            'quality_rating': 4,
            'value_rating': 5,
            'is_approved': True,
            'helpful_votes': 12
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: تقييم صندوق Ingco")

except Exception as e:
    print(f"❌ خطأ في إنشاء التقييمات: {e}")

# ==========================================
# 6. إنشاء الأسئلة والأجوبة
# ==========================================
print("\n💬 إنشاء الأسئلة والأجوبة...")

try:
    question1, created = ProductQuestion.objects.get_or_create(
        product=spanner_wrench,
        user=customer3,
        defaults={
            'question': "هل المفتاح مناسب للاستخدام مع السيارات؟",
            'answer': "نعم، مفاتيح Total مصنوعة من الكروم فاناديوم وهي قوية بما يكفي للاستخدام في صيانة السيارات.",
            'is_answered': True,
            'answered_by': support_user,
            'answered_at': timezone.now(),
            'helpful_votes': 5
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: سؤال عن مفتاح شق رنج")

    question2, created = ProductQuestion.objects.get_or_create(
        product=metal_plastic_toolbox,
        user=customer1,
        defaults={
            'question': "هل الصندوق مقاوم للماء؟",
            'answer': "الصندوق مقاوم لرذاذ الماء ولكنه غير مصمم للغمر الكامل في الماء. ننصح بحفظه في مكان جاف.",
            'is_answered': True,
            'answered_by': support_user,
            'answered_at': timezone.now(),
            'helpful_votes': 3
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: سؤال عن صندوق DeWalt")

except Exception as e:
    print(f"❌ خطأ في إنشاء الأسئلة: {e}")

# ==========================================
# 7. ربط المنتجات ذات الصلة
# ==========================================
print("\n🔗 ربط المنتجات ذات الصلة...")

try:
    # ربط المناشير مع بعضها وصندوق العدة
    multi_saw.related_products.add(metal_saw, metal_plastic_toolbox)
    print("  ✅ تم ربط منشار Stanley مع منتجات ذات صلة")

    # ربط المفكات مع المفاتيح وصندوق التنظيم
    screwdriver_set.related_products.add(spanner_wrench, drawer_organizer)
    print("  ✅ تم ربط طقم المفكات مع منتجات ذات صلة")

    # ربط صناديق العدة مع بعضها
    metal_plastic_toolbox.related_products.add(drawer_organizer)
    print("  ✅ تم ربط صناديق العدة")

except Exception as e:
    print(f"❌ خطأ في ربط المنتجات: {e}")

# ==========================================
# 8. تحديث إحصائيات التصنيفات
# ==========================================
print("\n📊 تحديث إحصائيات التصنيفات...")

try:
    for category in Category.objects.all():
        category.update_products_count()
    print("  ✅ تم تحديث جميع إحصائيات التصنيفات")
except Exception as e:
    print(f"❌ خطأ في تحديث الإحصائيات: {e}")

# ==========================================
# ملخص النتائج
# ==========================================
print("\n" + "=" * 50)
print("📊 ملخص الإدخال:")
print("=" * 50)
print(f"✅ التصنيفات: {Category.objects.count()}")
print(f"✅ العلامات التجارية: {Brand.objects.count()}")
print(f"✅ المنتجات: {Product.objects.count()}")
print(f"✅ متغيرات المنتجات: {ProductVariant.objects.count()}")
print(f"✅ التقييمات: {ProductReview.objects.count()}")
print(f"✅ الأسئلة: {ProductQuestion.objects.count()}")
print(f"✅ العروض: {ProductDiscount.objects.count()}")
print("=" * 50)
print("✨ تم إدخال جميع البيانات بنجاح!")