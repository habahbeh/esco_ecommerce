from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from cart.models import Cart
import uuid
from model_utils import FieldTracker


class Order(models.Model):
    """
    نموذج الطلب - يمثل طلب الشراء
    Order model - represents a purchase order
    """

    STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('confirmed', _('تأكيد الطلب')),
        ('closed', _('إغلاق الطلب')),
        ('cancelled', _('ملغي')),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', _('قيد الانتظار')),
        ('paid', _('مدفوع')),
        ('failed', _('فشل')),
        ('refunded', _('مسترجع')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
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

    # إضافة حقول لدعم الخصومات
    discount_amount = models.DecimalField(_("مبلغ الخصم"), max_digits=10, decimal_places=2, default=0)
    discount = models.ForeignKey('products.ProductDiscount', on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='orders',
                                 verbose_name=_("الخصم المطبق"))
    coupon_code = models.CharField(_("كود الكوبون"), max_length=50, blank=True)

    # إضافة tracker لتتبع تغييرات حالة الطلب وحالة الدفع
    tracker = FieldTracker(['status', 'payment_status'])

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

        self.grand_total = self.total_price + self.shipping_cost + self.tax_amount - self.discount_amount

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

    @classmethod
    def create_from_cart(cls, cart, user_data, shipping_data, payment_data):
        """
        إنشاء طلب من سلة التسوق
        Create an order from cart
        """
        if not cart or not cart.items.exists():
            return None

        # إنشاء الطلب الجديد
        order = cls.objects.create(
            user=cart.user,
            cart=cart,
            full_name=user_data.get('full_name', ''),
            email=user_data.get('email', ''),
            phone=user_data.get('phone', ''),
            shipping_address=shipping_data.get('address', ''),
            shipping_city=shipping_data.get('city', ''),
            shipping_state=shipping_data.get('state', ''),
            shipping_country=shipping_data.get('country', ''),
            shipping_postal_code=shipping_data.get('postal_code', ''),
            total_price=cart.total_price,
            shipping_cost=shipping_data.get('shipping_cost', 0),
            tax_amount=cart.total_price * Decimal('0.15'),  # 15% ضريبة القيمة المضافة مثلاً
            discount_amount=cart.discount_amount if hasattr(cart, 'discount_amount') else 0,
            discount=cart.applied_discount if hasattr(cart, 'applied_discount') else None,
            payment_method=payment_data.get('method', ''),
            payment_id=payment_data.get('id', ''),
            notes=user_data.get('notes', ''),
        )

        # إنشاء عناصر الطلب - نقوم بتحويل كل عنصر في السلة إلى عنصر في الطلب
        for cart_item in cart.items.all():
            # الحصول على المنتج والمتغير (إن وجد)
            product = cart_item.product
            variant = cart_item.variant

            # حساب مبلغ الخصم إن وجد
            discount_amount = 0
            discount_obj = None
            if hasattr(cart_item, 'applied_discount') and cart_item.applied_discount:
                discount_obj = cart_item.applied_discount
                discount_amount = cart_item.discount_amount

            # إنشاء عنصر الطلب
            OrderItem.objects.create(
                order=order,
                product_name=product.name,
                product_id=str(product.id),
                variant_name=variant.name if variant else '',
                variant_id=str(variant.id) if variant else '',
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                total_price=cart_item.total_price,
                discount=discount_obj,
                discount_amount=discount_amount
            )

        # تحديث حالة السلة
        cart.converted_to_order = True
        cart.is_active = False
        cart.save()

        return order


class OrderItem(models.Model):
    """
    نموذج عنصر الطلب - يمثل عنصرًا في الطلب
    Order item model - represents an item in the order
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items',
                              verbose_name=_("الطلب"))

    # مراجع للمنتجات بدلاً من تخزين النصوص فقط
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,  # حتى لو حُذف المنتج، لن يتأثر الطلب
        null=True,
        related_name='order_items',
        verbose_name=_("المنتج")
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
        verbose_name=_("المتغير")
    )

    # نحتفظ بالأسماء لأغراض العرض والتاريخ
    product_name = models.CharField(_("اسم المنتج"), max_length=255)
    variant_name = models.CharField(_("اسم المتغير"), max_length=100, blank=True)

    quantity = models.PositiveIntegerField(_("الكمية"), default=1)

    # أسعار في وقت الطلب - مهمة للسجل التاريخي
    unit_price = models.DecimalField(_("سعر الوحدة"), max_digits=10, decimal_places=2)
    total_price = models.DecimalField(_("السعر الإجمالي"), max_digits=10, decimal_places=2)

    # إضافة حقول الخصم
    discount = models.ForeignKey('products.ProductDiscount', on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='order_items',
                                 verbose_name=_("الخصم المطبق"))
    discount_amount = models.DecimalField(_("مبلغ الخصم"), max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("عنصر الطلب")
        verbose_name_plural = _("عناصر الطلب")

    def __str__(self):
        variant_info = f" ({self.variant_name})" if self.variant_name else ""
        return f"{self.product_name}{variant_info} x {self.quantity}"

    @property
    def discounted_total(self):
        """
        حساب المجموع بعد تطبيق الخصم
        Calculate the total after applying discount
        """
        return max(0, self.total_price - self.discount_amount)