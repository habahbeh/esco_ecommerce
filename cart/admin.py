from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """
    إضافة عناصر السلة مباشرة في صفحة تحرير السلة
    Add cart items directly in the cart edit page
    """
    model = CartItem
    extra = 0
    fields = ('product', 'variant', 'quantity', 'unit_price', 'total_price', 'added_at')
    readonly_fields = ('unit_price', 'total_price', 'added_at')

    def unit_price(self, obj):
        """عرض سعر الوحدة - Display unit price"""
        if obj.id:
            return obj.unit_price
        return "-"

    unit_price.short_description = _("سعر الوحدة")

    def total_price(self, obj):
        """عرض السعر الإجمالي - Display total price"""
        if obj.id:
            return obj.total_price
        return "-"

    total_price.short_description = _("السعر الإجمالي")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """
    إدارة سلة التسوق - تسمح للمشرفين بعرض وإدارة سلات التسوق
    Cart admin - allows administrators to view and manage shopping carts
    """
    list_display = ('id', 'user', 'session_key', 'total_items_count', 'total_price_display', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'session_key')
    readonly_fields = ('created_at', 'updated_at', 'total_price_display')
    date_hierarchy = 'created_at'
    inlines = [CartItemInline]

    def total_items_count(self, obj):
        """عرض إجمالي عدد العناصر في السلة - Display total number of items in the cart"""
        return obj.total_items

    total_items_count.short_description = _("عدد العناصر")

    def total_price_display(self, obj):
        """عرض إجمالي سعر السلة - Display total cart price"""
        return obj.total_price

    total_price_display.short_description = _("المجموع")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """
    إدارة عناصر سلة التسوق - تسمح للمشرفين بعرض وإدارة عناصر سلة التسوق
    Cart item admin - allows administrators to view and manage cart items
    """
    list_display = (
    'id', 'cart', 'product', 'variant', 'quantity', 'unit_price_display', 'total_price_display', 'added_at')
    list_filter = ('added_at', 'updated_at')
    search_fields = ('cart__user__username', 'product__name', 'product__sku')
    readonly_fields = ('added_at', 'updated_at', 'unit_price_display', 'total_price_display')

    def unit_price_display(self, obj):
        """عرض سعر الوحدة - Display unit price"""
        return obj.unit_price

    unit_price_display.short_description = _("سعر الوحدة")

    def total_price_display(self, obj):
        """عرض السعر الإجمالي - Display total price"""
        return obj.total_price

    total_price_display.short_description = _("السعر الإجمالي")