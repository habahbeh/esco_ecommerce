# payment/models.py
"""
نماذج المعاملات المالية
تستخدم لتسجيل عمليات الدفع واسترجاع المبالغ وتتبع المعاملات المالية
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
import uuid
from decimal import Decimal


class Transaction(models.Model):
    """
    نموذج المعاملات المالية - يسجل جميع المعاملات المالية في النظام
    التحويلات، المدفوعات، الاستردادات، إلخ
    """
    TRANSACTION_TYPES = [
        ('payment', _('دفع')),
        ('refund', _('استرداد')),
        ('deposit', _('إيداع')),
        ('withdrawal', _('سحب')),
        ('transfer', _('تحويل')),
        ('adjustment', _('تسوية')),
        ('fee', _('رسوم')),
        ('other', _('أخرى')),
    ]

    TRANSACTION_STATUS = [
        ('pending', _('قيد الانتظار')),
        ('processing', _('قيد المعالجة')),
        ('completed', _('مكتملة')),
        ('failed', _('فاشلة')),
        ('cancelled', _('ملغية')),
        ('reversed', _('معكوسة')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # معلومات المعاملة الأساسية
    reference_number = models.CharField(
        _("رقم المرجع"),
        max_length=100,
        unique=True,
        help_text=_("رقم مرجع فريد للمعاملة")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_("المستخدم")
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_("الطلب")
    )

    # القيم المالية
    amount = models.DecimalField(
        _("المبلغ"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("مبلغ المعاملة")
    )
    currency = models.CharField(
        _("العملة"),
        max_length=3,
        default='SAR',
        help_text=_("رمز العملة (مثل SAR أو USD)")
    )
    fees = models.DecimalField(
        _("الرسوم"),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_("رسوم المعاملة")
    )

    # تصنيف المعاملة
    transaction_type = models.CharField(
        _("نوع المعاملة"),
        max_length=20,
        choices=TRANSACTION_TYPES,
        default='payment',
        help_text=_("نوع المعاملة المالية")
    )
    status = models.CharField(
        _("الحالة"),
        max_length=20,
        choices=TRANSACTION_STATUS,
        default='pending',
        help_text=_("حالة المعاملة المالية")
    )

    # معلومات معالج الدفع
    payment_gateway = models.CharField(
        _("بوابة الدفع"),
        max_length=100,
        blank=True,
        help_text=_("اسم بوابة الدفع المستخدمة")
    )
    payment_method = models.CharField(
        _("طريقة الدفع"),
        max_length=100,
        blank=True,
        help_text=_("طريقة الدفع المستخدمة")
    )
    gateway_transaction_id = models.CharField(
        _("معرف المعاملة في البوابة"),
        max_length=255,
        blank=True,
        help_text=_("معرف المعاملة في بوابة الدفع الخارجية")
    )
    gateway_response = models.JSONField(
        _("استجابة البوابة"),
        default=dict,
        blank=True,
        help_text=_("استجابة بوابة الدفع الكاملة")
    )

    # تفاصيل إضافية
    description = models.TextField(
        _("الوصف"),
        blank=True,
        help_text=_("وصف المعاملة")
    )
    notes = models.TextField(
        _("الملاحظات"),
        blank=True,
        help_text=_("ملاحظات داخلية حول المعاملة")
    )
    metadata = models.JSONField(
        _("بيانات وصفية"),
        default=dict,
        blank=True,
        help_text=_("بيانات إضافية للمعاملة")
    )

    # معلومات الأمان
    ip_address = models.GenericIPAddressField(
        _("عنوان IP"),
        null=True,
        blank=True,
        help_text=_("عنوان IP للمستخدم عند إجراء المعاملة")
    )
    user_agent = models.TextField(
        _("متصفح المستخدم"),
        blank=True,
        help_text=_("معلومات متصفح المستخدم")
    )

    # طوابع الوقت
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)
    completed_at = models.DateTimeField(
        _("تاريخ الإكمال"),
        null=True,
        blank=True,
        help_text=_("تاريخ إكمال المعاملة")
    )

    class Meta:
        app_label = 'payment'
        verbose_name = _("معاملة مالية")
        verbose_name_plural = _("معاملات مالية")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference_number']),
            models.Index(fields=['user', 'transaction_type']),
            models.Index(fields=['order']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['payment_gateway']),
        ]

    def __str__(self):
        return f"{self.reference_number} - {self.get_transaction_type_display()} ({self.amount} {self.currency})"

    def save(self, *args, **kwargs):
        # إنشاء رقم مرجع إذا لم يكن موجوداً
        if not self.reference_number:
            self.reference_number = self.generate_reference_number()

        # تحديث تاريخ الإكمال عند تغيير الحالة إلى "مكتملة"
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()

        super().save(*args, **kwargs)

    def generate_reference_number(self):
        """توليد رقم مرجع فريد للمعاملة"""
        import random
        import string
        prefix = f"TXN-{self.transaction_type[:3].upper()}"
        timestamp = timezone.now().strftime('%y%m%d%H%M')
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{prefix}-{timestamp}-{random_suffix}"

    def mark_as_completed(self, gateway_response=None):
        """تعليم المعاملة كمكتملة"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if gateway_response:
            self.gateway_response = gateway_response
        self.save()

    def mark_as_failed(self, reason=None, gateway_response=None):
        """تعليم المعاملة كفاشلة"""
        self.status = 'failed'
        if reason:
            self.notes = reason
        if gateway_response:
            self.gateway_response = gateway_response
        self.save()


