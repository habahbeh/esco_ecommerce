"""
ملف تهيئة حزمة النماذج - يقوم باستيراد جميع النماذج لسهولة الوصول إليها
"""

# استيراد النماذج من المودلات المختلفة
from .accounts import (
    DashboardLoginForm, UserForm, RoleForm, UserProfileForm, UserAddressForm
)
from .products import (
    ProductForm, CategoryForm, ProductVariantForm, ProductImageForm, ProductDiscountForm
)
from .orders import (
    OrderForm, OrderItemForm, OrderStatusUpdateForm
)
from .checkout import (
    PaymentMethodForm, ShippingMethodForm
)
from .payment import (
    PaymentRefundForm
)
from .dashboard import (
    DashboardWidgetForm, DashboardUserSettingsForm
)
from .core import (
    SiteSettingsForm
)

# يمكن استيراد كل النماذج من خلال استيراد حزمة forms
__all__ = [
    'DashboardLoginForm', 'UserForm', 'RoleForm', 'UserProfileForm', 'UserAddressForm','UserAddressForm',
    'ProductForm', 'CategoryForm', 'ProductVariantForm', 'ProductImageForm', 'ProductDiscountForm',
    'OrderForm', 'OrderItemForm', 'OrderStatusUpdateForm',
    'PaymentMethodForm', 'ShippingMethodForm',
    'PaymentRefundForm',
    'DashboardWidgetForm', 'DashboardUserSettingsForm',
    'SiteSettingsForm'
]