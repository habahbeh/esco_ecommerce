from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from products.models import Product, ProductVariant
import uuid


class Cart(models.Model):
    """
    نموذج سلة التسوق - يخزن سلة التسوق للمستخدم
    Cart model - stores the user's shopping cart
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             null=True, blank=True, related_name='carts',
                             verbose_name=_("المستخدم"))
    session_key = models.CharField(_("مفتاح الجلسة"), max_length=40, null=True, blank=True)
    is_active = models.BooleanField(_("نشطة"), default=True,
                                    help_text=_("تشير إلى ما إذا كانت السلة نشطة أو تم تحويلها إلى طلب"))
    converted_to_order = models.BooleanField(_("تم تحويلها إلى طلب"), default=False,
                                             help_text=_("تشير إلى ما إذا كانت السلة قد تم تحويلها إلى طلب"))
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        app_label = 'cart'
        verbose_name = _("سلة التسوق")
        verbose_name_plural = _("سلات التسوق")

    def __str__(self):
        return f"Cart {self.id}"

    @property
    def total_price(self):
        """
        حساب إجمالي سعر السلة
        Calculate the total price of the cart
        """
        return sum(item.total_price for item in self.items.all())

    @property
    def total_items(self):
        """
        حساب إجمالي عدد العناصر في السلة
        Calculate the total number of items in the cart
        """
        return sum(item.quantity for item in self.items.all())

    @classmethod
    def get_cart_for_user_or_session(cls, user=None, session_key=None):
        """
        الحصول على سلة التسوق للمستخدم أو الجلسة
        Get the cart for a user or session
        """
        if user and user.is_authenticated:
            cart, created = cls.objects.get_or_create(user=user, defaults={'session_key': session_key})
        elif session_key:
            cart, created = cls.objects.get_or_create(session_key=session_key, user=None)
        else:
            cart = None

        return cart

    def convert_to_order(self):
        """
        تحويل السلة إلى طلب
        Convert cart to order
        """
        from orders.models import Order, OrderItem

        if self.converted_to_order:
            # السلة تم تحويلها بالفعل
            return None

        if not self.items.exists():
            # لا توجد عناصر في السلة
            return None

        # إنشاء الطلب
        order = Order.objects.create(
            user=self.user,
            cart=self,
            total_price=self.total_price,
            grand_total=self.total_price  # سيتم تعديله لاحقاً
        )

        # إنشاء عناصر الطلب
        for cart_item in self.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,  # مرجع للمنتج
                variant=cart_item.variant,  # مرجع للمتغير
                product_name=cart_item.product.name,
                variant_name=cart_item.variant.name if cart_item.variant else '',
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                total_price=cart_item.total_price,
                discount=cart_item.applied_discount if hasattr(cart_item, 'applied_discount') else None,
                discount_amount=cart_item.discount_amount if hasattr(cart_item, 'discount_amount') else 0
            )

        # تحديث حالة السلة
        self.converted_to_order = True
        self.is_active = False
        self.save()

        return order


class CartItem(models.Model):
    """
    نموذج عنصر السلة - يمثل عنصرًا في سلة التسوق
    Cart item model - represents an item in the shopping cart
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items',
                             verbose_name=_("سلة التسوق"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_("المنتج"))
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name=_("المتغير"))
    quantity = models.PositiveIntegerField(_("الكمية"), default=1)
    added_at = models.DateTimeField(_("تاريخ الإضافة"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    # إضافة الخصم
    applied_discount = models.ForeignKey('products.ProductDiscount', on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='applied_to_cart_items',
                                         verbose_name=_("الخصم المطبق"))

    class Meta:
        app_label = 'cart'
        verbose_name = _("عنصر السلة")
        verbose_name_plural = _("عناصر السلة")
        unique_together = ('cart', 'product', 'variant')

    def __str__(self):
        variant_name = f" ({self.variant.name})" if self.variant else ""
        return f"{self.product.name}{variant_name} x {self.quantity}"

    @property
    def unit_price(self):
        """
        حساب سعر الوحدة (يعتمد على ما إذا كان هناك متغير أم لا)
        Calculate the unit price (depends on whether there is a variant or not)
        """
        if self.variant:
            return self.variant.price
        return self.product.current_price

    @property
    def total_price(self):
        """
        حساب السعر الإجمالي للعنصر
        Calculate the total price of the item
        """
        return self.unit_price * self.quantity

    @property
    def discount_amount(self):
        """
        حساب مبلغ الخصم المطبق على هذا العنصر
        Calculate the discount amount applied to this item
        """
        if not self.applied_discount:
            return 0

        total = self.total_price
        if self.applied_discount.discount_type == 'percentage':
            return total * (self.applied_discount.value / 100)
        elif self.applied_discount.discount_type == 'fixed_amount':
            return min(self.applied_discount.value, total)
        return 0

    @property
    def discounted_total(self):
        """
        حساب المجموع بعد تطبيق الخصم
        Calculate the total after applying discount
        """
        return max(0, self.total_price - self.discount_amount)