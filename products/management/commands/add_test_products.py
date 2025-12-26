# products/management/commands/add_test_products.py
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from products.models import Product, Category, Brand
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Add three test products with full Arabic and English information'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')

        # Get or create a test user for created_by field
        test_user, user_created = User.objects.get_or_create(
            email='test@esco.jo',
            defaults={
                'first_name': 'Test',
                'last_name': 'Admin',
                'is_active': True,
            }
        )
        if user_created:
            test_user.set_password('testpass123')
            test_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created test user: {test_user.email}'))

        # Create or get a test category
        category, created = Category.objects.get_or_create(
            slug='electronics',
            defaults={
                'name': 'الإلكترونيات',
                'name_en': 'Electronics',
                'description': 'جميع المنتجات الإلكترونية والأجهزة الذكية',
                'description_en': 'All electronic products and smart devices',
                'is_active': True,
                'meta_title': 'الإلكترونيات - Electronics',
                'meta_description': 'تسوق أفضل المنتجات الإلكترونية بأسعار منافسة',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
        else:
            self.stdout.write(f'Using existing category: {category.name}')

        # Create or get a test brand
        brand, created = Brand.objects.get_or_create(
            slug='tech-brand',
            defaults={
                'name': 'تك برو',
                'name_en': 'Tech Pro',
                'description': 'علامة تجارية رائدة في مجال التكنولوجيا - A leading brand in technology',
                'is_active': True,
                'country': 'الأردن - Jordan',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created brand: {brand.name}'))
        else:
            self.stdout.write(f'Using existing brand: {brand.name}')

        # Test Products Data
        products_data = [
            {
                'name': 'سماعات بلوتوث لاسلكية برو',
                'name_en': 'Pro Wireless Bluetooth Headphones',
                'slug': 'pro-wireless-bluetooth-headphones',
                'sku': 'TEST-BT-001',
                'barcode': '1234567890123',
                'short_description': 'سماعات لاسلكية عالية الجودة مع خاصية إلغاء الضوضاء',
                'description': '''
                <h3>سماعات بلوتوث لاسلكية برو</h3>
                <p>استمتع بتجربة صوتية استثنائية مع سماعاتنا اللاسلكية المتطورة.</p>
                <h4>المميزات الرئيسية:</h4>
                <ul>
                    <li>تقنية إلغاء الضوضاء النشطة (ANC)</li>
                    <li>بطارية تدوم حتى 30 ساعة</li>
                    <li>صوت عالي الدقة Hi-Res Audio</li>
                    <li>اتصال بلوتوث 5.3</li>
                    <li>تصميم مريح للاستخدام الطويل</li>
                </ul>
                <h4>Pro Wireless Bluetooth Headphones</h4>
                <p>Experience exceptional audio with our advanced wireless headphones.</p>
                <h4>Key Features:</h4>
                <ul>
                    <li>Active Noise Cancellation (ANC)</li>
                    <li>Battery lasts up to 30 hours</li>
                    <li>Hi-Res Audio quality</li>
                    <li>Bluetooth 5.3 connectivity</li>
                    <li>Comfortable design for extended use</li>
                </ul>
                ''',
                'base_price': Decimal('89.990'),
                'compare_price': Decimal('129.990'),
                'stock_quantity': 50,
                'weight': Decimal('0.350'),
                'specifications': {
                    'ar': {
                        'نوع الاتصال': 'بلوتوث 5.3',
                        'عمر البطارية': '30 ساعة',
                        'نوع السماعة': 'فوق الأذن',
                        'اللون': 'أسود',
                        'الضمان': 'سنة واحدة'
                    },
                    'en': {
                        'Connectivity': 'Bluetooth 5.3',
                        'Battery Life': '30 hours',
                        'Headphone Type': 'Over-ear',
                        'Color': 'Black',
                        'Warranty': '1 Year'
                    }
                },
                'features': [
                    'إلغاء الضوضاء النشط - Active Noise Cancellation',
                    'صوت محيطي - Surround Sound',
                    'ميكروفون مدمج - Built-in Microphone',
                    'قابل للطي - Foldable Design'
                ],
                'warranty_period': 'سنة واحدة - 1 Year',
                'meta_title': 'سماعات بلوتوث لاسلكية - Pro Wireless Headphones',
                'meta_description': 'اشترِ سماعات بلوتوث لاسلكية برو مع إلغاء الضوضاء وبطارية 30 ساعة',
                'meta_keywords': 'سماعات, بلوتوث, لاسلكية, headphones, bluetooth, wireless',
                'is_featured': True,
                'is_new': True,
            },
            {
                'name': 'ساعة ذكية سبورت برو',
                'name_en': 'Sport Pro Smart Watch',
                'slug': 'sport-pro-smart-watch',
                'sku': 'TEST-SW-002',
                'barcode': '1234567890124',
                'short_description': 'ساعة ذكية رياضية متعددة الوظائف مع تتبع اللياقة البدنية',
                'description': '''
                <h3>ساعة ذكية سبورت برو</h3>
                <p>رفيقك المثالي لنمط حياة صحي ونشط.</p>
                <h4>المميزات الرئيسية:</h4>
                <ul>
                    <li>شاشة AMOLED بحجم 1.4 بوصة</li>
                    <li>مقاومة للماء حتى 50 متر</li>
                    <li>تتبع معدل ضربات القلب</li>
                    <li>GPS مدمج</li>
                    <li>أكثر من 100 وضع رياضي</li>
                    <li>بطارية تدوم 14 يوم</li>
                </ul>
                <h4>Sport Pro Smart Watch</h4>
                <p>Your perfect companion for a healthy and active lifestyle.</p>
                <h4>Key Features:</h4>
                <ul>
                    <li>1.4-inch AMOLED display</li>
                    <li>Water resistant up to 50 meters</li>
                    <li>Heart rate monitoring</li>
                    <li>Built-in GPS</li>
                    <li>Over 100 sport modes</li>
                    <li>14-day battery life</li>
                </ul>
                ''',
                'base_price': Decimal('149.990'),
                'compare_price': Decimal('199.990'),
                'stock_quantity': 35,
                'weight': Decimal('0.045'),
                'specifications': {
                    'ar': {
                        'حجم الشاشة': '1.4 بوصة AMOLED',
                        'مقاومة الماء': '50 متر (5ATM)',
                        'عمر البطارية': '14 يوم',
                        'الاتصال': 'بلوتوث 5.0 + GPS',
                        'التوافق': 'iOS و Android'
                    },
                    'en': {
                        'Display Size': '1.4-inch AMOLED',
                        'Water Resistance': '50 meters (5ATM)',
                        'Battery Life': '14 days',
                        'Connectivity': 'Bluetooth 5.0 + GPS',
                        'Compatibility': 'iOS & Android'
                    }
                },
                'features': [
                    'تتبع النوم - Sleep Tracking',
                    'قياس الأكسجين بالدم - Blood Oxygen Monitoring',
                    'إشعارات الهاتف - Phone Notifications',
                    'التحكم بالموسيقى - Music Control'
                ],
                'warranty_period': 'سنتان - 2 Years',
                'meta_title': 'ساعة ذكية رياضية - Sport Pro Smart Watch',
                'meta_description': 'ساعة ذكية سبورت برو مع GPS وتتبع اللياقة البدنية ومقاومة للماء',
                'meta_keywords': 'ساعة ذكية, رياضية, smart watch, fitness, GPS',
                'is_featured': True,
                'is_best_seller': True,
            },
            {
                'name': 'شاحن لاسلكي سريع 3 في 1',
                'name_en': '3-in-1 Fast Wireless Charger',
                'slug': '3-in-1-fast-wireless-charger',
                'sku': 'TEST-CH-003',
                'barcode': '1234567890125',
                'short_description': 'شاحن لاسلكي متعدد الأجهزة يشحن الهاتف والساعة والسماعات معاً',
                'description': '''
                <h3>شاحن لاسلكي سريع 3 في 1</h3>
                <p>حل الشحن المتكامل لجميع أجهزتك الذكية.</p>
                <h4>المميزات الرئيسية:</h4>
                <ul>
                    <li>شحن 3 أجهزة في وقت واحد</li>
                    <li>شحن سريع 15 واط للهاتف</li>
                    <li>متوافق مع جميع الأجهزة Qi</li>
                    <li>تصميم أنيق ومدمج</li>
                    <li>حماية من الحرارة الزائدة</li>
                    <li>مؤشر LED للشحن</li>
                </ul>
                <h4>3-in-1 Fast Wireless Charger</h4>
                <p>The complete charging solution for all your smart devices.</p>
                <h4>Key Features:</h4>
                <ul>
                    <li>Charge 3 devices simultaneously</li>
                    <li>15W fast charging for phone</li>
                    <li>Compatible with all Qi devices</li>
                    <li>Sleek and compact design</li>
                    <li>Overheating protection</li>
                    <li>LED charging indicator</li>
                </ul>
                ''',
                'base_price': Decimal('45.990'),
                'compare_price': Decimal('69.990'),
                'stock_quantity': 100,
                'weight': Decimal('0.250'),
                'specifications': {
                    'ar': {
                        'قوة الشحن': '15 واط (الهاتف) / 5 واط (الساعة) / 5 واط (السماعات)',
                        'المدخل': 'USB-C',
                        'التوافق': 'Qi معتمد',
                        'المواد': 'ABS + سيليكون مانع للانزلاق',
                        'الأبعاد': '20 × 10 × 2 سم'
                    },
                    'en': {
                        'Charging Power': '15W (Phone) / 5W (Watch) / 5W (Earbuds)',
                        'Input': 'USB-C',
                        'Compatibility': 'Qi Certified',
                        'Materials': 'ABS + Anti-slip Silicone',
                        'Dimensions': '20 x 10 x 2 cm'
                    }
                },
                'features': [
                    'شحن سريع - Fast Charging',
                    'تصميم مضاد للانزلاق - Anti-slip Design',
                    'حماية متعددة - Multiple Protection',
                    'صديق للبيئة - Eco-friendly'
                ],
                'warranty_period': '6 أشهر - 6 Months',
                'meta_title': 'شاحن لاسلكي 3 في 1 - Wireless Charger Station',
                'meta_description': 'شاحن لاسلكي سريع 3 في 1 لشحن الهاتف والساعة والسماعات معاً',
                'meta_keywords': 'شاحن, لاسلكي, wireless charger, 3 in 1, fast charging',
                'is_new': True,
            },
        ]

        # Create products
        for product_data in products_data:
            slug = product_data.pop('slug')
            sku = product_data.pop('sku')

            product, created = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    **product_data,
                    'slug': slug,
                    'category': category,
                    'brand': brand,
                    'created_by': test_user,
                    'status': 'published',
                    'is_active': True,
                    'stock_status': 'in_stock',
                    'condition': 'new',
                    'show_price': True,
                    'allow_reviews': True,
                    'tax_rate': Decimal('16.00'),
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created product: {product.name} / {product.name_en}'))
            else:
                self.stdout.write(self.style.WARNING(f'Updated product: {product.name} / {product.name_en}'))

        self.stdout.write(self.style.SUCCESS('\nSuccessfully added 3 test products with Arabic and English content!'))
        self.stdout.write(f'Category: {category.name} ({category.name_en})')
        self.stdout.write(f'Brand: {brand.name} ({brand.name_en})')
