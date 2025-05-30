"""
نظام إدارة المخزون للمنتجات
Inventory Management System for Products
"""

from django.db import models, transaction
from django.db.models import F, Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import logging

from .models import Product, ProductVariant

logger = logging.getLogger(__name__)


class InventoryManager:
    """
    مدير المخزون الرئيسي
    Main Inventory Manager
    """

    @staticmethod
    @transaction.atomic
    def update_stock(product_or_variant, quantity, operation='set', reason='manual'):
        """
        تحديث مخزون منتج أو متغير
        Update stock for product or variant

        Args:
            product_or_variant: Product or ProductVariant instance
            quantity: int - الكمية
            operation: str - 'set', 'add', 'subtract'
            reason: str - سبب التحديث
        """
        if isinstance(product_or_variant, ProductVariant):
            item = product_or_variant
            is_variant = True
        else:
            item = product_or_variant
            is_variant = False

        # Lock the record for update
        item = item.__class__.objects.select_for_update().get(pk=item.pk)

        old_quantity = item.stock_quantity

        if operation == 'set':
            item.stock_quantity = quantity
        elif operation == 'add':
            item.stock_quantity = F('stock_quantity') + quantity
        elif operation == 'subtract':
            if item.stock_quantity < quantity:
                raise ValidationError(_("الكمية المطلوبة غير متوفرة"))
            item.stock_quantity = F('stock_quantity') - quantity
        else:
            raise ValueError(f"Invalid operation: {operation}")

        item.save(update_fields=['stock_quantity'])
        item.refresh_from_db()

        # Update stock status
        InventoryManager.update_stock_status(item)

        # Log the change
        StockMovement.objects.create(
            product=item.product if is_variant else item,
            variant=item if is_variant else None,
            movement_type='adjustment',
            quantity=quantity if operation == 'add' else -quantity if operation == 'subtract' else quantity - old_quantity,
            old_stock=old_quantity,
            new_stock=item.stock_quantity,
            reason=reason
        )

        # Check low stock alert
        InventoryManager.check_low_stock_alert(item)

        return item

    @staticmethod
    def update_stock_status(item):
        """
        تحديث حالة المخزون
        Update stock status based on quantity
        """
        if not item.track_inventory:
            return

        if item.stock_quantity <= 0:
            item.stock_status = 'out_of_stock'
        elif item.stock_quantity <= item.min_stock_level:
            item.stock_status = 'low_stock'
        else:
            item.stock_status = 'in_stock'

        item.save(update_fields=['stock_status'])

    @staticmethod
    def check_low_stock_alert(item):
        """
        التحقق من تنبيه انخفاض المخزون
        Check and send low stock alerts
        """
        if item.stock_quantity <= item.min_stock_level:
            # Send notification (implement based on your notification system)
            logger.warning(f"Low stock alert for {item}: {item.stock_quantity} units left")

            # Create alert record
            StockAlert.objects.get_or_create(
                product=item.product if hasattr(item, 'product') else item,
                variant=item if isinstance(item, ProductVariant) else None,
                alert_type='low_stock',
                defaults={
                    'current_stock': item.stock_quantity,
                    'threshold': item.min_stock_level
                }
            )

    @staticmethod
    @transaction.atomic
    def reserve_stock(order_item, quantity):
        """
        حجز مخزون لطلب
        Reserve stock for an order
        """
        if order_item.variant:
            item = order_item.variant
        else:
            item = order_item.product

        # Lock the record
        item = item.__class__.objects.select_for_update().get(pk=item.pk)

        available = item.stock_quantity - getattr(item, 'reserved_quantity', 0)

        if available < quantity:
            raise ValidationError(
                _(f"الكمية المتاحة ({available}) أقل من المطلوبة ({quantity})")
            )

        if hasattr(item, 'reserved_quantity'):
            item.reserved_quantity = F('reserved_quantity') + quantity
            item.save(update_fields=['reserved_quantity'])

        # Create reservation record
        StockReservation.objects.create(
            order_item=order_item,
            product=order_item.product,
            variant=order_item.variant,
            quantity=quantity
        )

        return True

    @staticmethod
    @transaction.atomic
    def release_reservation(order_item):
        """
        إلغاء حجز المخزون
        Release reserved stock
        """
        reservations = StockReservation.objects.filter(
            order_item=order_item,
            is_active=True
        )

        for reservation in reservations:
            if reservation.variant and hasattr(reservation.variant, 'reserved_quantity'):
                reservation.variant.reserved_quantity = F('reserved_quantity') - reservation.quantity
                reservation.variant.save(update_fields=['reserved_quantity'])

            reservation.is_active = False
            reservation.released_at = timezone.now()
            reservation.save()

    @staticmethod
    @transaction.atomic
    def confirm_sale(order_item, quantity):
        """
        تأكيد البيع وخصم المخزون
        Confirm sale and deduct stock
        """
        if order_item.variant:
            item = order_item.variant
        else:
            item = order_item.product

        # Deduct stock
        InventoryManager.update_stock(item, quantity, 'subtract', f'Sale - Order #{order_item.order.id}')

        # Update sales count
        item.sales_count = F('sales_count') + quantity
        item.save(update_fields=['sales_count'])

        # Release any reservations
        InventoryManager.release_reservation(order_item)

        # Log the sale
        StockMovement.objects.create(
            product=order_item.product,
            variant=order_item.variant,
            movement_type='sale',
            quantity=-quantity,
            order=order_item.order,
            reason=f'Order #{order_item.order.id}'
        )

    @staticmethod
    def get_stock_report(category=None, brand=None, low_stock_only=False):
        """
        الحصول على تقرير المخزون
        Get stock report
        """
        products = Product.objects.filter(
            is_active=True,
            track_inventory=True
        ).select_related('category', 'brand')

        if category:
            products = products.filter(category=category)

        if brand:
            products = products.filter(brand=brand)

        if low_stock_only:
            products = products.filter(
                Q(stock_quantity__lte=F('min_stock_level')) |
                Q(stock_status='out_of_stock')
            )

        report = []
        for product in products:
            # Product level stock
            product_data = {
                'product': product,
                'total_stock': product.stock_quantity,
                'reserved': 0,
                'available': product.stock_quantity,
                'value': product.stock_quantity * product.base_price,
                'status': product.stock_status,
                'variants': []
            }

            # Variant level stock
            for variant in product.variants.filter(is_active=True):
                variant_data = {
                    'variant': variant,
                    'stock': variant.stock_quantity,
                    'reserved': getattr(variant, 'reserved_quantity', 0),
                    'available': variant.available_quantity,
                    'value': variant.stock_quantity * variant.current_price
                }
                product_data['variants'].append(variant_data)
                product_data['total_stock'] += variant.stock_quantity
                product_data['reserved'] += getattr(variant, 'reserved_quantity', 0)
                product_data['value'] += variant_data['value']

            product_data['available'] = product_data['total_stock'] - product_data['reserved']
            report.append(product_data)

        return report

    @staticmethod
    def get_stock_valuation():
        """
        حساب قيمة المخزون الإجمالية
        Calculate total stock valuation
        """
        from django.db.models import Sum

        # Product stock value
        product_value = Product.objects.filter(
            is_active=True,
            track_inventory=True
        ).aggregate(
            total_value=Sum(F('stock_quantity') * F('base_price'))
        )['total_value'] or Decimal('0')

        # Variant stock value
        variant_value = ProductVariant.objects.filter(
            is_active=True,
            product__track_inventory=True
        ).aggregate(
            total_value=Sum(F('stock_quantity') * (F('product__base_price') + F('price_adjustment')))
        )['total_value'] or Decimal('0')

        return {
            'product_value': product_value,
            'variant_value': variant_value,
            'total_value': product_value + variant_value
        }


