# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
# """
# سكريبت إدخال بيانات ESCO في قاعدة البيانات
# لتشغيل السكريبت:
# python manage.py shell < import_esco_data.py
# أو
# python manage.py shell
# ثم نسخ ولصق المحتوى
# """
#
# from decimal import Decimal
# from datetime import datetime, timedelta
# from django.utils import timezone
# from django.contrib.auth import get_user_model
#
# # استيراد جميع النماذج المطلوبة
# from products.models import (
#     Category, Brand, Product, ProductVariant,
#     ProductImage, ProductReview, ProductQuestion,
#     ProductDiscount, Wishlist, ProductComparison
# )
#
# User = get_user_model()
#
# print("🚀 بدء إدخال بيانات ESCO...")
#
# # إنشاء مستخدمين تجريبيين للتقييمات والأسئلة
# try:
#     admin_user, created = User.objects.get_or_create(
#         username='admin',
#         defaults={
#             'email': 'admin@esco.jo',
#             'is_staff': True,
#             'is_superuser': True
#         }
#     )
#     if created:
#         admin_user.set_password('admin123')
#         admin_user.save()
#
#     support_user, created = User.objects.get_or_create(
#         username='support',
#         defaults={
#             'email': 'support@esco.jo',
#             'is_staff': True
#         }
#     )
#     if created:
#         support_user.set_password('support123')
#         support_user.save()
#
#     # عملاء تجريبيين
#     customer1, created = User.objects.get_or_create(
#         username='ahmed_ali',
#         defaults={'email': 'ahmed@example.com'}
#     )
#     if created:
#         customer1.set_password('customer123')
#         customer1.save()
#
#     customer2, created = User.objects.get_or_create(
#         username='sara_mohammed',
#         defaults={'email': 'sara@example.com'}
#     )
#     if created:
#         customer2.set_password('customer123')
#         customer2.save()
#
#     customer3, created = User.objects.get_or_create(
#         username='khalid_omar',
#         defaults={'email': 'khalid@example.com'}
#     )
#     if created:
#         customer3.set_password('customer123')
#         customer3.save()
#
#     print("✅ تم إنشاء المستخدمين")
#     print("  📝 بيانات تسجيل الدخول:")
#     print("  - Admin: username=admin, password=admin123")
#     print("  - Support: username=support, password=support123")
#     print("  - Customers: password=customer123")
# except Exception as e:
#     print(f"❌ خطأ في إنشاء المستخدمين: {e}")
#
# # ==========================================
# # 1. إنشاء التصنيفات الهرمية
# # ==========================================
# print("\n📁 إنشاء التصنيفات...")
#
# try:
#     # التصنيف الرئيسي
#     hand_tools, created = Category.objects.get_or_create(
#         slug="hand-tools",
#         defaults={
#             'name': "العدد اليدوية",
#             'name_en': "Hand Tools",
#             'level': 0,
#             'icon': "fas fa-tools",
#             'is_featured': True,
#             'sort_order': 1,
#             'description': "جميع أنواع العدد اليدوية للاستخدام المنزلي والمهني"
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {hand_tools.name}")
#
#     # التصنيفات الفرعية - المستوى الأول
#     saws, created = Category.objects.get_or_create(
#         slug="metal-wood-saws",
#         defaults={
#             'name': "منشار حديد وخشب",
#             'name_en': "Metal and Wood Saws",
#             'parent': hand_tools,
#             'level': 1,
#             'sort_order': 1
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {saws.name}")
#
#     tool_boxes, created = Category.objects.get_or_create(
#         slug="tool-boxes",
#         defaults={
#             'name': "صناديق عدة",
#             'name_en': "Tool Boxes",
#             'parent': hand_tools,
#             'level': 1,
#             'sort_order': 2
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {tool_boxes.name}")
#
#     keys_screwdrivers, created = Category.objects.get_or_create(
#         slug="keys-screwdrivers",
#         defaults={
#             'name': "المفاتيح و المفكات",
#             'name_en': "Keys and Screwdrivers",
#             'parent': hand_tools,
#             'level': 1,
#             'sort_order': 3
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {keys_screwdrivers.name}")
#
#     # التصنيفات الفرعية - المستوى الثاني
#     metal_plastic_boxes, created = Category.objects.get_or_create(
#         slug="metal-plastic-tool-boxes",
#         defaults={
#             'name': "صندوق عدة حديد وبلاستيك",
#             'name_en': "Metal and Plastic Tool Boxes",
#             'parent': tool_boxes,
#             'level': 2,
#             'sort_order': 1
#         }
#     )
#     print(f"    {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {metal_plastic_boxes.name}")
#
#     plastic_drawer_boxes, created = Category.objects.get_or_create(
#         slug="plastic-drawer-boxes",
#         defaults={
#             'name': "صندوق جوارير بلاستك",
#             'name_en': "Plastic Drawer Boxes",
#             'parent': tool_boxes,
#             'level': 2,
#             'sort_order': 2
#         }
#     )
#     print(f"    {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {plastic_drawer_boxes.name}")
#
#     screwdrivers, created = Category.objects.get_or_create(
#         slug="screwdrivers",
#         defaults={
#             'name': "مفك عادي",
#             'name_en': "Screwdrivers",
#             'parent': keys_screwdrivers,
#             'level': 2,
#             'sort_order': 1
#         }
#     )
#     print(f"    {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {screwdrivers.name}")
#
#     spanners, created = Category.objects.get_or_create(
#         slug="open-end-spanners",
#         defaults={
#             'name': "مفتاح شق رنج",
#             'name_en': "Open End Spanners",
#             'parent': keys_screwdrivers,
#             'level': 2,
#             'sort_order': 2
#         }
#     )
#     print(f"    {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {spanners.name}")
#
# except Exception as e:
#     print(f"❌ خطأ في إنشاء التصنيفات: {e}")
#
# # ==========================================
# # 2. إنشاء العلامات التجارية
# # ==========================================
# print("\n🏷️ إنشاء العلامات التجارية...")
#
# try:
#     stanley, created = Brand.objects.get_or_create(
#         slug="stanley",
#         defaults={
#             'name': "Stanley",
#             'name_en': "Stanley",
#             'country': "الولايات المتحدة",
#             'description': "علامة تجارية رائدة في صناعة العدد اليدوية منذ 1843",
#             'is_featured': True
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: Stanley")
#
#     total, created = Brand.objects.get_or_create(
#         slug="total",
#         defaults={
#             'name': "Total",
#             'name_en': "Total",
#             'country': "الصين",
#             'description': "عدد يدوية بجودة عالية وأسعار منافسة"
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: Total")
#
#     ingco, created = Brand.objects.get_or_create(
#         slug="ingco",
#         defaults={
#             'name': "Ingco",
#             'name_en': "Ingco",
#             'country': "الصين",
#             'description': "أدوات احترافية للاستخدام الشاق"
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: Ingco")
#
#     dewalt, created = Brand.objects.get_or_create(
#         slug="dewalt",
#         defaults={
#             'name': "DeWalt",
#             'name_en': "DeWalt",
#             'country': "الولايات المتحدة",
#             'description': "عدد احترافية للمهنيين"
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: DeWalt")
#
# except Exception as e:
#     print(f"❌ خطأ في إنشاء العلامات التجارية: {e}")
#
# # ==========================================
# # 3. إنشاء المنتجات
# # ==========================================
# print("\n📦 إنشاء المنتجات...")
#
# # منتج 1: منشار يدوي Stanley
# try:
#     multi_saw, created = Product.objects.get_or_create(
#         sku="STAN-SAW-20",
#         defaults={
#             'name': "منشار يدوي Stanley 20 بوصة",
#             'name_en': "Stanley 20 inch Hand Saw",
#             'slug': "stanley-20-inch-hand-saw",
#             'category': saws,
#             'brand': stanley,
#             'base_price': Decimal('12.50'),
#             'compare_price': Decimal('15.00'),
#             'created_by': admin_user,  # إضافة المستخدم الذي أنشأ المنتج
#             'description': """منشار يدوي احترافي من Stanley لقطع الخشب والحديد
#     - شفرة مصنوعة من الفولاذ المقسى
#     - مقبض مريح مضاد للانزلاق
#     - طول الشفرة: 20 بوصة (50 سم)
#     - مناسب للخشب الصلب واللين""",
#             'specifications': {
#                 "طول الشفرة": "20 بوصة (50 سم)",
#                 "نوع الأسنان": "7 أسنان لكل بوصة",
#                 "المادة": "فولاذ مقسى",
#                 "نوع المقبض": "بلاستيك مقوى",
#                 "الوزن": "450 جرام"
#             },
#             'features': [
#                 "شفرة قابلة للاستبدال",
#                 "مقبض مريح",
#                 "مناسب للاستخدام المنزلي والمهني"
#             ],
#             'stock_quantity': 25,
#             'weight': Decimal('0.45'),
#             'warranty_period': "سنة واحدة"
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {multi_saw.name}")
#
#     # إضافة صورة للمنتج
#     if created:
#         ProductImage.objects.create(
#             product=multi_saw,
#             image="products/saws/stanley-20-inch-main.jpg",
#             alt_text="منشار Stanley 20 بوصة",
#             is_primary=True,
#             sort_order=1
#         )
# except Exception as e:
#     print(f"❌ خطأ في إنشاء منشار Stanley: {e}")
#
# # منتج 2: منشار حديد Total مع متغيرات
# try:
#     metal_saw, created = Product.objects.get_or_create(
#         sku="TOT-HACK",
#         defaults={
#             'name': "منشار حديد Total",
#             'name_en': "Total Metal Hacksaw",
#             'slug': "total-metal-hacksaw",
#             'category': saws,
#             'brand': total,
#             'base_price': Decimal('8.00'),
#             'created_by': admin_user,  # إضافة المستخدم
#             'description': """منشار حديد قابل للتعديل من Total
#     - إطار معدني قوي قابل للتعديل
#     - يقبل شفرات بطول 10-12 بوصة
#     - مقبض مطاطي مريح""",
#             'specifications': {
#                 "المادة": "إطار معدني",
#                 "نوع المقبض": "مطاط",
#                 "قابل للتعديل": "نعم"
#             },
#             'stock_quantity': 0
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {metal_saw.name}")
#
#     # إنشاء المتغيرات
#     if created:
#         variants_data = [
#             {
#                 'name': "منشار حديد Total - 18 سن",
#                 'sku': "TOT-HACK-18T",
#                 'attributes': {
#                     "نوع الشفرة": "18 سن/بوصة",
#                     "الاستخدام": "للحديد السميك"
#                 },
#                 'base_price': Decimal('8.00'),
#                 'stock_quantity': 30
#             },
#             {
#                 'name': "منشار حديد Total - 24 سن",
#                 'sku': "TOT-HACK-24T",
#                 'attributes': {
#                     "نوع الشفرة": "24 سن/بوصة",
#                     "الاستخدام": "للحديد الرقيق والأنابيب"
#                 },
#                 'base_price': Decimal('8.50'),
#                 'stock_quantity': 20
#             },
#             {
#                 'name': "منشار حديد Total - طقم كامل",
#                 'sku': "TOT-HACK-SET",
#                 'attributes': {
#                     "المحتويات": "منشار + 5 شفرات متنوعة",
#                     "الشفرات": "2×18 سن + 2×24 سن + 1×32 سن"
#                 },
#                 'base_price': Decimal('15.00'),
#                 'stock_quantity': 15
#             }
#         ]
#
#         for variant_data in variants_data:
#             variant, _ = ProductVariant.objects.get_or_create(
#                 product=metal_saw,
#                 sku=variant_data['sku'],
#                 defaults=variant_data
#             )
#             print(f"    ✅ متغير: {variant.name}")
#
# except Exception as e:
#     print(f"❌ خطأ في إنشاء منشار Total: {e}")
#
# # منتج 3: صندوق عدة DeWalt
# try:
#     metal_plastic_toolbox, created = Product.objects.get_or_create(
#         sku="DEW-TB-19",
#         defaults={
#             'name': "صندوق عدة DeWalt 19 بوصة",
#             'name_en': "DeWalt 19 inch Tool Box",
#             'slug': "dewalt-19-inch-toolbox",
#             'category': metal_plastic_boxes,
#             'brand': dewalt,
#             'base_price': Decimal('35.00'),
#             'compare_price': Decimal('42.00'),
#             'created_by': admin_user,  # إضافة المستخدم
#             'description': """صندوق عدة احترافي من DeWalt
#     - هيكل معدني قوي مع أجزاء بلاستيكية
#     - صينية علوية قابلة للإزالة
#     - قفل معدني آمن
#     - مقبض مريح قابل للطي""",
#             'specifications': {
#                 "الأبعاد": "19×7.5×7 بوصة",
#                 "المادة": "حديد + بلاستيك ABS",
#                 "عدد الأقسام": "صينية علوية + قسم رئيسي",
#                 "نوع القفل": "معدني بمفتاح",
#                 "الوزن": "2.5 كجم",
#                 "اللون": "أصفر وأسود"
#             },
#             'features': [
#                 "صينية قابلة للإزالة",
#                 "قفل أمان",
#                 "مقاوم للصدأ",
#                 "ضمان 3 سنوات"
#             ],
#             'stock_quantity': 18,
#             'weight': Decimal('2.5'),
#             'warranty_period': "3 سنوات"
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {metal_plastic_toolbox.name}")
# except Exception as e:
#     print(f"❌ خطأ في إنشاء صندوق DeWalt: {e}")
#
# # منتج 4: صندوق جوارير Ingco مع متغيرات
# try:
#     drawer_organizer, created = Product.objects.get_or_create(
#         sku="ING-ORG",
#         defaults={
#             'name': "صندوق جوارير Ingco",
#             'name_en': "Ingco Drawer Organizer Box",
#             'slug': "ingco-drawer-organizer",
#             'category': plastic_drawer_boxes,
#             'brand': ingco,
#             'base_price': Decimal('12.00'),
#             'created_by': admin_user,  # إضافة المستخدم
#             'description': """صندوق تنظيم متعدد الجوارير من Ingco
#     - بلاستيك عالي الجودة
#     - جوارير شفافة لسهولة الرؤية
#     - مثالي لتنظيم البراغي والمسامير""",
#             'specifications': {
#                 "المادة": "بلاستيك PP",
#                 "شفاف": "نعم",
#                 "قابل للتعليق": "نعم"
#             }
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {drawer_organizer.name}")
#
#     # إنشاء المتغيرات
#     if created:
#         drawer_variants = [
#             {
#                 'name': "صندوق جوارير Ingco - 12 جارور",
#                 'sku': "ING-ORG-12",
#                 'attributes': {
#                     "عدد الجوارير": "12",
#                     "الأبعاد": "30×15×5 سم",
#                     "حجم الجارور": "7×5×4 سم"
#                 },
#                 'base_price': Decimal('12.00'),
#                 'stock_quantity': 40,
#                 'weight': Decimal('0.8')
#             },
#             {
#                 'name': "صندوق جوارير Ingco - 24 جارور",
#                 'sku': "ING-ORG-24",
#                 'attributes': {
#                     "عدد الجوارير": "24",
#                     "الأبعاد": "38×16×6 سم",
#                     "حجم الجارور": "5×4×5 سم"
#                 },
#                 'base_price': Decimal('18.00'),
#                 'stock_quantity': 25,
#                 'weight': Decimal('1.2')
#             },
#             {
#                 'name': "صندوق جوارير Ingco - 39 جارور",
#                 'sku': "ING-ORG-39",
#                 'attributes': {
#                     "عدد الجوارير": "39",
#                     "الأبعاد": "49×16×7 سم",
#                     "حجم الجارور": "متنوع (3 أحجام)"
#                 },
#                 'base_price': Decimal('28.00'),
#                 'stock_quantity': 12,
#                 'weight': Decimal('1.8')
#             }
#         ]
#
#         for variant_data in drawer_variants:
#             variant, _ = ProductVariant.objects.get_or_create(
#                 product=drawer_organizer,
#                 sku=variant_data['sku'],
#                 defaults=variant_data
#             )
#             print(f"    ✅ متغير: {variant.name}")
#
# except Exception as e:
#     print(f"❌ خطأ في إنشاء صندوق Ingco: {e}")
#
# # منتج 5: طقم مفكات Stanley
# try:
#     screwdriver_set, created = Product.objects.get_or_create(
#         sku="STAN-SD-SET6",
#         defaults={
#             'name': "طقم مفكات Stanley 6 قطع",
#             'name_en': "Stanley 6-Piece Screwdriver Set",
#             'slug': "stanley-screwdriver-set-6pc",
#             'category': screwdrivers,
#             'brand': stanley,
#             'base_price': Decimal('22.00'),
#             'compare_price': Decimal('28.00'),
#             'created_by': admin_user,  # إضافة المستخدم
#             'description': """طقم مفكات احترافي من Stanley
#     - 3 مفكات عادية (صليبة)
#     - 3 مفكات مسطحة
#     - مقابض مريحة مضادة للانزلاق
#     - شفرات من الكروم فاناديوم""",
#             'specifications': {
#                 "عدد القطع": "6",
#                 "الأحجام": "3 صليبة (PH0, PH1, PH2) + 3 مسطحة (3mm, 5mm, 6mm)",
#                 "مادة الشفرة": "كروم فاناديوم",
#                 "مادة المقبض": "بلاستيك مع مطاط",
#                 "مغناطيسي": "نعم"
#             },
#             'features': [
#                 "شفرات مغناطيسية",
#                 "مقاومة للصدأ",
#                 "ضمان مدى الحياة"
#             ],
#             'stock_quantity': 35,
#             'weight': Decimal('0.65'),
#             'warranty_period': "مدى الحياة"
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {screwdriver_set.name}")
# except Exception as e:
#     print(f"❌ خطأ في إنشاء طقم المفكات: {e}")
#
# # منتج 6: مفتاح شق رنج Total مع متغيرات
# try:
#     spanner_wrench, created = Product.objects.get_or_create(
#         sku="TOT-SPANNER",
#         defaults={
#             'name': "مفتاح شق رنج Total",
#             'name_en': "Total Open End Ring Spanner",
#             'slug': "total-open-end-ring-spanner",
#             'category': spanners,
#             'brand': total,
#             'base_price': Decimal('3.50'),
#             'created_by': admin_user,  # إضافة المستخدم
#             'description': """مفتاح شق رنج من Total
#     - فولاذ كروم فاناديوم عالي الجودة
#     - طرف شق وطرف رنج
#     - مقاوم للصدأ والتآكل""",
#             'specifications': {
#                 "المادة": "كروم فاناديوم",
#                 "النوع": "شق من جهة ورنج من جهة",
#                 "الطلاء": "كروم لامع"
#             }
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {spanner_wrench.name}")
#
#     # إنشاء المتغيرات للمقاسات المختلفة
#     if created:
#         sizes = [
#             {"size": "8mm", "price": "3.50", "sku": "TOT-SPAN-8"},
#             {"size": "10mm", "price": "3.50", "sku": "TOT-SPAN-10"},
#             {"size": "12mm", "price": "4.00", "sku": "TOT-SPAN-12"},
#             {"size": "13mm", "price": "4.00", "sku": "TOT-SPAN-13"},
#             {"size": "14mm", "price": "4.50", "sku": "TOT-SPAN-14"},
#             {"size": "17mm", "price": "5.00", "sku": "TOT-SPAN-17"},
#             {"size": "19mm", "price": "5.50", "sku": "TOT-SPAN-19"},
#             {"size": "22mm", "price": "6.50", "sku": "TOT-SPAN-22"},
#             {"size": "24mm", "price": "7.00", "sku": "TOT-SPAN-24"}
#         ]
#
#         for size_info in sizes:
#             variant, _ = ProductVariant.objects.get_or_create(
#                 product=spanner_wrench,
#                 sku=size_info['sku'],
#                 defaults={
#                     'name': f"مفتاح شق رنج Total - {size_info['size']}",
#                     'attributes': {
#                         "المقاس": size_info['size'],
#                         "الطول": f"{int(size_info['size'][:-2]) * 13}mm"
#                     },
#                     'base_price': Decimal(size_info['price']),
#                     'stock_quantity': 20
#                 }
#             )
#             print(f"    ✅ متغير: {variant.name}")
#
#         # طقم كامل
#         variant_set, _ = ProductVariant.objects.get_or_create(
#             product=spanner_wrench,
#             sku="TOT-SPAN-SET8",
#             defaults={
#                 'name': "طقم مفاتيح شق رنج Total - 8 قطع",
#                 'attributes': {
#                     "المحتويات": "8-10-12-13-14-17-19-22mm",
#                     "مع حقيبة": "نعم"
#                 },
#                 'base_price': Decimal('35.00'),
#                 'stock_quantity': 10
#             }
#         )
#         print(f"    ✅ متغير: {variant_set.name}")
#
# except Exception as e:
#     print(f"❌ خطأ في إنشاء مفتاح شق رنج: {e}")
#
# # ==========================================
# # 4. إنشاء العروض والخصومات
# # ==========================================
# print("\n🎯 إنشاء العروض والخصومات...")
#
# try:
#     # خصم على فئة العدد اليدوية
#     hand_tools_discount, created = ProductDiscount.objects.get_or_create(
#         code="TOOLS20",
#         defaults={
#             'name': "خصم 20% على العدد اليدوية",
#             'discount_type': "percentage",
#             'value': Decimal('20'),
#             'application_type': "category",
#             'category': hand_tools,  # التصنيف الرئيسي
#             'start_date': timezone.now(),
#             'end_date': timezone.now() + timedelta(days=7),
#             'is_active': True,
#             'created_by': admin_user
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: خصم العدد اليدوية 20%")
#
#     # خصم على صناديق العدة (buy 2 get 1)
#     toolbox_bogo, created = ProductDiscount.objects.get_or_create(
#         code="TOOLBOX_BOGO",
#         defaults={
#             'name': "اشتري 2 احصل على 1 مجاناً - صناديق العدة",
#             'discount_type': "buy_x_get_y",
#             'value': Decimal('100'),  # قيمة الخصم (100% للمنتج المجاني)
#             'buy_quantity': 2,
#             'get_quantity': 1,
#             'get_discount_percentage': Decimal('100'),
#             'application_type': "category",
#             'category': tool_boxes,
#             'start_date': timezone.now(),
#             'end_date': timezone.now() + timedelta(days=30),
#             'is_active': True,
#             'created_by': admin_user
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: عرض اشتري 2 احصل على 1")
#
#     # خصم بحد أدنى للشراء
#     min_purchase_discount, created = ProductDiscount.objects.get_or_create(
#         code="SAVE50",
#         defaults={
#             'name': "خصم 15% عند الشراء بـ 50 دينار أو أكثر",
#             'discount_type': "percentage",
#             'value': Decimal('15'),
#             'application_type': "minimum_purchase",
#             'min_purchase_amount': Decimal('50.00'),
#             'start_date': timezone.now(),
#             'is_active': True,
#             'created_by': admin_user
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: خصم الحد الأدنى للشراء")
#
# except Exception as e:
#     print(f"❌ خطأ في إنشاء العروض: {e}")
#
# # ==========================================
# # 5. إنشاء التقييمات
# # ==========================================
# print("\n⭐ إنشاء التقييمات...")
#
# try:
#     # تقييم على منشار Stanley
#     review1, created = ProductReview.objects.get_or_create(
#         product=multi_saw,
#         user=customer1,
#         defaults={
#             'rating': 5,
#             'title': "منشار ممتاز للاستخدام المنزلي",
#             'content': "اشتريته قبل شهرين واستخدمته في قص الخشب والأنابيب البلاستيكية. الشفرة حادة جداً والمقبض مريح.",
#             'quality_rating': 5,
#             'value_rating': 5,
#             'is_approved': True,
#             'helpful_votes': 8
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: تقييم منشار Stanley")
#
#     # تقييم على صندوق الجوارير
#     review2, created = ProductReview.objects.get_or_create(
#         product=drawer_organizer,
#         user=customer2,  # مستخدم مختلف
#         defaults={
#             'rating': 4,
#             'title': "ممتاز للتنظيم",
#             'content': "صندوق ممتاز لتنظيم البراغي والمسامير. الجوارير شفافة وسهل معرفة المحتويات. العيب الوحيد أن البلاستيك رقيق نوعاً ما.",
#             'quality_rating': 4,
#             'value_rating': 5,
#             'is_approved': True,
#             'helpful_votes': 12
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: تقييم صندوق Ingco")
#
# except Exception as e:
#     print(f"❌ خطأ في إنشاء التقييمات: {e}")
#
# # ==========================================
# # 6. إنشاء الأسئلة والأجوبة
# # ==========================================
# print("\n💬 إنشاء الأسئلة والأجوبة...")
#
# try:
#     question1, created = ProductQuestion.objects.get_or_create(
#         product=spanner_wrench,
#         user=customer3,
#         defaults={
#             'question': "هل المفتاح مناسب للاستخدام مع السيارات؟",
#             'answer': "نعم، مفاتيح Total مصنوعة من الكروم فاناديوم وهي قوية بما يكفي للاستخدام في صيانة السيارات.",
#             'is_answered': True,
#             'answered_by': support_user,
#             'answered_at': timezone.now(),
#             'helpful_votes': 5
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: سؤال عن مفتاح شق رنج")
#
#     question2, created = ProductQuestion.objects.get_or_create(
#         product=metal_plastic_toolbox,
#         user=customer1,
#         defaults={
#             'question': "هل الصندوق مقاوم للماء؟",
#             'answer': "الصندوق مقاوم لرذاذ الماء ولكنه غير مصمم للغمر الكامل في الماء. ننصح بحفظه في مكان جاف.",
#             'is_answered': True,
#             'answered_by': support_user,
#             'answered_at': timezone.now(),
#             'helpful_votes': 3
#         }
#     )
#     print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: سؤال عن صندوق DeWalt")
#
# except Exception as e:
#     print(f"❌ خطأ في إنشاء الأسئلة: {e}")
#
# # ==========================================
# # 7. ربط المنتجات ذات الصلة
# # ==========================================
# print("\n🔗 ربط المنتجات ذات الصلة...")
#
# try:
#     # ربط المناشير مع بعضها وصندوق العدة
#     multi_saw.related_products.add(metal_saw, metal_plastic_toolbox)
#     print("  ✅ تم ربط منشار Stanley مع منتجات ذات صلة")
#
#     # ربط المفكات مع المفاتيح وصندوق التنظيم
#     screwdriver_set.related_products.add(spanner_wrench, drawer_organizer)
#     print("  ✅ تم ربط طقم المفكات مع منتجات ذات صلة")
#
#     # ربط صناديق العدة مع بعضها
#     metal_plastic_toolbox.related_products.add(drawer_organizer)
#     print("  ✅ تم ربط صناديق العدة")
#
# except Exception as e:
#     print(f"❌ خطأ في ربط المنتجات: {e}")
#
# # ==========================================
# # 8. تحديث إحصائيات التصنيفات
# # ==========================================
# print("\n📊 تحديث إحصائيات التصنيفات...")
#
# try:
#     for category in Category.objects.all():
#         category.update_products_count()
#     print("  ✅ تم تحديث جميع إحصائيات التصنيفات")
# except Exception as e:
#     print(f"❌ خطأ في تحديث الإحصائيات: {e}")
#
# # ==========================================
# # ملخص النتائج
# # ==========================================
# print("\n" + "=" * 50)
# print("📊 ملخص الإدخال:")
# print("=" * 50)
# print(f"✅ التصنيفات: {Category.objects.count()}")
# print(f"✅ العلامات التجارية: {Brand.objects.count()}")
# print(f"✅ المنتجات: {Product.objects.count()}")
# print(f"✅ متغيرات المنتجات: {ProductVariant.objects.count()}")
# print(f"✅ التقييمات: {ProductReview.objects.count()}")
# print(f"✅ الأسئلة: {ProductQuestion.objects.count()}")
# print(f"✅ العروض: {ProductDiscount.objects.count()}")
# print("=" * 50)
# print("✨ تم إدخال جميع البيانات بنجاح!")


# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
سكريبت إضافة بيانات موسعة لـ ESCO
يحتوي على فئات ومنتجات إضافية مع مميزات جديدة
لتشغيل السكريبت:
python manage.py shell < import_esco_extended_data.py
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

print("🚀 بدء إضافة البيانات الموسعة لـ ESCO...")

# الحصول على المستخدمين الموجودين
admin_user = User.objects.get(username='admin')
support_user = User.objects.get(username='support')
customer1 = User.objects.get(username='ahmed_ali')
customer2 = User.objects.get(username='sara_mohammed')
customer3 = User.objects.get(username='khalid_omar')

# إنشاء مستخدمين إضافيين
try:
    customer4, created = User.objects.get_or_create(
        username='mona_hassan',
        defaults={'email': 'mona@example.com'}
    )
    if created:
        customer4.set_password('customer123')
        customer4.save()

    customer5, created = User.objects.get_or_create(
        username='faisal_nasser',
        defaults={'email': 'faisal@example.com'}
    )
    if created:
        customer5.set_password('customer123')
        customer5.save()

    print("✅ تم إنشاء المستخدمين الإضافيين")
except Exception as e:
    print(f"❌ خطأ في إنشاء المستخدمين: {e}")

# ==========================================
# 1. إنشاء التصنيفات الجديدة
# ==========================================
print("\n📁 إنشاء التصنيفات الجديدة...")