class Payment(models.Model):
    """
    نموذج المدفوعات - يسجل عمليات دفع معينة من العملاء
    """
    PAYMENT_STATUS = [
        ('pending', _('قيد الانتظار')),
        ('authorized', _('مفوض')),
        ('paid', _('مدفوع')),
        ('failed', _('فاشل')),
        ('cancelled', _('ملغي')),
        ('refunded', _('مسترد')),
        ('partially_refunded', _('مسترد جزئياً')),
    ]

    PAYMENT_METHODS = [
        ('credit_card', _('بطاقة ائتمان')),
        ('debit_card', _('بطاقة خصم')),
        ('bank_transfer', _('تحويل بنكي')),
        ('cash_on_delivery', _('الدفع عند الاستلام')),
        ('digital_wallet', _('محفظة إلكترونية')),
        ('paypal', _('باي بال')),
        ('apple_pay', _('آبل باي')),
        ('google_pay', _('جوجل باي')),
        ('other', _('أخرى')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # العلاقات
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name=_("المستخدم")
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name=_("الطلب")
    )
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment',
        verbose_name=_("المعاملة")
    )

    # معلومات الدفع
    amount = models.DecimalField(
        _("المبلغ"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("مبلغ الدفع")
    )
    currency = models.CharField(
        _("العملة"),
        max_length=3,
        default='SAR',
        help_text=_("رمز العملة")
    )
    payment_method = models.CharField(
        _("طريقة الدفع"),
        max_length=50,
        choices=PAYMENT_METHODS,
        default='credit_card',
        help_text=_("طريقة الدفع المستخدمة")
    )
    status = models.CharField(
        _("الحالة"),
        max_length=20,
        choices=PAYMENT_STATUS,
        default='pending',
        help_text=_("حالة الدفع")
    )

    # معلومات بوابة الدفع
    payment_gateway = models.CharField(
        _("بوابة الدفع"),
        max_length=100,
        blank=True,
        help_text=_("اسم بوابة الدفع المستخدمة")
    )
    gateway_payment_id = models.CharField(
        _("معرف الدفع في البوابة"),
        max_length=255,
        blank=True,
        help_text=_("معرف عملية الدفع في بوابة الدفع")
    )
    gateway_response = models.JSONField(
        _("استجابة البوابة"),
        default=dict,
        blank=True,
        help_text=_("استجابة بوابة الدفع الكاملة")
    )

    # معلومات البطاقة (مشفرة/جزئية)
    card_type = models.CharField(
        _("نوع البطاقة"),
        max_length=50,
        blank=True,
        help_text=_("نوع البطاقة المستخدمة")
    )
    last_4_digits = models.CharField(
        _("آخر 4 أرقام"),
        max_length=4,
        blank=True,
        help_text=_("آخر 4 أرقام من البطاقة")
    )
    card_expiry = models.CharField(
        _("تاريخ انتهاء البطاقة"),
        max_length=7,
        blank=True,
        help_text=_("تاريخ انتهاء صلاحية البطاقة (MM/YYYY)")
    )

    # التفاصيل والملاحظات
    billing_address = models.TextField(
        _("عنوان الفواتير"),
        blank=True,
        help_text=_("العنوان المستخدم للفواتير")
    )
    description = models.TextField(
        _("الوصف"),
        blank=True,
        help_text=_("وصف عملية الدفع")
    )
    notes = models.TextField(
        _("الملاحظات"),
        blank=True,
        help_text=_("ملاحظات داخلية")
    )

    # معلومات الأمان
    ip_address = models.GenericIPAddressField(
        _("عنوان IP"),
        null=True,
        blank=True,
        help_text=_("عنوان IP للمستخدم عند الدفع")
    )

    # طوابع الوقت
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)
    paid_at = models.DateTimeField(
        _("تاريخ الدفع"),
        null=True,
        blank=True,
        help_text=_("تاريخ اكتمال الدفع")
    )

    class Meta:
        app_label = 'payment'
        verbose_name = _("عملية دفع")
        verbose_name_plural = _("عمليات الدفع")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['created_at']),
            models.Index(fields=['paid_at']),
        ]

    def __str__(self):
        return f"{self.get_payment_method_display()} - {self.amount} {self.currency} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # تحديث تاريخ الدفع عند تغيير الحالة إلى "مدفوع"
        if self.status == 'paid' and not self.paid_at:
            self.paid_at = timezone.now()

        super().save(*args, **kwargs)

    def create_transaction(self):
        """إنشاء معاملة مالية مرتبطة بعملية الدفع"""
        if not self.transaction:
            transaction = Transaction.objects.create(
                user=self.user,
                order=self.order,
                amount=self.amount,
                currency=self.currency,
                transaction_type='payment',
                status='pending' if self.status == 'pending' else 'completed',
                payment_gateway=self.payment_gateway,
                payment_method=self.payment_method,
                gateway_transaction_id=self.gateway_payment_id,
                gateway_response=self.gateway_response,
                description=self.description,
                ip_address=self.ip_address,
                completed_at=self.paid_at
            )

            self.transaction = transaction
            self.save(update_fields=['transaction'])

            return transaction

        return None

    def mark_as_paid(self, gateway_response=None):
        """تعليم الدفع كمكتمل"""
        self.status = 'paid'
        self.paid_at = timezone.now()
        if gateway_response:
            self.gateway_response = gateway_response

        # تحديث المعاملة المرتبطة
        if self.transaction:
            self.transaction.status = 'completed'
            self.transaction.completed_at = self.paid_at
            if gateway_response:
                self.transaction.gateway_response = gateway_response
            self.transaction.save()

        # تحديث حالة الطلب
        if self.order:
            self.order.payment_status = 'paid'
            self.order.save(update_fields=['payment_status'])

        self.save()