class StockMovement(models.Model):
    """
    نموذج حركات المخزون
    Stock Movement Model
    """
    MOVEMENT_TYPES = [
        ('purchase', _('شراء')),
        ('sale', _('بيع')),
        ('return', _('إرجاع')),
        ('adjustment', _('تعديل')),
        ('transfer', _('نقل')),
        ('damage', _('تلف')),
        ('loss', _('فقدان')),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_movements',
        verbose_name=_("المنتج")
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name=_("المتغير")
    )
    movement_type = models.CharField(
        _("نوع الحركة"),
        max_length=20,
        choices=MOVEMENT_TYPES
    )
    quantity = models.IntegerField(
        _("الكمية"),
        help_text=_("موجب للإضافة، سالب للخصم")
    )
    old_stock = models.PositiveIntegerField(_("المخزون السابق"))
    new_stock = models.PositiveIntegerField(_("المخزون الجديد"))
    reason = models.CharField(_("السبب"), max_length=255)
    reference = models.CharField(
        _("المرجع"),
        max_length=100,
        blank=True,
        help_text=_("رقم الفاتورة، رقم الطلب، إلخ")
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name=_("الطلب")
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_movements',
        verbose_name=_("المستخدم")
    )
    created_at = models.DateTimeField(_("تاريخ الحركة"), auto_now_add=True)
    notes = models.TextField(_("ملاحظات"), blank=True)

    class Meta:
        verbose_name = _("حركة مخزون")
        verbose_name_plural = _("حركات المخزون")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'created_at']),
            models.Index(fields=['movement_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name} ({self.quantity})"


class StockAlert(models.Model):
    """
    نموذج تنبيهات المخزون
    Stock Alert Model
    """
    ALERT_TYPES = [
        ('low_stock', _('مخزون منخفض')),
        ('out_of_stock', _('نفاد المخزون')),
        ('overstock', _('مخزون زائد')),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_alerts',
        verbose_name=_("المنتج")
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='stock_alerts',
        verbose_name=_("المتغير")
    )
    alert_type = models.CharField(
        _("نوع التنبيه"),
        max_length=20,
        choices=ALERT_TYPES
    )
    current_stock = models.PositiveIntegerField(_("المخزون الحالي"))
    threshold = models.PositiveIntegerField(_("الحد الأدنى"))
    is_resolved = models.BooleanField(_("تم الحل"), default=False)
    created_at = models.DateTimeField(_("تاريخ التنبيه"), auto_now_add=True)
    resolved_at = models.DateTimeField(_("تاريخ الحل"), null=True, blank=True)
    resolved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts',
        verbose_name=_("تم الحل بواسطة")
    )

    class Meta:
        verbose_name = _("تنبيه مخزون")
        verbose_name_plural = _("تنبيهات المخزون")
        ordering = ['-created_at']
        unique_together = [['product', 'variant', 'alert_type', 'is_resolved']]

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.product.name}"

    def resolve(self, user):
        """حل التنبيه"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save()


class StockReservation(models.Model):
    """
    نموذج حجز المخزون
    Stock Reservation Model
    """
    order_item = models.ForeignKey(
        'orders.OrderItem',
        on_delete=models.CASCADE,
        related_name='stock_reservations',
        verbose_name=_("بند الطلب")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_reservations',
        verbose_name=_("المنتج")
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='stock_reservations',
        verbose_name=_("المتغير")
    )
    quantity = models.PositiveIntegerField(_("الكمية المحجوزة"))
    is_active = models.BooleanField(_("نشط"), default=True)
    created_at = models.DateTimeField(_("تاريخ الحجز"), auto_now_add=True)
    expires_at = models.DateTimeField(
        _("تاريخ انتهاء الحجز"),
        null=True,
        blank=True,
        help_text=_("إذا لم يتم تأكيد الطلب قبل هذا التاريخ، سيتم إلغاء الحجز")
    )
    released_at = models.DateTimeField(_("تاريخ الإلغاء"), null=True, blank=True)

    class Meta:
        verbose_name = _("حجز مخزون")
        verbose_name_plural = _("حجوزات المخزون")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_item', 'is_active']),
            models.Index(fields=['expires_at', 'is_active']),
        ]

    def __str__(self):
        return f"Reservation for {self.product.name} - {self.quantity} units"

    def is_expired(self):
        """التحقق من انتهاء الحجز"""
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False

    def release(self):
        """إلغاء الحجز"""
        if self.is_active:
            InventoryManager.release_reservation(self.order_item)


class InventoryAdjustment(models.Model):
    """
    نموذج تعديلات المخزون اليدوية
    Manual Inventory Adjustment Model
    """
    ADJUSTMENT_REASONS = [
        ('count', _('جرد')),
        ('damage', _('تلف')),
        ('loss', _('فقدان')),
        ('found', _('عثور')),
        ('correction', _('تصحيح')),
        ('other', _('أخرى')),
    ]

    reference_number = models.CharField(
        _("رقم المرجع"),
        max_length=50,
        unique=True
    )
    adjustment_date = models.DateTimeField(
        _("تاريخ التعديل"),
        default=timezone.now
    )
    reason = models.CharField(
        _("السبب"),
        max_length=20,
        choices=ADJUSTMENT_REASONS
    )
    notes = models.TextField(_("ملاحظات"))
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='inventory_adjustments',
        verbose_name=_("أنشئ بواسطة")
    )
    approved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_adjustments',
        verbose_name=_("اعتمد بواسطة")
    )
    is_approved = models.BooleanField(_("معتمد"), default=False)
    approved_at = models.DateTimeField(_("تاريخ الاعتماد"), null=True, blank=True)
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)

    class Meta:
        verbose_name = _("تعديل مخزون")
        verbose_name_plural = _("تعديلات المخزون")
        ordering = ['-created_at']
        permissions = [
            ("approve_adjustment", "Can approve inventory adjustments"),
        ]

    def __str__(self):
        return f"{self.reference_number} - {self.get_reason_display()}"

    def approve(self, user):
        """اعتماد التعديل"""
        if not self.is_approved:
            self.is_approved = True
            self.approved_by = user
            self.approved_at = timezone.now()
            self.save()

            # Apply adjustments
            for item in self.items.all():
                InventoryManager.update_stock(
                    item.product if not item.variant else item.variant,
                    item.new_quantity,
                    'set',
                    f'Adjustment #{self.reference_number} - {self.get_reason_display()}'
                )


class InventoryAdjustmentItem(models.Model):
    """
    نموذج بنود تعديل المخزون
    Inventory Adjustment Item Model
    """
    adjustment = models.ForeignKey(
        InventoryAdjustment,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("التعديل")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name=_("المنتج")
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("المتغير")
    )
    old_quantity = models.PositiveIntegerField(_("الكمية السابقة"))
    new_quantity = models.PositiveIntegerField(_("الكمية الجديدة"))
    difference = models.IntegerField(_("الفرق"))
    notes = models.CharField(_("ملاحظات"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("بند تعديل مخزون")
        verbose_name_plural = _("بنود تعديل المخزون")
        unique_together = [['adjustment', 'product', 'variant']]

    def __str__(self):
        return f"{self.product.name} - {self.difference:+d}"

    def save(self, *args, **kwargs):
        self.difference = self.new_quantity - self.old_quantity
        super().save(*args, **kwargs)