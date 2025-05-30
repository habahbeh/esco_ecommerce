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
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
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

    class Meta:
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