class Refund(models.Model):
    """
    نموذج استرداد المبالغ - يسجل عمليات استرداد المبالغ للعملاء
    """
    REFUND_STATUS = [
        ('pending', _('قيد الانتظار')),
        ('processing', _('قيد المعالجة')),
        ('completed', _('مكتمل')),
        ('failed', _('فاشل')),
        ('cancelled', _('ملغي')),
    ]

    REFUND_REASONS = [
        ('customer_request', _('طلب العميل')),
        ('duplicate_payment', _('دفع مكرر')),
        ('fraudulent', _('معاملة احتيالية')),
        ('order_cancelled', _('إلغاء الطلب')),
        ('item_unavailable', _('المنتج غير متوفر')),
        ('shipping_issue', _('مشكلة في الشحن')),
        ('quality_issue', _('مشكلة في الجودة')),
        ('wrong_item', _('منتج خاطئ')),
        ('other', _('أخرى')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # العلاقات
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds',
        verbose_name=_("عملية الدفع")
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refunds',
        verbose_name=_("الطلب")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refunds',
        verbose_name=_("المستخدم")
    )
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refund',
        verbose_name=_("المعاملة")
    )

    # معلومات الاسترداد
    amount = models.DecimalField(
        _("المبلغ"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("مبلغ الاسترداد")
    )
    currency = models.CharField(
        _("العملة"),
        max_length=3,
        default='SAR',
        help_text=_("رمز العملة")
    )
    reason = models.CharField(
        _("سبب الاسترداد"),
        max_length=50,
        choices=REFUND_REASONS,
        default='customer_request',
        help_text=_("سبب طلب الاسترداد")
    )
    status = models.CharField(
        _("الحالة"),
        max_length=20,
        choices=REFUND_STATUS,
        default='pending',
        help_text=_("حالة الاسترداد")
    )

    # معلومات بوابة الدفع
    refund_gateway = models.CharField(
        _("بوابة الاسترداد"),
        max_length=100,
        blank=True,
        help_text=_("اسم بوابة الدفع المستخدمة للاسترداد")
    )
    gateway_refund_id = models.CharField(
        _("معرف الاسترداد في البوابة"),
        max_length=255,
        blank=True,
        help_text=_("معرف عملية الاسترداد في بوابة الدفع")
    )
    gateway_response = models.JSONField(
        _("استجابة البوابة"),
        default=dict,
        blank=True,
        help_text=_("استجابة بوابة الدفع الكاملة للاسترداد")
    )

    # التفاصيل والملاحظات
    notes = models.TextField(
        _("الملاحظات"),
        blank=True,
        help_text=_("ملاحظات داخلية حول الاسترداد")
    )
    customer_notes = models.TextField(
        _("ملاحظات العميل"),
        blank=True,
        help_text=_("ملاحظات العميل حول سبب الاسترداد")
    )
    admin_notes = models.TextField(
        _("ملاحظات الإدارة"),
        blank=True,
        help_text=_("ملاحظات المدير حول الاسترداد")
    )

    # من قام بالإجراء
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_refunds',
        verbose_name=_("طلب بواسطة")
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_refunds',
        verbose_name=_("تمت معالجته بواسطة")
    )

    # طوابع الوقت
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)
    completed_at = models.DateTimeField(
        _("تاريخ الإكمال"),
        null=True,
        blank=True,
        help_text=_("تاريخ اكتمال الاسترداد")
    )

    class Meta:
        app_label = 'payment'
        verbose_name = _("عملية استرداد")
        verbose_name_plural = _("عمليات الاسترداد")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment']),
            models.Index(fields=['order']),
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['completed_at']),
        ]

    def __str__(self):
        return f"{self.get_reason_display()} - {self.amount} {self.currency} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # تحديث تاريخ الإكمال عند تغيير الحالة إلى "مكتمل"
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()

        super().save(*args, **kwargs)

        # تحديث حالة الدفع عند اكتمال الاسترداد
        if self.status == 'completed' and self.payment:
            payment = self.payment

            # التحقق مما إذا كان الاسترداد كاملاً أو جزئياً
            refunded_amount = Refund.objects.filter(
                payment=payment,
                status='completed'
            ).aggregate(total=models.Sum('amount'))['total'] or 0

            if refunded_amount >= payment.amount:
                payment.status = 'refunded'
            else:
                payment.status = 'partially_refunded'

            payment.save(update_fields=['status'])

    def create_transaction(self):
        """إنشاء معاملة مالية مرتبطة بعملية الاسترداد"""
        if not self.transaction:
            transaction = Transaction.objects.create(
                user=self.user,
                order=self.order,
                amount=self.amount,
                currency=self.currency,
                transaction_type='refund',
                status='pending' if self.status == 'pending' else 'completed',
                payment_gateway=self.refund_gateway,
                gateway_transaction_id=self.gateway_refund_id,
                gateway_response=self.gateway_response,
                description=f"استرداد لـ {self.payment.gateway_payment_id}" if self.payment else "استرداد",
                notes=self.notes,
                completed_at=self.completed_at
            )

            self.transaction = transaction
            self.save(update_fields=['transaction'])

            return transaction

        return None

    def mark_as_completed(self, gateway_response=None, processed_by=None):
        """تعليم الاسترداد كمكتمل"""
        self.status = 'completed'
        self.completed_at = timezone.now()

        if gateway_response:
            self.gateway_response = gateway_response

        if processed_by:
            self.processed_by = processed_by

        # تحديث المعاملة المرتبطة
        if self.transaction:
            self.transaction.status = 'completed'
            self.transaction.completed_at = self.completed_at
            if gateway_response:
                self.transaction.gateway_response = gateway_response
            self.transaction.save()

        # تحديث حالة الطلب إذا كان الاسترداد كاملاً
        if self.order and self.amount >= self.payment.amount:
            self.order.payment_status = 'refunded'
            self.order.save(update_fields=['payment_status'])

        self.save()