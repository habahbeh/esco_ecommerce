# Generated by Django 5.2.1 on 2025-06-03 15:22

import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cart', '0002_initial'),
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='اسم طريقة الدفع المعروض للمستخدم', max_length=100, verbose_name='اسم طريقة الدفع')),
                ('code', models.CharField(help_text='رمز فريد لطريقة الدفع (للاستخدام التقني)', max_length=50, unique=True, verbose_name='رمز طريقة الدفع')),
                ('payment_type', models.CharField(choices=[('credit_card', 'بطاقة ائتمان'), ('debit_card', 'بطاقة خصم'), ('bank_transfer', 'تحويل بنكي'), ('cash_on_delivery', 'الدفع عند الاستلام'), ('digital_wallet', 'محفظة إلكترونية'), ('paypal', 'باي بال'), ('apple_pay', 'آبل باي'), ('google_pay', 'جوجل باي'), ('other', 'أخرى')], default='credit_card', help_text='نوع طريقة الدفع', max_length=50, verbose_name='نوع الدفع')),
                ('description', models.TextField(blank=True, help_text='وصف طريقة الدفع المعروض للمستخدم', verbose_name='الوصف')),
                ('icon', models.ImageField(blank=True, help_text='أيقونة تمثل طريقة الدفع', null=True, upload_to='payment_methods/', verbose_name='أيقونة')),
                ('instructions', models.TextField(blank=True, help_text='تعليمات خاصة بطريقة الدفع', verbose_name='تعليمات')),
                ('fee_fixed', models.DecimalField(decimal_places=2, default=0, help_text='رسوم ثابتة لاستخدام طريقة الدفع', max_digits=10, verbose_name='رسوم ثابتة')),
                ('fee_percentage', models.DecimalField(decimal_places=2, default=0, help_text='رسوم بالنسبة المئوية لاستخدام طريقة الدفع', max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='رسوم بالنسبة المئوية')),
                ('is_active', models.BooleanField(default=True, help_text='هل طريقة الدفع متاحة للاستخدام', verbose_name='نشط')),
                ('is_default', models.BooleanField(default=False, help_text='هل هي طريقة الدفع الافتراضية', verbose_name='افتراضي')),
                ('min_amount', models.DecimalField(decimal_places=2, default=0, help_text='الحد الأدنى للمبلغ المسموح به لهذه الطريقة', max_digits=10, verbose_name='الحد الأدنى للمبلغ')),
                ('max_amount', models.DecimalField(decimal_places=2, default=0, help_text='الحد الأقصى للمبلغ المسموح به لهذه الطريقة (0 = غير محدود)', max_digits=10, verbose_name='الحد الأقصى للمبلغ')),
                ('sort_order', models.PositiveIntegerField(default=0, help_text='ترتيب عرض طريقة الدفع (الأصغر أولاً)', verbose_name='ترتيب العرض')),
                ('api_credentials', models.JSONField(blank=True, default=dict, help_text='بيانات اعتماد API لبوابة الدفع (مشفرة)', verbose_name='بيانات اعتماد API')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')),
            ],
            options={
                'verbose_name': 'طريقة دفع',
                'verbose_name_plural': 'طرق الدفع',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='ShippingMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='اسم طريقة الشحن المعروض للمستخدم', max_length=100, verbose_name='اسم طريقة الشحن')),
                ('code', models.CharField(help_text='رمز فريد لطريقة الشحن (للاستخدام التقني)', max_length=50, unique=True, verbose_name='رمز طريقة الشحن')),
                ('description', models.TextField(blank=True, help_text='وصف طريقة الشحن المعروض للمستخدم', verbose_name='الوصف')),
                ('icon', models.ImageField(blank=True, help_text='أيقونة تمثل طريقة الشحن', null=True, upload_to='shipping_methods/', verbose_name='أيقونة')),
                ('base_cost', models.DecimalField(decimal_places=2, default=0, help_text='التكلفة الأساسية للشحن', max_digits=10, verbose_name='التكلفة الأساسية')),
                ('free_shipping_threshold', models.DecimalField(decimal_places=2, default=0, help_text='الحد الأدنى للطلب للحصول على شحن مجاني (0 = غير متاح)', max_digits=10, verbose_name='حد الشحن المجاني')),
                ('estimated_days_min', models.PositiveIntegerField(default=1, help_text='الحد الأدنى لعدد أيام التوصيل المتوقعة', verbose_name='الحد الأدنى للأيام المتوقعة')),
                ('estimated_days_max', models.PositiveIntegerField(default=3, help_text='الحد الأقصى لعدد أيام التوصيل المتوقعة', verbose_name='الحد الأقصى للأيام المتوقعة')),
                ('is_active', models.BooleanField(default=True, help_text='هل طريقة الشحن متاحة للاستخدام', verbose_name='نشط')),
                ('is_default', models.BooleanField(default=False, help_text='هل هي طريقة الشحن الافتراضية', verbose_name='افتراضي')),
                ('sort_order', models.PositiveIntegerField(default=0, help_text='ترتيب عرض طريقة الشحن (الأصغر أولاً)', verbose_name='ترتيب العرض')),
                ('restrictions', models.TextField(blank=True, help_text='أي قيود أو شروط خاصة بطريقة الشحن', verbose_name='القيود')),
                ('countries', models.JSONField(blank=True, default=list, help_text='قائمة الدول التي تتوفر فيها طريقة الشحن (فارغة = كل الدول)', verbose_name='الدول المتاحة')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')),
            ],
            options={
                'verbose_name': 'طريقة شحن',
                'verbose_name_plural': 'طرق الشحن',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='كود الكوبون الذي يدخله المستخدم', max_length=50, unique=True, verbose_name='كود الكوبون')),
                ('description', models.CharField(blank=True, help_text='وصف الكوبون المعروض للمستخدم', max_length=200, verbose_name='الوصف')),
                ('discount_type', models.CharField(choices=[('percentage', 'نسبة مئوية'), ('fixed_amount', 'مبلغ ثابت'), ('free_shipping', 'شحن مجاني')], default='percentage', help_text='نوع الخصم المطبق', max_length=20, verbose_name='نوع الخصم')),
                ('discount_value', models.DecimalField(decimal_places=2, help_text='قيمة الخصم (نسبة مئوية أو مبلغ ثابت)', max_digits=10, verbose_name='قيمة الخصم')),
                ('min_order_value', models.DecimalField(decimal_places=2, default=0, help_text='الحد الأدنى لقيمة الطلب لتطبيق الكوبون', max_digits=10, verbose_name='الحد الأدنى لقيمة الطلب')),
                ('max_discount_amount', models.DecimalField(decimal_places=2, default=0, help_text='الحد الأقصى لمبلغ الخصم (0 = غير محدود)', max_digits=10, verbose_name='الحد الأقصى لمبلغ الخصم')),
                ('is_active', models.BooleanField(default=True, help_text='هل الكوبون نشط ويمكن استخدامه', verbose_name='نشط')),
                ('start_date', models.DateTimeField(blank=True, help_text='تاريخ بداية صلاحية الكوبون', null=True, verbose_name='تاريخ البداية')),
                ('end_date', models.DateTimeField(blank=True, help_text='تاريخ نهاية صلاحية الكوبون', null=True, verbose_name='تاريخ النهاية')),
                ('max_uses', models.PositiveIntegerField(default=0, help_text='الحد الأقصى لعدد مرات استخدام الكوبون (0 = غير محدود)', verbose_name='الحد الأقصى للاستخدام')),
                ('max_uses_per_user', models.PositiveIntegerField(default=0, help_text='الحد الأقصى لعدد مرات استخدام الكوبون لكل مستخدم (0 = غير محدود)', verbose_name='الحد الأقصى للاستخدام للمستخدم')),
                ('uses_count', models.PositiveIntegerField(default=0, editable=False, help_text='عدد مرات استخدام الكوبون', verbose_name='عدد مرات الاستخدام')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')),
            ],
            options={
                'verbose_name': 'كوبون خصم',
                'verbose_name_plural': 'كوبونات الخصم',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['code'], name='checkout_co_code_dc11db_idx'), models.Index(fields=['is_active'], name='checkout_co_is_acti_648c25_idx'), models.Index(fields=['start_date', 'end_date'], name='checkout_co_start_d_4d20c4_idx')],
            },
        ),
        migrations.CreateModel(
            name='CheckoutSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('session_key', models.CharField(blank=True, help_text='مفتاح جلسة المستخدم للمستخدمين غير المسجلين', max_length=40, null=True, verbose_name='مفتاح الجلسة')),
                ('email', models.EmailField(blank=True, max_length=255, verbose_name='البريد الإلكتروني')),
                ('phone_number', models.CharField(blank=True, max_length=20, verbose_name='رقم الهاتف')),
                ('current_step', models.CharField(choices=[('cart', 'سلة التسوق'), ('information', 'معلومات العميل'), ('shipping', 'الشحن'), ('payment', 'الدفع'), ('review', 'مراجعة الطلب'), ('complete', 'اكتمال الطلب')], default='cart', help_text='الخطوة الحالية في عملية الدفع', max_length=20, verbose_name='الخطوة الحالية')),
                ('is_completed', models.BooleanField(default=False, help_text='هل اكتملت عملية الدفع', verbose_name='مكتملة')),
                ('notes', models.TextField(blank=True, help_text='ملاحظات العميل حول الطلب', verbose_name='ملاحظات')),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, help_text='مجموع سعر المنتجات قبل الضريبة والشحن', max_digits=10, verbose_name='المجموع الفرعي')),
                ('shipping_cost', models.DecimalField(decimal_places=2, default=0, help_text='تكلفة الشحن', max_digits=10, verbose_name='تكلفة الشحن')),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0, help_text='مبلغ الضريبة المضافة', max_digits=10, verbose_name='مبلغ الضريبة')),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, help_text='مبلغ الخصم الكلي', max_digits=10, verbose_name='مبلغ الخصم')),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, help_text='المبلغ الإجمالي للطلب', max_digits=10, verbose_name='المبلغ الإجمالي')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')),
                ('expires_at', models.DateTimeField(blank=True, help_text='تاريخ انتهاء صلاحية جلسة الدفع', null=True, verbose_name='تاريخ الانتهاء')),
                ('completed_at', models.DateTimeField(blank=True, help_text='تاريخ اكتمال عملية الدفع', null=True, verbose_name='تاريخ الاكتمال')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='عنوان IP للمستخدم أثناء عملية الدفع', null=True, verbose_name='عنوان IP')),
                ('user_agent', models.TextField(blank=True, help_text='معلومات متصفح المستخدم', verbose_name='معلومات المتصفح')),
                ('cart', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='checkout_session', to='cart.cart', verbose_name='سلة التسوق')),
                ('order', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='checkout_session', to='orders.order', verbose_name='الطلب')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='checkout_sessions', to=settings.AUTH_USER_MODEL, verbose_name='المستخدم')),
                ('payment_method', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='checkout_sessions', to='checkout.paymentmethod', verbose_name='طريقة الدفع')),
                ('shipping_method', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='checkout_sessions', to='checkout.shippingmethod', verbose_name='طريقة الشحن')),
            ],
            options={
                'verbose_name': 'جلسة دفع',
                'verbose_name_plural': 'جلسات الدفع',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CouponUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('used_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الاستخدام')),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usages', to='checkout.coupon', verbose_name='الكوبون')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='coupon_usages', to='orders.order', verbose_name='الطلب')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coupon_usages', to=settings.AUTH_USER_MODEL, verbose_name='المستخدم')),
            ],
            options={
                'verbose_name': 'استخدام كوبون',
                'verbose_name_plural': 'استخدامات الكوبونات',
                'ordering': ['-used_at'],
                'unique_together': {('coupon', 'user', 'order')},
            },
        ),
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('transaction_id', models.CharField(help_text='رقم المعاملة الفريد من بوابة الدفع', max_length=255, verbose_name='رقم المعاملة')),
                ('amount', models.DecimalField(decimal_places=2, help_text='مبلغ المعاملة', max_digits=10, verbose_name='المبلغ')),
                ('currency', models.CharField(default='SAR', help_text='رمز العملة (مثل SAR, USD)', max_length=3, verbose_name='العملة')),
                ('status', models.CharField(choices=[('pending', 'قيد الانتظار'), ('processing', 'قيد المعالجة'), ('completed', 'مكتملة'), ('failed', 'فاشلة'), ('refunded', 'مستردة'), ('cancelled', 'ملغية')], default='pending', help_text='حالة المعاملة', max_length=20, verbose_name='الحالة')),
                ('transaction_type', models.CharField(choices=[('payment', 'دفع'), ('refund', 'استرداد'), ('capture', 'تحصيل'), ('authorization', 'تفويض'), ('void', 'إلغاء')], default='payment', help_text='نوع المعاملة', max_length=20, verbose_name='نوع المعاملة')),
                ('gateway_response', models.JSONField(blank=True, default=dict, help_text='البيانات الكاملة المستلمة من بوابة الدفع', verbose_name='استجابة بوابة الدفع')),
                ('gateway_message', models.TextField(blank=True, help_text='رسالة الخطأ أو النجاح من بوابة الدفع', verbose_name='رسالة بوابة الدفع')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='عنوان IP للمستخدم أثناء المعاملة', null=True, verbose_name='عنوان IP')),
                ('user_agent', models.TextField(blank=True, help_text='معلومات متصفح المستخدم', verbose_name='معلومات المتصفح')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='تاريخ بدء المعاملة', verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='تاريخ آخر تحديث للمعاملة', verbose_name='تاريخ التحديث')),
                ('completed_at', models.DateTimeField(blank=True, help_text='تاريخ اكتمال المعاملة', null=True, verbose_name='تاريخ الاكتمال')),
                ('checkout_session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment_transactions', to='checkout.checkoutsession', verbose_name='جلسة الدفع')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment_transactions', to='orders.order', verbose_name='الطلب')),
                ('payment_method', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='checkout.paymentmethod', verbose_name='طريقة الدفع')),
            ],
            options={
                'verbose_name': 'معاملة دفع',
                'verbose_name_plural': 'معاملات الدفع',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['order'], name='checkout_pa_order_i_5b4647_idx'), models.Index(fields=['checkout_session'], name='checkout_pa_checkou_75a0fb_idx'), models.Index(fields=['transaction_id'], name='checkout_pa_transac_3655ee_idx'), models.Index(fields=['status'], name='checkout_pa_status_25af30_idx'), models.Index(fields=['created_at'], name='checkout_pa_created_7d064d_idx')],
            },
        ),
        migrations.AddIndex(
            model_name='checkoutsession',
            index=models.Index(fields=['user'], name='checkout_ch_user_id_cddb8e_idx'),
        ),
        migrations.AddIndex(
            model_name='checkoutsession',
            index=models.Index(fields=['session_key'], name='checkout_ch_session_15062a_idx'),
        ),
        migrations.AddIndex(
            model_name='checkoutsession',
            index=models.Index(fields=['created_at'], name='checkout_ch_created_c15d7c_idx'),
        ),
        migrations.AddIndex(
            model_name='checkoutsession',
            index=models.Index(fields=['is_completed'], name='checkout_ch_is_comp_1c70b3_idx'),
        ),
    ]
