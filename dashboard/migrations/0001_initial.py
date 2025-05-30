# Generated by Django 5.2.1 on 2025-05-31 11:34

import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DashboardWidget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')),
                ('name', models.CharField(max_length=100, verbose_name='اسم الودجة')),
                ('widget_type', models.CharField(choices=[('chart', 'مخطط'), ('counter', 'عداد'), ('list', 'قائمة'), ('table', 'جدول'), ('text', 'نص'), ('progress', 'شريط تقدم')], max_length=20, verbose_name='نوع الودجة')),
                ('title', models.CharField(max_length=200, verbose_name='العنوان')),
                ('description', models.TextField(blank=True, verbose_name='الوصف')),
                ('config', models.JSONField(default=dict, help_text='إعدادات JSON للودجة', verbose_name='إعدادات الودجة')),
                ('row', models.PositiveIntegerField(default=1, verbose_name='الصف')),
                ('column', models.PositiveIntegerField(default=1, verbose_name='العمود')),
                ('width', models.PositiveIntegerField(default=6, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)], verbose_name='العرض')),
                ('height', models.PositiveIntegerField(default=300, verbose_name='الارتفاع')),
                ('required_permissions', models.JSONField(default=list, help_text='قائمة بالصلاحيات المطلوبة لعرض الودجة', verbose_name='الصلاحيات المطلوبة')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='الترتيب')),
            ],
            options={
                'verbose_name': 'ودجة لوحة التحكم',
                'verbose_name_plural': 'ودجات لوحة التحكم',
                'ordering': ['row', 'column', 'sort_order'],
            },
        ),
        migrations.CreateModel(
            name='DashboardUserSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')),
                ('widgets_layout', models.JSONField(default=dict, help_text='تخطيط ودجات المستخدم المخصص', verbose_name='تخطيط الودجات')),
                ('email_notifications', models.BooleanField(default=True, verbose_name='إشعارات البريد الإلكتروني')),
                ('browser_notifications', models.BooleanField(default=True, verbose_name='إشعارات المتصفح')),
                ('notification_sound', models.BooleanField(default=False, verbose_name='صوت الإشعارات')),
                ('default_view', models.CharField(default='overview', max_length=50, verbose_name='العرض الافتراضي')),
                ('items_per_page', models.PositiveIntegerField(default=20, validators=[django.core.validators.MinValueValidator(10), django.core.validators.MaxValueValidator(100)], verbose_name='عدد العناصر في الصفحة')),
                ('theme', models.CharField(choices=[('light', 'فاتح'), ('dark', 'داكن'), ('auto', 'تلقائي')], default='light', max_length=20, verbose_name='السمة')),
                ('language', models.CharField(choices=[('ar', 'العربية'), ('en', 'الإنجليزية')], default='ar', max_length=10, verbose_name='اللغة')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='dashboard_settings', to=settings.AUTH_USER_MODEL, verbose_name='المستخدم')),
            ],
            options={
                'verbose_name': 'إعدادات المستخدم للوحة التحكم',
                'verbose_name_plural': 'إعدادات المستخدمين للوحة التحكم',
            },
        ),
        migrations.CreateModel(
            name='DashboardNotification',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(help_text='عنوان الإشعار', max_length=200, verbose_name='العنوان')),
                ('message', models.TextField(help_text='محتوى الإشعار', verbose_name='الرسالة')),
                ('notification_type', models.CharField(choices=[('info', 'معلومات'), ('success', 'نجاح'), ('warning', 'تحذير'), ('error', 'خطأ'), ('urgent', 'عاجل')], default='info', max_length=20, verbose_name='نوع الإشعار')),
                ('related_object_type', models.CharField(blank=True, help_text='نوع الكائن المرتبط بالإشعار', max_length=50, verbose_name='نوع الكائن المرتبط')),
                ('related_object_id', models.CharField(blank=True, help_text='معرف الكائن المرتبط بالإشعار', max_length=100, verbose_name='معرف الكائن المرتبط')),
                ('is_read', models.BooleanField(default=False, verbose_name='مقروء')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='تاريخ القراءة')),
                ('action_url', models.URLField(blank=True, help_text='رابط للانتقال إليه عند النقر على الإشعار', verbose_name='رابط الإجراء')),
                ('action_text', models.CharField(blank=True, help_text='نص زر الإجراء', max_length=100, verbose_name='نص الإجراء')),
                ('expires_at', models.DateTimeField(blank=True, help_text='تاريخ انتهاء صلاحية الإشعار', null=True, verbose_name='ينتهي في')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dashboard_notifications', to=settings.AUTH_USER_MODEL, verbose_name='المستخدم')),
            ],
            options={
                'verbose_name': 'إشعار لوحة التحكم',
                'verbose_name_plural': 'إشعارات لوحة التحكم',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['user', 'is_read'], name='dashboard_d_user_id_561e39_idx'), models.Index(fields=['user', 'created_at'], name='dashboard_d_user_id_596f4a_idx'), models.Index(fields=['notification_type'], name='dashboard_d_notific_4bf483_idx'), models.Index(fields=['related_object_type', 'related_object_id'], name='dashboard_d_related_7e918e_idx'), models.Index(fields=['expires_at'], name='dashboard_d_expires_36187f_idx')],
            },
        ),
        migrations.CreateModel(
            name='ProductReviewAssignment',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('assigned_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التعيين')),
                ('due_date', models.DateTimeField(blank=True, help_text='التاريخ المطلوب إنجاز المراجعة فيه', null=True, verbose_name='تاريخ الاستحقاق')),
                ('priority', models.CharField(choices=[('low', 'منخفضة'), ('normal', 'عادية'), ('high', 'عالية'), ('urgent', 'عاجلة')], default='normal', max_length=20, verbose_name='الأولوية')),
                ('instructions', models.TextField(blank=True, help_text='تعليمات خاصة للمراجع', verbose_name='التعليمات')),
                ('is_completed', models.BooleanField(default=False, verbose_name='مكتمل')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='تاريخ الإكمال')),
                ('review_notes', models.TextField(blank=True, help_text='ملاحظات المراجع حول المنتج', verbose_name='ملاحظات المراجعة')),
                ('is_accepted', models.BooleanField(default=False, verbose_name='مقبول')),
                ('rejection_reason', models.TextField(blank=True, help_text='سبب رفض المنتج', verbose_name='سبب الرفض')),
                ('estimated_time', models.PositiveIntegerField(blank=True, help_text='الوقت المقدر لإكمال المراجعة', null=True, verbose_name='الوقت المقدر (بالدقائق)')),
                ('actual_time', models.PositiveIntegerField(blank=True, help_text='الوقت الفعلي لإكمال المراجعة', null=True, verbose_name='الوقت الفعلي (بالدقائق)')),
                ('assigned_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_product_reviews', to=settings.AUTH_USER_MODEL, verbose_name='عُين بواسطة')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='review_assignments', to='products.product', verbose_name='المنتج')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_review_assignments', to=settings.AUTH_USER_MODEL, verbose_name='المراجع')),
            ],
            options={
                'verbose_name': 'تعيين مراجعة منتج',
                'verbose_name_plural': 'تعيينات مراجعة المنتجات',
                'ordering': ['-assigned_at'],
                'indexes': [models.Index(fields=['reviewer', 'is_completed'], name='dashboard_p_reviewe_43cd0a_idx'), models.Index(fields=['product', 'is_completed'], name='dashboard_p_product_cdc34c_idx'), models.Index(fields=['assigned_at'], name='dashboard_p_assigne_2a898d_idx'), models.Index(fields=['due_date'], name='dashboard_p_due_dat_3e409b_idx'), models.Index(fields=['priority'], name='dashboard_p_priorit_d08ad4_idx')],
                'unique_together': {('product', 'reviewer')},
            },
        ),
    ]