try:
    # التصنيف الرئيسي - أدوات كهربائية
    power_tools, created = Category.objects.get_or_create(
        slug="power-tools",
        defaults={
            'name': "الأدوات الكهربائية",
            'name_en': "Power Tools",
            'level': 0,
            'icon': "fas fa-bolt",
            'is_featured': True,
            'sort_order': 2,
            'description': "أدوات كهربائية احترافية للاستخدام المنزلي والصناعي"
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {power_tools.name}")

    # الفئات الفرعية للأدوات الكهربائية
    drills, created = Category.objects.get_or_create(
        slug="drills",
        defaults={
            'name': "المثاقب الكهربائية",
            'name_en': "Electric Drills",
            'parent': power_tools,
            'level': 1,
            'sort_order': 1
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {drills.name}")

    grinders, created = Category.objects.get_or_create(
        slug="grinders",
        defaults={
            'name': "أجهزة الطحن والصنفرة",
            'name_en': "Grinders and Sanders",
            'parent': power_tools,
            'level': 1,
            'sort_order': 2
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {grinders.name}")

    # التصنيف الرئيسي - معدات السلامة
    safety_equipment, created = Category.objects.get_or_create(
        slug="safety-equipment",
        defaults={
            'name': "معدات السلامة",
            'name_en': "Safety Equipment",
            'level': 0,
            'icon': "fas fa-hard-hat",
            'is_featured': True,
            'sort_order': 3,
            'description': "معدات الحماية الشخصية والسلامة المهنية"
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {safety_equipment.name}")

    # الفئات الفرعية لمعدات السلامة
    helmets, created = Category.objects.get_or_create(
        slug="safety-helmets",
        defaults={
            'name': "خوذات السلامة",
            'name_en': "Safety Helmets",
            'parent': safety_equipment,
            'level': 1,
            'sort_order': 1
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {helmets.name}")

    gloves, created = Category.objects.get_or_create(
        slug="work-gloves",
        defaults={
            'name': "قفازات العمل",
            'name_en': "Work Gloves",
            'parent': safety_equipment,
            'level': 1,
            'sort_order': 2
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {gloves.name}")

    safety_shoes, created = Category.objects.get_or_create(
        slug="safety-shoes",
        defaults={
            'name': "أحذية السلامة",
            'name_en': "Safety Shoes",
            'parent': safety_equipment,
            'level': 1,
            'sort_order': 3
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {safety_shoes.name}")

    # التصنيف الرئيسي - أدوات القياس
    measuring_tools, created = Category.objects.get_or_create(
        slug="measuring-tools",
        defaults={
            'name': "أدوات القياس",
            'name_en': "Measuring Tools",
            'level': 0,
            'icon': "fas fa-ruler",
            'sort_order': 4,
            'description': "أدوات قياس دقيقة للاستخدام المهني"
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {measuring_tools.name}")

    tape_measures, created = Category.objects.get_or_create(
        slug="tape-measures",
        defaults={
            'name': "أشرطة القياس",
            'name_en': "Tape Measures",
            'parent': measuring_tools,
            'level': 1,
            'sort_order': 1
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {tape_measures.name}")

    levels, created = Category.objects.get_or_create(
        slug="levels",
        defaults={
            'name': "ميزان الماء",
            'name_en': "Spirit Levels",
            'parent': measuring_tools,
            'level': 1,
            'sort_order': 2
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {levels.name}")

except Exception as e:
    print(f"❌ خطأ في إنشاء التصنيفات: {e}")

# ==========================================
# 2. إضافة علامات تجارية جديدة
# ==========================================
print("\n🏷️ إضافة علامات تجارية جديدة...")

try:
    bosch, created = Brand.objects.get_or_create(
        slug="bosch",
        defaults={
            'name': "Bosch",
            'name_en': "Bosch",
            'country': "ألمانيا",
            'description': "رائدة في صناعة الأدوات الكهربائية الاحترافية",
            'is_featured': True
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: Bosch")

    makita, created = Brand.objects.get_or_create(
        slug="makita",
        defaults={
            'name': "Makita",
            'name_en': "Makita",
            'country': "اليابان",
            'description': "جودة يابانية في الأدوات الكهربائية",
            'is_featured': True
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: Makita")

    milwaukee, created = Brand.objects.get_or_create(
        slug="milwaukee",
        defaults={
            'name': "Milwaukee",
            'name_en': "Milwaukee",
            'country': "الولايات المتحدة",
            'description': "أدوات احترافية للاستخدام الشاق"
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: Milwaukee")

    threeem, created = Brand.objects.get_or_create(
        slug="3m",
        defaults={
            'name': "3M",
            'name_en': "3M",
            'country': "الولايات المتحدة",
            'description': "رائدة في معدات السلامة والحماية"
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: 3M")

except Exception as e:
    print(f"❌ خطأ في إنشاء العلامات التجارية: {e}")

# ==========================================
# 3. إنشاء المنتجات الجديدة مع الألوان
# ==========================================
print("\n📦 إنشاء المنتجات الجديدة...")

# منتج 1: مثقاب Bosch مع ألوان متعددة
try:
    bosch_drill, created = Product.objects.get_or_create(
        sku="BOSCH-PSB-18",
        defaults={
            'name': "مثقاب Bosch PSB 18 LI-2 لاسلكي",
            'name_en': "Bosch PSB 18 LI-2 Cordless Drill",
            'slug': "bosch-psb-18-li-2-cordless-drill",
            'category': drills,
            'brand': bosch,
            'base_price': Decimal('125.00'),
            'compare_price': Decimal('150.00'),
            'created_by': admin_user,
            'description': """مثقاب لاسلكي احترافي من Bosch
- بطارية ليثيوم أيون 18 فولت
- سرعتان للدوران
- 20 إعداد للعزم + وضع الثقب
- إضاءة LED مدمجة
- مقبض مريح مضاد للانزلاق""",
            'specifications': {
                "الجهد": "18 فولت",
                "سعة البطارية": "2.0 أمبير",
                "السرعة القصوى": "1350 دورة/دقيقة",
                "العزم الأقصى": "38 نيوتن متر",
                "قطر الظرف": "13 مم",
                "الوزن": "1.3 كجم مع البطارية",
                "عدد البطاريات": "2",
                "وقت الشحن": "60 دقيقة"
            },
            'features': [
                "نظام ECP لحماية البطارية",
                "تقنية Syneon Chip للكفاءة",
                "ضمان 3 سنوات",
                "حقيبة حمل صلبة"
            ],
            'stock_quantity': 0,
            'weight': Decimal('2.5'),
            'warranty_period': "3 سنوات"
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {bosch_drill.name}")

    # إنشاء متغيرات بألوان مختلفة
    if created:
        drill_variants = [
            {
                'name': "مثقاب Bosch PSB 18 - أخضر",
                'sku': "BOSCH-PSB-18-GREEN",
                'attributes': {
                    "اللون": "أخضر Bosch الكلاسيكي",
                    "المحتويات": "مثقاب + 2 بطارية + شاحن + حقيبة",
                    "كود اللون": "#00684B"
                },
                'base_price': Decimal('125.00'),
                'stock_quantity': 15
            },
            {
                'name': "مثقاب Bosch PSB 18 - أزرق احترافي",
                'sku': "BOSCH-PSB-18-BLUE",
                'attributes': {
                    "اللون": "أزرق احترافي",
                    "المحتويات": "مثقاب + 2 بطارية + شاحن + حقيبة",
                    "كود اللون": "#0A4C8F",
                    "ملاحظة": "إصدار احترافي"
                },
                'base_price': Decimal('135.00'),
                'stock_quantity': 10
            },
            {
                'name': "مثقاب Bosch PSB 18 - طقم كامل",
                'sku': "BOSCH-PSB-18-FULLKIT",
                'attributes': {
                    "اللون": "أخضر",
                    "المحتويات": "مثقاب + 2 بطارية + شاحن + حقيبة + طقم 50 قطعة",
                    "الإضافات": "50 قطعة (لقم ثقب، بت مفك، مفاتيح)"
                },
                'base_price': Decimal('165.00'),
                'stock_quantity': 8
            }
        ]

        for variant_data in drill_variants:
            variant, _ = ProductVariant.objects.get_or_create(
                product=bosch_drill,
                sku=variant_data['sku'],
                defaults=variant_data
            )
            print(f"    ✅ متغير: {variant.name}")

except Exception as e:
    print(f"❌ خطأ في إنشاء مثقاب Bosch: {e}")

# منتج 2: جلاخة Makita مع أحجام مختلفة
try:
    makita_grinder, created = Product.objects.get_or_create(
        sku="MAK-GA4530",
        defaults={
            'name': "جلاخة زاوية Makita",
            'name_en': "Makita Angle Grinder",
            'slug': "makita-angle-grinder",
            'category': grinders,
            'brand': makita,
            'base_price': Decimal('85.00'),
            'created_by': admin_user,
            'description': """جلاخة زاوية احترافية من Makita
- محرك قوي 720 واط
- حماية من الغبار المتطورة
- مقبض جانبي قابل للتعديل
- نظام تبديل القرص السريع""",
            'specifications': {
                "القدرة": "720 واط",
                "السرعة": "11000 دورة/دقيقة",
                "قطر القرص": "115 مم",
                "الوزن": "1.8 كجم"
            },
            'stock_quantity': 0
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {makita_grinder.name}")

    # متغيرات بأحجام مختلفة
    if created:
        grinder_variants = [
            {
                'name': "جلاخة Makita 4.5 بوصة (115مم)",
                'sku': "MAK-GA4530-115",
                'attributes': {
                    "قطر القرص": "115 مم (4.5 بوصة)",
                    "القدرة": "720 واط",
                    "الاستخدام": "للأعمال الخفيفة والمتوسطة"
                },
                'base_price': Decimal('85.00'),
                'stock_quantity': 20
            },
            {
                'name': "جلاخة Makita 5 بوصة (125مم)",
                'sku': "MAK-GA5030-125",
                'attributes': {
                    "قطر القرص": "125 مم (5 بوصة)",
                    "القدرة": "720 واط",
                    "الاستخدام": "للأعمال المتوسطة"
                },
                'base_price': Decimal('95.00'),
                'stock_quantity': 15
            },
            {
                'name': "جلاخة Makita 7 بوصة (180مم)",
                'sku': "MAK-GA7020-180",
                'attributes': {
                    "قطر القرص": "180 مم (7 بوصة)",
                    "القدرة": "2200 واط",
                    "الاستخدام": "للأعمال الشاقة"
                },
                'base_price': Decimal('165.00'),
                'stock_quantity': 10
            }
        ]

        for variant_data in grinder_variants:
            variant, _ = ProductVariant.objects.get_or_create(
                product=makita_grinder,
                sku=variant_data['sku'],
                defaults=variant_data
            )
            print(f"    ✅ متغير: {variant.name}")

except Exception as e:
    print(f"❌ خطأ في إنشاء جلاخة Makita: {e}")

# منتج 3: خوذة سلامة 3M مع ألوان مختلفة
try:
    safety_helmet, created = Product.objects.get_or_create(
        sku="3M-H700",
        defaults={
            'name': "خوذة سلامة 3M H-700",
            'name_en': "3M H-700 Safety Helmet",
            'slug': "3m-h700-safety-helmet",
            'category': helmets,
            'brand': threeem,
            'base_price': Decimal('18.00'),
            'created_by': admin_user,
            'description': """خوذة سلامة احترافية من 3M
- مطابقة للمواصفات الأوروبية EN397
- نظام تعليق 4 نقاط للراحة
- فتحات تهوية للتبريد
- حزام ذقن قابل للتعديل""",
            'specifications': {
                "المادة": "ABS عالي الجودة",
                "المعايير": "EN397, ANSI Z89.1",
                "التعليق": "4 نقاط",
                "الحجم": "قابل للتعديل 52-64 سم",
                "الوزن": "350 جرام"
            },
            'features': [
                "مقاومة للصدمات",
                "عزل كهربائي حتى 440 فولت",
                "مقاومة للحرارة",
                "إمكانية إضافة واقي الوجه"
            ],
            'stock_quantity': 0,
            'weight': Decimal('0.35')
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {safety_helmet.name}")

    # متغيرات بألوان مختلفة للسلامة
    if created:
        helmet_colors = [
            {
                'name': "خوذة 3M H-700 - أبيض",
                'sku': "3M-H700-WHITE",
                'attributes': {
                    "اللون": "أبيض",
                    "كود اللون": "#FFFFFF",
                    "الاستخدام": "مشرفين ومهندسين"
                },
                'base_price': Decimal('18.00'),
                'stock_quantity': 30
            },
            {
                'name': "خوذة 3M H-700 - أصفر",
                'sku': "3M-H700-YELLOW",
                'attributes': {
                    "اللون": "أصفر",
                    "كود اللون": "#FFD700",
                    "الاستخدام": "عمال عامين"
                },
                'base_price': Decimal('18.00'),
                'stock_quantity': 50
            },
            {
                'name': "خوذة 3M H-700 - أحمر",
                'sku': "3M-H700-RED",
                'attributes': {
                    "اللون": "أحمر",
                    "كود اللون": "#FF0000",
                    "الاستخدام": "مسؤولي السلامة"
                },
                'base_price': Decimal('18.00'),
                'stock_quantity': 20
            },
            {
                'name': "خوذة 3M H-700 - أزرق",
                'sku': "3M-H700-BLUE",
                'attributes': {
                    "اللون": "أزرق",
                    "كود اللون": "#0000FF",
                    "الاستخدام": "زوار وضيوف"
                },
                'base_price': Decimal('18.00'),
                'stock_quantity': 25
            },
            {
                'name': "خوذة 3M H-700 - أخضر",
                'sku': "3M-H700-GREEN",
                'attributes': {
                    "اللون": "أخضر",
                    "كود اللون": "#008000",
                    "الاستخدام": "مسؤولي البيئة والسلامة"
                },
                'base_price': Decimal('18.00'),
                'stock_quantity': 15
            }
        ]

        for color_data in helmet_colors:
            variant, _ = ProductVariant.objects.get_or_create(
                product=safety_helmet,
                sku=color_data['sku'],
                defaults=color_data
            )
            print(f"    ✅ متغير: {variant.name}")

except Exception as e:
    print(f"❌ خطأ في إنشاء خوذة السلامة: {e}")

# منتج 4: قفازات عمل مع مقاسات وأنواع
try:
    work_gloves, created = Product.objects.get_or_create(
        sku="MILWAUKEE-GLOVES",
        defaults={
            'name': "قفازات عمل Milwaukee",
            'name_en': "Milwaukee Work Gloves",
            'slug': "milwaukee-work-gloves",
            'category': gloves,
            'brand': milwaukee,
            'base_price': Decimal('12.00'),
            'created_by': admin_user,
            'description': """قفازات عمل احترافية من Milwaukee
- حماية فائقة مع مرونة عالية
- راحة يد مبطنة
- أطراف أصابع معززة
- قابلة للغسل""",
            'specifications': {
                "المادة الخارجية": "جلد صناعي",
                "البطانة": "قماش تنفس",
                "المعايير": "EN388"
            },
            'stock_quantity': 0
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {work_gloves.name}")

    # متغيرات بمقاسات وأنواع مختلفة
    if created:
        glove_variants = [
            # قفازات جلد - مقاسات مختلفة
            {
                'name': "قفازات Milwaukee جلد - مقاس M",
                'sku': "MIL-GLOVE-LEATHER-M",
                'attributes': {
                    "النوع": "جلد كامل",
                    "المقاس": "M (متوسط)",
                    "محيط اليد": "20-22 سم",
                    "اللون": "بني"
                },
                'base_price': Decimal('15.00'),
                'stock_quantity': 25
            },
            {
                'name': "قفازات Milwaukee جلد - مقاس L",
                'sku': "MIL-GLOVE-LEATHER-L",
                'attributes': {
                    "النوع": "جلد كامل",
                    "المقاس": "L (كبير)",
                    "محيط اليد": "22-24 سم",
                    "اللون": "بني"
                },
                'base_price': Decimal('15.00'),
                'stock_quantity': 30
            },
            {
                'name': "قفازات Milwaukee جلد - مقاس XL",
                'sku': "MIL-GLOVE-LEATHER-XL",
                'attributes': {
                    "النوع": "جلد كامل",
                    "المقاس": "XL (كبير جداً)",
                    "محيط اليد": "24-26 سم",
                    "اللون": "بني"
                },
                'base_price': Decimal('15.00'),
                'stock_quantity': 20
            },
            # قفازات ميكانيك
            {
                'name': "قفازات Milwaukee ميكانيك - مقاس L",
                'sku': "MIL-GLOVE-MECH-L",
                'attributes': {
                    "النوع": "ميكانيك",
                    "المقاس": "L (كبير)",
                    "اللون": "أحمر وأسود",
                    "المميزات": "حماية المفاصل"
                },
                'base_price': Decimal('22.00'),
                'stock_quantity': 15
            },
            # قفازات مقاومة للقطع
            {
                'name': "قفازات Milwaukee مقاومة للقطع - مقاس L",
                'sku': "MIL-GLOVE-CUT-L",
                'attributes': {
                    "النوع": "مقاومة للقطع Level 5",
                    "المقاس": "L (كبير)",
                    "اللون": "رمادي",
                    "المعيار": "EN388 - 5544"
                },
                'base_price': Decimal('28.00'),
                'stock_quantity': 10
            }
        ]

        for glove_data in glove_variants:
            variant, _ = ProductVariant.objects.get_or_create(
                product=work_gloves,
                sku=glove_data['sku'],
                defaults=glove_data
            )
            print(f"    ✅ متغير: {variant.name}")

except Exception as e:
    print(f"❌ خطأ في إنشاء قفازات العمل: {e}")

# منتج 5: حذاء سلامة DeWalt
try:
    safety_boot, created = Product.objects.get_or_create(
        sku="DEW-TITANIUM",
        defaults={
            'name': "حذاء سلامة DeWalt Titanium",
            'name_en': "DeWalt Titanium Safety Boot",
            'slug': "dewalt-titanium-safety-boot",
            'category': safety_shoes,
            'brand': dewalt,
            'base_price': Decimal('65.00'),
            'compare_price': Decimal('80.00'),
            'created_by': admin_user,
            'description': """حذاء سلامة احترافي من DeWalt
- مقدمة فولاذية للحماية 200 جول
- نعل مقاوم للانزلاق والزيوت
- مقاوم للماء
- راحة فائقة طوال اليوم""",
            'specifications': {
                "المعايير": "S3 SRC",
                "مقدمة الحماية": "فولاذ 200 جول",
                "النعل": "مطاط مقاوم للانزلاق",
                "الجزء العلوي": "جلد مقاوم للماء",
                "البطانة": "قماش تنفس"
            },
            'features': [
                "مقاوم للماء",
                "نعل مضاد للثقب",
                "مقاوم للكهرباء الساكنة",
                "نعل ممتص للصدمات"
            ],
            'stock_quantity': 0,
            'weight': Decimal('1.2')
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {safety_boot.name}")

    # متغيرات بمقاسات مختلفة
    if created:
        boot_sizes = [40, 41, 42, 43, 44, 45, 46]
        colors = [
            {"name": "بني", "code": "#8B4513", "sku_suffix": "BRN"},
            {"name": "أسود", "code": "#000000", "sku_suffix": "BLK"}
        ]

        for size in boot_sizes:
            for color in colors:
                variant, _ = ProductVariant.objects.get_or_create(
                    product=safety_boot,
                    sku=f"DEW-TITAN-{size}-{color['sku_suffix']}",
                    defaults={
                        'name': f"حذاء DeWalt Titanium - مقاس {size} - {color['name']}",
                        'attributes': {
                            "المقاس": str(size),
                            "اللون": color['name'],
                            "كود اللون": color['code'],
                            "المقاس الأوروبي": f"EU {size}",
                            "المقاس الأمريكي": f"US {size - 33}"
                        },
                        'base_price': Decimal('65.00'),
                        'stock_quantity': 5 if size in [42, 43, 44] else 3
                    }
                )
                print(f"    ✅ متغير: مقاس {size} - {color['name']}")

except Exception as e:
    print(f"❌ خطأ في إنشاء حذاء السلامة: {e}")

# منتج 6: شريط قياس Stanley FatMax
try:
    tape_measure, created = Product.objects.get_or_create(
        sku="STAN-FATMAX",
        defaults={
            'name': "شريط قياس Stanley FatMax",
            'name_en': "Stanley FatMax Tape Measure",
            'slug': "stanley-fatmax-tape-measure",
            'category': tape_measures,
            'brand': stanley,
            'base_price': Decimal('12.00'),
            'created_by': admin_user,
            'description': """شريط قياس احترافي Stanley FatMax
- شفرة مطلية بـ Mylar للمتانة
- خطاف مغناطيسي
- قفل شفرة أوتوماتيكي
- علبة مطاطية مقاومة للصدمات""",
            'specifications': {
                "عرض الشفرة": "32 مم",
                "طلاء الشفرة": "Mylar",
                "نوع القفل": "أوتوماتيكي",
                "الخطاف": "مغناطيسي 3 براشي"
            },
            'stock_quantity': 0
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {tape_measure.name}")

    # متغيرات بأطوال مختلفة
    if created:
        tape_lengths = [
            {
                'length': "3m",
                'sku': "STAN-FM-3M",
                'price': "12.00",
                'stock': 40
            },
            {
                'length': "5m",
                'sku': "STAN-FM-5M",
                'price': "15.00",
                'stock': 35
            },
            {
                'length': "8m",
                'sku': "STAN-FM-8M",
                'price': "22.00",
                'stock': 25
            },
            {
                'length': "10m",
                'sku': "STAN-FM-10M",
                'price': "28.00",
                'stock': 15
            }
        ]

        for tape_data in tape_lengths:
            variant, _ = ProductVariant.objects.get_or_create(
                product=tape_measure,
                sku=tape_data['sku'],
                defaults={
                    'name': f"شريط Stanley FatMax - {tape_data['length']}",
                    'attributes': {
                        "الطول": tape_data['length'],
                        "الوصول": f"حتى {tape_data['length'][:-1]} متر",
                        "العرض": "32 مم"
                    },
                    'base_price': Decimal(tape_data['price']),
                    'stock_quantity': tape_data['stock']
                }
            )
            print(f"    ✅ متغير: {variant.name}")

except Exception as e:
    print(f"❌ خطأ في إنشاء شريط القياس: {e}")

# منتج 7: ميزان ماء Bosch
try:
    spirit_level, created = Product.objects.get_or_create(
        sku="BOSCH-LEVEL",
        defaults={
            'name': "ميزان ماء Bosch Professional",
            'name_en': "Bosch Professional Spirit Level",
            'slug': "bosch-professional-spirit-level",
            'category': levels,
            'brand': bosch,
            'base_price': Decimal('35.00'),
            'created_by': admin_user,
            'description': """ميزان ماء احترافي من Bosch
- دقة عالية 0.5 مم/م
- 3 فقاعات (أفقي، عمودي، 45°)
- إطار ألومنيوم مقوى
- أسطح مغناطيسية""",
            'specifications': {
                "الدقة": "0.5 مم/م",
                "عدد الفقاعات": "3",
                "المادة": "ألومنيوم",
                "مغناطيسي": "نعم"
            },
            'stock_quantity': 0
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: {spirit_level.name}")

    # متغيرات بأطوال مختلفة
    if created:
        level_variants = [
            {
                'name': "ميزان Bosch 40 سم",
                'sku': "BOSCH-LVL-40",
                'attributes': {
                    "الطول": "40 سم",
                    "عدد الفقاعات": "2",
                    "الوزن": "250 جرام"
                },
                'base_price': Decimal('35.00'),
                'stock_quantity': 20
            },
            {
                'name': "ميزان Bosch 60 سم",
                'sku': "BOSCH-LVL-60",
                'attributes': {
                    "الطول": "60 سم",
                    "عدد الفقاعات": "3",
                    "الوزن": "380 جرام"
                },
                'base_price': Decimal('45.00'),
                'stock_quantity': 15
            },
            {
                'name': "ميزان Bosch 100 سم",
                'sku': "BOSCH-LVL-100",
                'attributes': {
                    "الطول": "100 سم",
                    "عدد الفقاعات": "3",
                    "الوزن": "620 جرام"
                },
                'base_price': Decimal('65.00'),
                'stock_quantity': 10
            },
            {
                'name': "ميزان Bosch 200 سم",
                'sku': "BOSCH-LVL-200",
                'attributes': {
                    "الطول": "200 سم",
                    "عدد الفقاعات": "3",
                    "الوزن": "1.2 كجم",
                    "مع حقيبة": "نعم"
                },
                'base_price': Decimal('120.00'),
                'stock_quantity': 5
            }
        ]

        for level_data in level_variants:
            variant, _ = ProductVariant.objects.get_or_create(
                product=spirit_level,
                sku=level_data['sku'],
                defaults=level_data
            )
            print(f"    ✅ متغير: {variant.name}")

except Exception as e:
    print(f"❌ خطأ في إنشاء ميزان الماء: {e}")

# ==========================================
# 4. إنشاء عروض وخصومات متنوعة
# ==========================================
print("\n🎯 إنشاء عروض وخصومات متنوعة...")

try:
    # عرض على الأدوات الكهربائية
    power_tools_offer, created = ProductDiscount.objects.get_or_create(
        code="POWER25",
        defaults={
            'name': "خصم 25% على الأدوات الكهربائية",
            'discount_type': "percentage",
            'value': Decimal('25'),
            'application_type': "category",
            'category': power_tools,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=14),
            'is_active': True,
            'created_by': admin_user,
            'description': "احصل على خصم 25% على جميع الأدوات الكهربائية"
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: عرض الأدوات الكهربائية")

    # عرض على معدات السلامة (خصم كمية)
    safety_quantity_discount, created = ProductDiscount.objects.get_or_create(
        code="SAFETY_BULK",
        defaults={
            'name': "خصم الكمية على معدات السلامة",
            'discount_type': "quantity_based",
            'value': Decimal('0'),  # سيتم تحديد القيمة حسب الكمية
            'application_type': "category",
            'category': safety_equipment,
            'quantity_tiers': {
                "tiers": [
                    {"min_qty": 10, "max_qty": 19, "discount": 10},
                    {"min_qty": 20, "max_qty": 49, "discount": 15},
                    {"min_qty": 50, "max_qty": None, "discount": 20}
                ]
            },
            'start_date': timezone.now(),
            'is_active': True,
            'created_by': admin_user,
            'description': "خصومات خاصة للشراء بالجملة"
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: خصم الكمية على معدات السلامة")

    # عرض حزمة (Bundle)
    bundle_offer, created = ProductDiscount.objects.get_or_create(
        code="PRO_BUNDLE",
        defaults={
            'name': "حزمة المحترفين - وفر 50 دينار",
            'discount_type': "bundle",
            'value': Decimal('50'),
            'application_type': "bundle_products",
            'bundle_products': [bosch_drill.id, makita_grinder.id, safety_helmet.id],
            'bundle_description': "اشتري مثقاب Bosch + جلاخة Makita + خوذة سلامة واحصل على خصم 50 دينار",
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=30),
            'is_active': True,
            'created_by': admin_user
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: عرض الحزمة")

    # خصم للعملاء الجدد
    new_customer_discount, created = ProductDiscount.objects.get_or_create(
        code="WELCOME15",
        defaults={
            'name': "خصم ترحيبي 15% للعملاء الجدد",
            'discount_type': "percentage",
            'value': Decimal('15'),
            'application_type': "first_purchase",
            'max_discount_amount': Decimal('20.00'),
            'usage_limit': 1,
            'usage_limit_per_customer': 1,
            'start_date': timezone.now(),
            'is_active': True,
            'created_by': admin_user
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: خصم العملاء الجدد")

except Exception as e:
    print(f"❌ خطأ في إنشاء العروض: {e}")

# ==========================================
# 5. إنشاء تقييمات متنوعة
# ==========================================
print("\n⭐ إنشاء تقييمات متنوعة...")

try:
    # تقييمات على المثقاب
    review_drill1, created = ProductReview.objects.get_or_create(
        product=bosch_drill,
        user=customer1,
        defaults={
            'rating': 5,
            'title': "أفضل مثقاب استخدمته",
            'content': """اشتريت المثقاب قبل 3 أشهر وأستخدمه يومياً تقريباً. 
البطارية تدوم طويلاً والعزم قوي جداً. 
نصيحة: احصلوا على الطقم الكامل مع اللقم الإضافية.""",
            'quality_rating': 5,
            'value_rating': 4,
            'is_approved': True,
            'helpful_votes': 24,
            'verified_purchase': True,
            'pros': ["بطارية قوية", "عزم ممتاز", "خفيف الوزن", "ضمان 3 سنوات"],
            'cons': ["السعر مرتفع قليلاً", "الحقيبة بلاستيكية وليست معدنية"]
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: تقييم المثقاب 1")

    review_drill2, created = ProductReview.objects.get_or_create(
        product=bosch_drill,
        user=customer4,
        defaults={
            'rating': 4,
            'title': "ممتاز للاستخدام المنزلي",
            'content': "مثقاب قوي ومناسب جداً للأعمال المنزلية. استخدمته في تركيب الرفوف والستائر.",
            'quality_rating': 5,
            'value_rating': 3,
            'is_approved': True,
            'helpful_votes': 8,
            'verified_purchase': True
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: تقييم المثقاب 2")

    # تقييم على خوذة السلامة
    review_helmet, created = ProductReview.objects.get_or_create(
        product=safety_helmet,
        user=customer5,
        defaults={
            'rating': 5,
            'title': "خوذة ممتازة ومريحة",
            'content': """أعمل في موقع بناء وهذه الخوذة مريحة جداً حتى مع ارتدائها طوال اليوم.
التهوية ممتازة ولا تسبب التعرق مثل الخوذات الأخرى.
اللون الأصفر واضح جداً للسلامة.""",
            'quality_rating': 5,
            'value_rating': 5,
            'is_approved': True,
            'helpful_votes': 15,
            'verified_purchase': True,
            'pros': ["خفيفة الوزن", "تهوية ممتازة", "سهلة التعديل"],
            'cons': []
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: تقييم الخوذة")

    # تقييم على القفازات
    review_gloves, created = ProductReview.objects.get_or_create(
        product=work_gloves,
        user=customer2,
        defaults={
            'rating': 4,
            'title': "قفازات متينة وعملية",
            'content': """القفازات ممتازة للأعمال الثقيلة. الجلد قوي ومتين.
النوع المقاوم للقطع ممتاز فعلاً وحماني من إصابات كثيرة.
العيب الوحيد أنها تحتاج وقت لتلين في البداية.""",
            'quality_rating': 4,
            'value_rating': 4,
            'is_approved': True,
            'helpful_votes': 12,
            'verified_purchase': True
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: تقييم القفازات")

    # تقييم سلبي للتنوع
    review_negative, created = ProductReview.objects.get_or_create(
        product=makita_grinder,
        user=customer3,
        defaults={
            'rating': 2,
            'title': "جودة أقل من المتوقع",
            'content': """للأسف الجلاخة لم تكن بالجودة المتوقعة من Makita.
بدأت تصدر أصوات غريبة بعد شهر من الاستخدام.
خدمة العملاء كانت جيدة وتم استبدالها.""",
            'quality_rating': 2,
            'value_rating': 2,
            'is_approved': True,
            'helpful_votes': 3,
            'verified_purchase': True,
            'pros': ["خدمة عملاء جيدة"],
            'cons': ["صوت عالي", "اهتزاز قوي", "توقفت عن العمل بعد شهر"]
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: تقييم سلبي")

except Exception as e:
    print(f"❌ خطأ في إنشاء التقييمات: {e}")

# ==========================================
# 6. إنشاء أسئلة وأجوبة إضافية
# ==========================================
print("\n💬 إنشاء أسئلة وأجوبة إضافية...")

try:
    # أسئلة على المثقاب
    q1, created = ProductQuestion.objects.get_or_create(
        product=bosch_drill,
        user=customer2,
        defaults={
            'question': "هل يمكن استخدام المثقاب للخرسانة؟",
            'answer': """نعم، يمكن استخدام المثقاب للخرسانة ولكن بشكل محدود. 
المثقاب يحتوي على وضع الطرق (Hammer) ومناسب للثقوب الصغيرة في الخرسانة حتى 10مم.
للاستخدام المكثف في الخرسانة ننصح بمثقاب دقاق (Rotary Hammer) مخصص.""",
            'is_answered': True,
            'answered_by': support_user,
            'answered_at': timezone.now(),
            'helpful_votes': 18
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: سؤال المثقاب")

    # سؤال على معدات السلامة
    q2, created = ProductQuestion.objects.get_or_create(
        product=safety_helmet,
        user=customer4,
        defaults={
            'question': "ما الفرق بين ألوان الخوذات؟",
            'answer': """ألوان الخوذات لها دلالات في مواقع العمل:
- الأبيض: للمهندسين والمشرفين
- الأصفر: للعمال العامين
- الأحمر: لمسؤولي السلامة والإطفاء
- الأزرق: للزوار والفنيين
- الأخضر: لمسؤولي البيئة والسلامة
- البرتقالي: لمراقبي المرور

يمكنك اختيار أي لون حسب سياسة موقع العمل لديك.""",
            'is_answered': True,
            'answered_by': support_user,
            'answered_at': timezone.now(),
            'helpful_votes': 35
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: سؤال ألوان الخوذات")

    # سؤال بدون إجابة
    q3, created = ProductQuestion.objects.get_or_create(
        product=tape_measure,
        user=customer5,
        defaults={
            'question': "هل الشريط مقاوم للصدأ في البيئة البحرية؟",
            'is_answered': False,
            'helpful_votes': 2
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: سؤال بدون إجابة")

    # سؤال على الأحذية
    q4, created = ProductQuestion.objects.get_or_create(
        product=safety_boot,
        user=customer1,
        defaults={
            'question': "كيف أختار المقاس المناسب؟",
            'answer': """لاختيار المقاس المناسب:
1. قس قدمك في نهاية اليوم (عندما تكون القدم في أكبر حجم)
2. ارتدي الجوارب التي ستستخدمها مع الحذاء
3. اترك مسافة 1-1.5 سم بين أطول إصبع ومقدمة الحذاء
4. تأكد من عدم وجود ضغط على الجوانب

جدول المقاسات:
- EU 40 = UK 6.5 = US 7.5 (25.5 سم)
- EU 41 = UK 7.5 = US 8.5 (26.5 سم)
- EU 42 = UK 8 = US 9 (27 سم)
- EU 43 = UK 9 = US 10 (27.5 سم)
- EU 44 = UK 10 = US 11 (28.5 سم)
- EU 45 = UK 11 = US 12 (29 سم)""",
            'is_answered': True,
            'answered_by': support_user,
            'answered_at': timezone.now(),
            'helpful_votes': 42
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: سؤال مقاسات الأحذية")

except Exception as e:
    print(f"❌ خطأ في إنشاء الأسئلة: {e}")

# ==========================================
# 7. إنشاء قوائم الأمنيات والمقارنات
# ==========================================
print("\n❤️ إنشاء قوائم أمنيات...")

try:
    # قائمة أمنيات للعميل 1
    wishlist1, created = Wishlist.objects.get_or_create(
        user=customer1,
        product=bosch_drill
    )
    print(f"  {'✅ تم إضافة' if created else '⚠️ موجود مسبقاً'}: مثقاب Bosch لقائمة أمنيات أحمد")

    wishlist2, created = Wishlist.objects.get_or_create(
        user=customer1,
        product=safety_boot
    )
    print(f"  {'✅ تم إضافة' if created else '⚠️ موجود مسبقاً'}: حذاء DeWalt لقائمة أمنيات أحمد")

    # قائمة أمنيات للعميل 2
    wishlist3, created = Wishlist.objects.get_or_create(
        user=customer2,
        product=work_gloves
    )
    print(f"  {'✅ تم إضافة' if created else '⚠️ موجود مسبقاً'}: قفازات Milwaukee لقائمة أمنيات سارة")

except Exception as e:
    print(f"❌ خطأ في إنشاء قوائم الأمنيات: {e}")

# ==========================================
# 8. ربط المنتجات ذات الصلة
# ==========================================
print("\n🔗 ربط المنتجات الجديدة...")

try:
    # ربط الأدوات الكهربائية
    bosch_drill.related_products.add(makita_grinder, tape_measure, safety_helmet)
    print("  ✅ تم ربط مثقاب Bosch مع منتجات ذات صلة")

    # ربط معدات السلامة
    safety_helmet.related_products.add(safety_boot, work_gloves)
    safety_boot.related_products.add(safety_helmet, work_gloves)
    work_gloves.related_products.add(safety_helmet, safety_boot)
    print("  ✅ تم ربط معدات السلامة")

    # ربط أدوات القياس
    tape_measure.related_products.add(spirit_level)
    spirit_level.related_products.add(tape_measure)
    print("  ✅ تم ربط أدوات القياس")

except Exception as e:
    print(f"❌ خطأ في ربط المنتجات: {e}")

# ==========================================
# 9. إنشاء حزم منتجات (Product Bundles)
# ==========================================
print("\n📦 إنشاء حزم المنتجات...")

try:
    # حزمة المبتدئين
    starter_bundle, created = Product.objects.get_or_create(
        sku="BUNDLE-STARTER",
        defaults={
            'name': "حزمة المبتدئين - أدوات أساسية",
            'name_en': "Starter Bundle - Essential Tools",
            'slug': "starter-bundle-essential-tools",
            'category': Category.objects.get(slug="hand-tools"),  # الفئة الرئيسية
            'base_price': Decimal('99.00'),
            'compare_price': Decimal('125.00'),
            'created_by': admin_user,
            'description': """حزمة مثالية للمبتدئين تحتوي على:
- مثقاب لاسلكي Bosch
- طقم مفكات Stanley 6 قطع  
- شريط قياس Stanley FatMax 5m
- صندوق عدة DeWalt 19 بوصة
- قفازات عمل Milwaukee

وفر 26 دينار عند شراء الحزمة!""",
            'is_bundle': True,
            'bundle_items': {
                "items": [
                    {"product_id": bosch_drill.id, "quantity": 1},
                    {"product_id": Product.objects.get(sku="STAN-SD-SET6").id, "quantity": 1},
                    {"product_id": tape_measure.id, "quantity": 1, "variant": "5m"},
                    {"product_id": Product.objects.get(sku="DEW-TB-19").id, "quantity": 1},
                    {"product_id": work_gloves.id, "quantity": 1, "variant": "L"}
                ]
            },
            'stock_quantity': 10,
            'featured': True
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: حزمة المبتدئين")

    # حزمة السلامة الكاملة
    safety_bundle, created = Product.objects.get_or_create(
        sku="BUNDLE-SAFETY",
        defaults={
            'name': "حزمة السلامة الكاملة",
            'name_en': "Complete Safety Bundle",
            'slug': "complete-safety-bundle",
            'category': safety_equipment,
            'base_price': Decimal('85.00'),
            'compare_price': Decimal('105.00'),
            'created_by': admin_user,
            'description': """حزمة السلامة الشاملة تحتوي على:
- خوذة سلامة 3M (اختر اللون)
- حذاء سلامة DeWalt (اختر المقاس)
- قفازات عمل Milwaukee (اختر المقاس)
- نظارات سلامة 3M
- سدادات أذن 3M

كل ما تحتاجه للحماية الكاملة في موقع العمل!""",
            'is_bundle': True,
            'stock_quantity': 15,
            'featured': True
        }
    )
    print(f"  {'✅ تم إنشاء' if created else '⚠️ موجود مسبقاً'}: حزمة السلامة")

except Exception as e:
    print(f"❌ خطأ في إنشاء حزم المنتجات: {e}")

# ==========================================
# 10. تحديث الإحصائيات النهائية
# ==========================================
print("\n📊 تحديث الإحصائيات النهائية...")

try:
    # تحديث عدد المنتجات في التصنيفات
    for category in Category.objects.all():
        category.update_products_count()

    # تحديث متوسط التقييمات للمنتجات
    for product in Product.objects.all():
        reviews = ProductReview.objects.filter(product=product, is_approved=True)
        if reviews.exists():
            product.rating_average = reviews.aggregate(avg=models.Avg('rating'))['avg']
            product.rating_count = reviews.count()
            product.save()

    print("  ✅ تم تحديث جميع الإحصائيات")

except Exception as e:
    print(f"❌ خطأ في تحديث الإحصائيات: {e}")

# ==========================================
# ملخص البيانات المضافة
# ==========================================
print("\n" + "=" * 50)
print("📊 ملخص البيانات المضافة:")
print("=" * 50)
print(f"✅ التصنيفات الجديدة: {Category.objects.filter(created_at__gte=timezone.now() - timedelta(minutes=5)).count()}")
print(
    f"✅ العلامات التجارية الجديدة: {Brand.objects.filter(created_at__gte=timezone.now() - timedelta(minutes=5)).count()}")
print(f"✅ المنتجات الجديدة: {Product.objects.filter(created_at__gte=timezone.now() - timedelta(minutes=5)).count()}")
print(f"✅ إجمالي المتغيرات: {ProductVariant.objects.count()}")
print(f"✅ إجمالي التقييمات: {ProductReview.objects.count()}")
print(f"✅ إجمالي الأسئلة: {ProductQuestion.objects.count()}")
print(f"✅ إجمالي العروض النشطة: {ProductDiscount.objects.filter(is_active=True).count()}")
print("=" * 50)
print("✨ تم إضافة جميع البيانات الموسعة بنجاح!")
print("\n📌 ملاحظة: يمكنك الآن تصفح المنتجات الجديدة مع:")
print("   - متغيرات الألوان (خوذات السلامة)")
print("   - متغيرات المقاسات (الأحذية والقفازات)")
print("   - متغيرات الأحجام (الجلاخات وأشرطة القياس)")
print("   - حزم المنتجات الخاصة")
print("   - عروض متنوعة (خصومات الكمية، حزم، عملاء جدد)")