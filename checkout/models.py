# checkout/models.py
"""
نماذج عملية الدفع والشراء
Checkout and payment process models
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from decimal import Decimal

from cart.models import Cart
from orders.models import Order


class CheckoutSession(models.Model):
    """
    نموذج جلسة الدفع - يمثل عملية دفع واحدة
    يستخدم لتتبع حالة المستخدم أثناء عملية الدفع
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkout_sessions',
        verbose_name=_("المستخدم")
    )
    cart = models.OneToOneField(
        Cart,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkout_session',
        verbose_name=_("سلة التسوق")
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkout_session',
        verbose_name=_("الطلب")
    )
    session_key = models.CharField(
        _("مفتاح الجلسة"),
        max_length=40,
        null=True,
        blank=True,
        help_text=_("مفتاح جلسة المستخدم للمستخدمين غير المسجلين")
    )

    # معلومات العميل - Customer information
    email = models.EmailField(_("البريد الإلكتروني"), max_length=255, blank=True)
    phone_number = models.CharField(_("رقم الهاتف"), max_length=20, blank=True)

    # حالة الجلسة - Session status
    CHECKOUT_STEPS = [
        ('cart', _('سلة التسوق')),
        ('information', _('معلومات العميل')),
        ('shipping', _('الشحن')),
        ('payment', _('الدفع')),
        ('review', _('مراجعة الطلب')),
        ('complete', _('اكتمال الطلب')),
    ]

    current_step = models.CharField(
        _("الخطوة الحالية"),
        max_length=20,
        choices=CHECKOUT_STEPS,
        default='cart',
        help_text=_("الخطوة الحالية في عملية الدفع")
    )

    is_completed = models.BooleanField(
        _("مكتملة"),
        default=False,
        help_text=_("هل اكتملت عملية الدفع")
    )

    # معلومات إضافية - Additional information
    notes = models.TextField(
        _("ملاحظات"),
        blank=True,
        help_text=_("ملاحظات العميل حول الطلب")
    )

    # خيارات التسليم والدفع - Delivery and payment options
    shipping_method = models.ForeignKey(
        'ShippingMethod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkout_sessions',
        verbose_name=_("طريقة الشحن")
    )

    payment_method = models.ForeignKey(
        'PaymentMethod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkout_sessions',
        verbose_name=_("طريقة الدفع")
    )

    # المبالغ والخصومات - Amounts and discounts
    subtotal = models.DecimalField(
        _("المجموع الفرعي"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("مجموع سعر المنتجات قبل الضريبة والشحن")
    )

    shipping_cost = models.DecimalField(
        _("تكلفة الشحن"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("تكلفة الشحن")
    )

    tax_amount = models.DecimalField(
        _("مبلغ الضريبة"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("مبلغ الضريبة المضافة")
    )

    discount_amount = models.DecimalField(
        _("مبلغ الخصم"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("مبلغ الخصم الكلي")
    )

    total_amount = models.DecimalField(
        _("المبلغ الإجمالي"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("المبلغ الإجمالي للطلب")
    )

    # سجلات الوقت - Timestamps
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)
    expires_at = models.DateTimeField(
        _("تاريخ الانتهاء"),
        null=True,
        blank=True,
        help_text=_("تاريخ انتهاء صلاحية جلسة الدفع")
    )
    completed_at = models.DateTimeField(
        _("تاريخ الاكتمال"),
        null=True,
        blank=True,
        help_text=_("تاريخ اكتمال عملية الدفع")
    )

    # عنوان IP - IP Address
    ip_address = models.GenericIPAddressField(
        _("عنوان IP"),
        null=True,
        blank=True,
        help_text=_("عنوان IP للمستخدم أثناء عملية الدفع")
    )

    # معلومات المتصفح - Browser information
    user_agent = models.TextField(
        _("معلومات المتصفح"),
        blank=True,
        help_text=_("معلومات متصفح المستخدم")
    )

    class Meta:
        verbose_name = _("جلسة دفع")
        verbose_name_plural = _("جلسات الدفع")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_completed']),
        ]

    def __str__(self):
        if self.order:
            return f"جلسة دفع للطلب {self.order.order_number}"
        return f"جلسة دفع {self.id}"

    def save(self, *args, **kwargs):
        """تعيين تاريخ انتهاء الصلاحية إذا لم يكن موجوداً"""
        if not self.expires_at:
            # تعيين تاريخ انتهاء الصلاحية بعد 24 ساعة من الإنشاء
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)

        # حساب المجموع الإجمالي
        self.calculate_totals()

        super().save(*args, **kwargs)

    def calculate_totals(self):
        """حساب جميع المبالغ والمجموع الإجمالي"""
        # حساب المجموع الفرعي من سلة التسوق
        if self.cart:
            self.subtotal = self.cart.total_price

        # حساب تكلفة الشحن
        if self.shipping_method:
            self.shipping_cost = self.shipping_method.calculate_cost(self.subtotal)

        # حساب الضريبة (مثال: 15%)
        tax_rate = Decimal('0.15')  # يمكن تعديلها حسب الإعدادات
        self.tax_amount = (self.subtotal * tax_rate).quantize(Decimal('0.01'))

        # حساب المجموع الإجمالي
        self.total_amount = (
                self.subtotal + self.shipping_cost +
                self.tax_amount - self.discount_amount
        ).quantize(Decimal('0.01'))

    def mark_as_completed(self):
        """تعليم جلسة الدفع كمكتملة"""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()

    def create_order(self):
        """إنشاء طلب من جلسة الدفع"""
        if self.order:
            return self.order

        # التحقق من وجود سلة
        if not self.cart:
            raise ValueError(_("لا يمكن إنشاء طلب بدون سلة تسوق"))

        # إنشاء الطلب
        from orders.models import Order, OrderItem

        order = Order.objects.create(
            user=self.user,
            cart=self.cart,
            full_name=self.user.get_full_name() if self.user else "",
            email=self.email or (self.user.email if self.user else ""),
            phone=self.phone_number,
            total_price=self.subtotal,
            shipping_cost=self.shipping_cost,
            tax_amount=self.tax_amount,
            grand_total=self.total_amount,
            payment_method=self.payment_method.name if self.payment_method else "",
            notes=self.notes
        )

        # إنشاء عناصر الطلب من عناصر السلة
        for cart_item in self.cart.items.all():
            OrderItem.objects.create(
                order=order,
                product_name=cart_item.product.name,
                product_id=str(cart_item.product.id),
                variant_name=cart_item.variant.name if cart_item.variant else "",
                variant_id=str(cart_item.variant.id) if cart_item.variant else "",
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                total_price=cart_item.total_price
            )

        # ربط الطلب بجلسة الدفع
        self.order = order
        self.save()

        return order

    @property
    def is_expired(self):
        """التحقق من انتهاء صلاحية جلسة الدفع"""
        if not self.expires_at:
            return False

        return timezone.now() > self.expires_at

    @property
    def progress_percentage(self):
        """نسبة اكتمال عملية الدفع"""
        steps = dict(self.CHECKOUT_STEPS)
        step_keys = list(steps.keys())

        if self.is_completed:
            return 100

        current_index = step_keys.index(self.current_step)
        total_steps = len(step_keys)

        return int((current_index / (total_steps - 1)) * 100)


class PaymentMethod(models.Model):
    """
    نموذج طرق الدفع - يمثل طريقة دفع متاحة في النظام
    مثل بطاقة الائتمان، الدفع عند الاستلام، حوالة بنكية، إلخ
    """
    PAYMENT_TYPE_CHOICES = [
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

    name = models.CharField(
        _("اسم طريقة الدفع"),
        max_length=100,
        help_text=_("اسم طريقة الدفع المعروض للمستخدم")
    )
    code = models.CharField(
        _("رمز طريقة الدفع"),
        max_length=50,
        unique=True,
        help_text=_("رمز فريد لطريقة الدفع (للاستخدام التقني)")
    )
    payment_type = models.CharField(
        _("نوع الدفع"),
        max_length=50,
        choices=PAYMENT_TYPE_CHOICES,
        default='credit_card',
        help_text=_("نوع طريقة الدفع")
    )
    description = models.TextField(
        _("الوصف"),
        blank=True,
        help_text=_("وصف طريقة الدفع المعروض للمستخدم")
    )
    icon = models.ImageField(
        _("أيقونة"),
        upload_to='payment_methods/',
        null=True,
        blank=True,
        help_text=_("أيقونة تمثل طريقة الدفع")
    )
    instructions = models.TextField(
        _("تعليمات"),
        blank=True,
        help_text=_("تعليمات خاصة بطريقة الدفع")
    )

    # تكاليف ورسوم طريقة الدفع - Fees and charges
    fee_fixed = models.DecimalField(
        _("رسوم ثابتة"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("رسوم ثابتة لاستخدام طريقة الدفع")
    )
    fee_percentage = models.DecimalField(
        _("رسوم بالنسبة المئوية"),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("رسوم بالنسبة المئوية لاستخدام طريقة الدفع")
    )

    # الإعدادات - Settings
    is_active = models.BooleanField(
        _("نشط"),
        default=True,
        help_text=_("هل طريقة الدفع متاحة للاستخدام")
    )
    is_default = models.BooleanField(
        _("افتراضي"),
        default=False,
        help_text=_("هل هي طريقة الدفع الافتراضية")
    )
    min_amount = models.DecimalField(
        _("الحد الأدنى للمبلغ"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("الحد الأدنى للمبلغ المسموح به لهذه الطريقة")
    )
    max_amount = models.DecimalField(
        _("الحد الأقصى للمبلغ"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("الحد الأقصى للمبلغ المسموح به لهذه الطريقة (0 = غير محدود)")
    )
    sort_order = models.PositiveIntegerField(
        _("ترتيب العرض"),
        default=0,
        help_text=_("ترتيب عرض طريقة الدفع (الأصغر أولاً)")
    )

    # معلومات الاتصال بواجهة برمجة التطبيقات (API) - API connection info
    api_credentials = models.JSONField(
        _("بيانات اعتماد API"),
        default=dict,
        blank=True,
        help_text=_("بيانات اعتماد API لبوابة الدفع (مشفرة)")
    )

    # سجلات الوقت - Timestamps
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        verbose_name = _("طريقة دفع")
        verbose_name_plural = _("طرق الدفع")
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ضمان وجود طريقة دفع افتراضية واحدة فقط"""
        if self.is_default:
            # جعل كل الطرق الأخرى غير افتراضية
            PaymentMethod.objects.filter(is_default=True).update(is_default=False)

        super().save(*args, **kwargs)

    def calculate_fee(self, amount):
        """حساب رسوم استخدام طريقة الدفع"""
        fixed_fee = self.fee_fixed
        percentage_fee = (amount * self.fee_percentage / 100).quantize(Decimal('0.01'))

        return fixed_fee + percentage_fee

    def is_available_for_amount(self, amount):
        """التحقق مما إذا كانت طريقة الدفع متاحة للمبلغ المحدد"""
        if not self.is_active:
            return False

        if self.min_amount > 0 and amount < self.min_amount:
            return False

        if self.max_amount > 0 and amount > self.max_amount:
            return False

        return True


class ShippingMethod(models.Model):
    """
    نموذج طرق الشحن - يمثل طريقة شحن متاحة في النظام
    مثل التوصيل العادي، التوصيل السريع، استلام من المتجر، إلخ
    """
    name = models.CharField(
        _("اسم طريقة الشحن"),
        max_length=100,
        help_text=_("اسم طريقة الشحن المعروض للمستخدم")
    )
    code = models.CharField(
        _("رمز طريقة الشحن"),
        max_length=50,
        unique=True,
        help_text=_("رمز فريد لطريقة الشحن (للاستخدام التقني)")
    )
    description = models.TextField(
        _("الوصف"),
        blank=True,
        help_text=_("وصف طريقة الشحن المعروض للمستخدم")
    )
    icon = models.ImageField(
        _("أيقونة"),
        upload_to='shipping_methods/',
        null=True,
        blank=True,
        help_text=_("أيقونة تمثل طريقة الشحن")
    )

    # تكاليف الشحن - Shipping costs
    base_cost = models.DecimalField(
        _("التكلفة الأساسية"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("التكلفة الأساسية للشحن")
    )
    free_shipping_threshold = models.DecimalField(
        _("حد الشحن المجاني"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("الحد الأدنى للطلب للحصول على شحن مجاني (0 = غير متاح)")
    )

    # مدة التوصيل - Delivery time
    estimated_days_min = models.PositiveIntegerField(
        _("الحد الأدنى للأيام المتوقعة"),
        default=1,
        help_text=_("الحد الأدنى لعدد أيام التوصيل المتوقعة")
    )
    estimated_days_max = models.PositiveIntegerField(
        _("الحد الأقصى للأيام المتوقعة"),
        default=3,
        help_text=_("الحد الأقصى لعدد أيام التوصيل المتوقعة")
    )

    # الإعدادات - Settings
    is_active = models.BooleanField(
        _("نشط"),
        default=True,
        help_text=_("هل طريقة الشحن متاحة للاستخدام")
    )
    is_default = models.BooleanField(
        _("افتراضي"),
        default=False,
        help_text=_("هل هي طريقة الشحن الافتراضية")
    )
    sort_order = models.PositiveIntegerField(
        _("ترتيب العرض"),
        default=0,
        help_text=_("ترتيب عرض طريقة الشحن (الأصغر أولاً)")
    )

    # معلومات إضافية - Additional information
    restrictions = models.TextField(
        _("القيود"),
        blank=True,
        help_text=_("أي قيود أو شروط خاصة بطريقة الشحن")
    )
    countries = models.JSONField(
        _("الدول المتاحة"),
        default=list,
        blank=True,
        help_text=_("قائمة الدول التي تتوفر فيها طريقة الشحن (فارغة = كل الدول)")
    )

    # سجلات الوقت - Timestamps
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        verbose_name = _("طريقة شحن")
        verbose_name_plural = _("طرق الشحن")
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ضمان وجود طريقة شحن افتراضية واحدة فقط"""
        if self.is_default:
            # جعل كل الطرق الأخرى غير افتراضية
            ShippingMethod.objects.filter(is_default=True).update(is_default=False)

        super().save(*args, **kwargs)

    def calculate_cost(self, order_subtotal):
        """حساب تكلفة الشحن بناءً على قيمة الطلب"""
        # التحقق من حد الشحن المجاني
        if self.free_shipping_threshold > 0 and order_subtotal >= self.free_shipping_threshold:
            return Decimal('0.00')

        return self.base_cost

    @property
    def delivery_time_text(self):
        """نص وقت التوصيل المعروض للمستخدم"""
        if self.estimated_days_min == self.estimated_days_max:
            return _("{} يوم").format(self.estimated_days_min)

        return _("من {} إلى {} يوم").format(
            self.estimated_days_min,
            self.estimated_days_max
        )


class PaymentTransaction(models.Model):
    """
    نموذج معاملات الدفع - يسجل جميع معاملات الدفع في النظام
    """
    TRANSACTION_STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('processing', _('قيد المعالجة')),
        ('completed', _('مكتملة')),
        ('failed', _('فاشلة')),
        ('refunded', _('مستردة')),
        ('cancelled', _('ملغية')),
    ]

    TRANSACTION_TYPE_CHOICES = [
        ('payment', _('دفع')),
        ('refund', _('استرداد')),
        ('capture', _('تحصيل')),
        ('authorization', _('تفويض')),
        ('void', _('إلغاء')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # العلاقات - Relations
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_transactions',
        verbose_name=_("الطلب")
    )
    checkout_session = models.ForeignKey(
        CheckoutSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_transactions',
        verbose_name=_("جلسة الدفع")
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_("طريقة الدفع")
    )

    # المعلومات الأساسية - Basic information
    transaction_id = models.CharField(
        _("رقم المعاملة"),
        max_length=255,
        help_text=_("رقم المعاملة الفريد من بوابة الدفع")
    )
    amount = models.DecimalField(
        _("المبلغ"),
        max_digits=10,
        decimal_places=2,
        help_text=_("مبلغ المعاملة")
    )
    currency = models.CharField(
        _("العملة"),
        max_length=3,
        default='SAR',
        help_text=_("رمز العملة (مثل SAR, USD)")
    )

    # الحالة والنوع - Status and type
    status = models.CharField(
        _("الحالة"),
        max_length=20,
        choices=TRANSACTION_STATUS_CHOICES,
        default='pending',
        help_text=_("حالة المعاملة")
    )
    transaction_type = models.CharField(
        _("نوع المعاملة"),
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        default='payment',
        help_text=_("نوع المعاملة")
    )

    # معلومات إضافية - Additional information
    gateway_response = models.JSONField(
        _("استجابة بوابة الدفع"),
        default=dict,
        blank=True,
        help_text=_("البيانات الكاملة المستلمة من بوابة الدفع")
    )
    gateway_message = models.TextField(
        _("رسالة بوابة الدفع"),
        blank=True,
        help_text=_("رسالة الخطأ أو النجاح من بوابة الدفع")
    )

    # معلومات الأمان - Security information
    ip_address = models.GenericIPAddressField(
        _("عنوان IP"),
        null=True,
        blank=True,
        help_text=_("عنوان IP للمستخدم أثناء المعاملة")
    )
    user_agent = models.TextField(
        _("معلومات المتصفح"),
        blank=True,
        help_text=_("معلومات متصفح المستخدم")
    )

    # سجلات الوقت - Timestamps
    created_at = models.DateTimeField(
        _("تاريخ الإنشاء"),
        auto_now_add=True,
        help_text=_("تاريخ بدء المعاملة")
    )
    updated_at = models.DateTimeField(
        _("تاريخ التحديث"),
        auto_now=True,
        help_text=_("تاريخ آخر تحديث للمعاملة")
    )
    completed_at = models.DateTimeField(
        _("تاريخ الاكتمال"),
        null=True,
        blank=True,
        help_text=_("تاريخ اكتمال المعاملة")
    )

    class Meta:
        verbose_name = _("معاملة دفع")
        verbose_name_plural = _("معاملات الدفع")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['checkout_session']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.transaction_id}"

    def save(self, *args, **kwargs):
        """تحديث تاريخ الاكتمال عند تغيير الحالة"""
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()

        super().save(*args, **kwargs)

    def mark_as_completed(self, gateway_response=None):
        """تعليم المعاملة كمكتملة"""
        self.status = 'completed'
        self.completed_at = timezone.now()

        if gateway_response:
            self.gateway_response = gateway_response

        self.save()

    def mark_as_failed(self, gateway_message=None, gateway_response=None):
        """تعليم المعاملة كفاشلة"""
        self.status = 'failed'

        if gateway_message:
            self.gateway_message = gateway_message

        if gateway_response:
            self.gateway_response = gateway_response

        self.save()


class Coupon(models.Model):
    """
    نموذج كوبونات الخصم - يمثل كوبون خصم يمكن تطبيقه أثناء عملية الدفع
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', _('نسبة مئوية')),
        ('fixed_amount', _('مبلغ ثابت')),
        ('free_shipping', _('شحن مجاني')),
    ]

    code = models.CharField(
        _("كود الكوبون"),
        max_length=50,
        unique=True,
        help_text=_("كود الكوبون الذي يدخله المستخدم")
    )
    description = models.CharField(
        _("الوصف"),
        max_length=200,
        blank=True,
        help_text=_("وصف الكوبون المعروض للمستخدم")
    )

    # نوع وقيمة الخصم - Discount type and value
    discount_type = models.CharField(
        _("نوع الخصم"),
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage',
        help_text=_("نوع الخصم المطبق")
    )
    discount_value = models.DecimalField(
        _("قيمة الخصم"),
        max_digits=10,
        decimal_places=2,
        help_text=_("قيمة الخصم (نسبة مئوية أو مبلغ ثابت)")
    )
    min_order_value = models.DecimalField(
        _("الحد الأدنى لقيمة الطلب"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("الحد الأدنى لقيمة الطلب لتطبيق الكوبون")
    )
    max_discount_amount = models.DecimalField(
        _("الحد الأقصى لمبلغ الخصم"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("الحد الأقصى لمبلغ الخصم (0 = غير محدود)")
    )

    # قيود الاستخدام - Usage restrictions
    is_active = models.BooleanField(
        _("نشط"),
        default=True,
        help_text=_("هل الكوبون نشط ويمكن استخدامه")
    )
    start_date = models.DateTimeField(
        _("تاريخ البداية"),
        null=True,
        blank=True,
        help_text=_("تاريخ بداية صلاحية الكوبون")
    )
    end_date = models.DateTimeField(
        _("تاريخ النهاية"),
        null=True,
        blank=True,
        help_text=_("تاريخ نهاية صلاحية الكوبون")
    )
    max_uses = models.PositiveIntegerField(
        _("الحد الأقصى للاستخدام"),
        default=0,
        help_text=_("الحد الأقصى لعدد مرات استخدام الكوبون (0 = غير محدود)")
    )
    max_uses_per_user = models.PositiveIntegerField(
        _("الحد الأقصى للاستخدام للمستخدم"),
        default=0,
        help_text=_("الحد الأقصى لعدد مرات استخدام الكوبون لكل مستخدم (0 = غير محدود)")
    )

    # الإحصائيات - Statistics
    uses_count = models.PositiveIntegerField(
        _("عدد مرات الاستخدام"),
        default=0,
        editable=False,
        help_text=_("عدد مرات استخدام الكوبون")
    )

    # سجلات الوقت - Timestamps
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        verbose_name = _("كوبون خصم")
        verbose_name_plural = _("كوبونات الخصم")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return self.code

    def is_valid(self, order_value=None, user=None):
        """التحقق من صلاحية الكوبون للاستخدام"""
        # التحقق من حالة النشاط
        if not self.is_active:
            return False

        # التحقق من تاريخ الصلاحية
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False

        # التحقق من الحد الأقصى للاستخدام
        if self.max_uses > 0 and self.uses_count >= self.max_uses:
            return False

        # التحقق من الحد الأقصى للمستخدم
        if user and self.max_uses_per_user > 0:
            user_count = CouponUsage.objects.filter(coupon=self, user=user).count()
            if user_count >= self.max_uses_per_user:
                return False

        # التحقق من الحد الأدنى لقيمة الطلب
        if order_value is not None and self.min_order_value > 0:
            if order_value < self.min_order_value:
                return False

        return True

    def calculate_discount(self, order_value):
        """حساب مبلغ الخصم المطبق على قيمة الطلب"""
        if self.discount_type == 'percentage':
            # خصم بنسبة مئوية
            discount = order_value * (self.discount_value / 100)

            # تطبيق الحد الأقصى لمبلغ الخصم إذا كان محدداً
            if self.max_discount_amount > 0:
                discount = min(discount, self.max_discount_amount)

            return discount.quantize(Decimal('0.01'))

        elif self.discount_type == 'fixed_amount':
            # خصم بمبلغ ثابت
            return min(self.discount_value, order_value)

        elif self.discount_type == 'free_shipping':
            # خصم الشحن المجاني يتم تطبيقه في مكان آخر
            return Decimal('0.00')

        return Decimal('0.00')

    def increment_usage(self, user=None):
        """زيادة عدد مرات استخدام الكوبون"""
        self.uses_count += 1
        self.save(update_fields=['uses_count'])

        # تسجيل استخدام الكوبون للمستخدم
        if user:
            CouponUsage.objects.create(coupon=self, user=user)


class CouponUsage(models.Model):
    """
    نموذج استخدام الكوبونات - يسجل استخدام الكوبونات بواسطة المستخدمين
    """
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='usages',
        verbose_name=_("الكوبون")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coupon_usages',
        verbose_name=_("المستخدم")
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coupon_usages',
        verbose_name=_("الطلب")
    )
    used_at = models.DateTimeField(_("تاريخ الاستخدام"), auto_now_add=True)

    class Meta:
        verbose_name = _("استخدام كوبون")
        verbose_name_plural = _("استخدامات الكوبونات")
        ordering = ['-used_at']
        unique_together = [['coupon', 'user', 'order']]

    def __str__(self):
        return f"{self.coupon.code} - {self.user.username}"