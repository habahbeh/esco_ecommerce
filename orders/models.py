from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from cart.models import Cart
import uuid


class Order(models.Model):
    """
    نموذج الطلب - يمثل طلب الشراء
    Order model - represents a purchase order
    """
    STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('processing', _('قيد المعالجة')),
        ('shipped', _('تم الشحن')),
        ('delivered', _('تم التسليم')),
        ('cancelled', _('ملغي')),
        ('refunded', _('مسترجع')),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('paid', _('مدفوع')),
        ('failed', _('فشل')),
        ('refunded', _('مسترجع')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(_("رقم الطلب"), max_length=20, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                             related_name='orders', verbose_name=_("المستخدم"))
    cart = models.OneToOneField(Cart, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name=_("سلة التسوق"))

    # معلومات العميل - Customer information
    full_name = models.CharField(_("الاسم الكامل"), max_length=100)
    email = models.EmailField(_("البريد الإلكتروني"))
    phone = models.CharField(_("رقم الهاتف"), max_length=20)

    # معلومات الشحن - Shipping information
    shipping_address = models.TextField(_("عنوان الشحن"))
    shipping_city = models.CharField(_("المدينة"), max_length=100)
    shipping_state = models.CharField(_("المحافظة/الولاية"), max_length=100)
    shipping_country = models.CharField(_("الدولة"), max_length=100)
    shipping_postal_code = models.CharField(_("الرمز البريدي"), max_length=20, blank=True)

    # معلومات الدفع - Payment information
    total_price = models.DecimalField(_("السعر الإجمالي"), max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(_("تكلفة الشحن"), max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("مبلغ الضريبة"), max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(_("المجموع الكلي"), max_digits=10, decimal_places=2)
    payment_method = models.CharField(_("طريقة الدفع"), max_length=50, blank=True)
    payment_id = models.CharField(_("معرف الدفع"), max_length=100, blank=True)

    # الحالة والتواريخ - Status and dates
    status = models.CharField(_("حالة الطلب"), max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(_("حالة الدفع"), max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    notes = models.TextField(_("ملاحظات"), blank=True)

    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        verbose_name = _("طلب")
        verbose_name_plural = _("الطلبات")
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        # إنشاء رقم الطلب إذا لم يكن موجودًا - Create order number if it doesn't exist
        if not self.order_number:
            self.order_number = self._generate_order_number()

        # حساب المجموع الكلي - Calculate grand total
        self.grand_total = self.total_price + self.shipping_cost + self.tax_amount

        super().save(*args, **kwargs)

    def _generate_order_number(self):
        """
        إنشاء رقم طلب فريد
        Generate a unique order number
        """
        import random
        import string
        from django.utils import timezone

        # استخدام الوقت الحالي والأحرف العشوائية لإنشاء رقم طلب فريد
        # Use current time and random characters to create a unique order number
        prefix = timezone.now().strftime('%y%m%d')
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{prefix}-{suffix}"


class OrderItem(models.Model):
    """
    نموذج عنصر الطلب - يمثل عنصرًا في الطلب
    Order item model - represents an item in the order
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items',
                              verbose_name=_("الطلب"))
    product_name = models.CharField(_("اسم المنتج"), max_length=255)
    product_id = models.CharField(_("معرف المنتج"), max_length=100)
    variant_name = models.CharField(_("اسم المتغير"), max_length=100, blank=True)
    variant_id = models.CharField(_("معرف المتغير"), max_length=100, blank=True)
    quantity = models.PositiveIntegerField(_("الكمية"), default=1)
    unit_price = models.DecimalField(_("سعر الوحدة"), max_digits=10, decimal_places=2)
    total_price = models.DecimalField(_("السعر الإجمالي"), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _("عنصر الطلب")
        verbose_name_plural = _("عناصر الطلب")

    def __str__(self):
        variant_info = f" ({self.variant_name})" if self.variant_name else ""
        return f"{self.product_name}{variant_info} x {self.quantity}"

    def save(self, *args, **kwargs):
        # حساب السعر الإجمالي - Calculate total price
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)