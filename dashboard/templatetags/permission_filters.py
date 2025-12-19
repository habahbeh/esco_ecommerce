from django import template

register = template.Library()


@register.filter
def translate_permission(permission_name):
    """ترجمة أسماء الصلاحيات إلى العربية"""
    translations = {
        # صلاحيات المنتج
        'Can add product': 'إضافة منتج جديد',
        'Can change product': 'تعديل بيانات المنتج',
        'Can delete product': 'حذف المنتج',
        'Can view product': 'عرض تفاصيل المنتج',

        # صلاحيات الفئات
        'Can add category': 'إضافة فئة جديدة',
        'Can change category': 'تعديل بيانات الفئة',
        'Can delete category': 'حذف الفئة',
        'Can view category': 'عرض تفاصيل الفئة',

        # صلاحيات العلامات التجارية
        'Can add brand': 'إضافة علامة تجارية جديدة',
        'Can change brand': 'تعديل بيانات العلامة التجارية',
        'Can delete brand': 'حذف العلامة التجارية',
        'Can view brand': 'عرض تفاصيل العلامة التجارية',

        # صلاحيات المستخدم
        'Can add user': 'إضافة مستخدم جديد',
        'Can change user': 'تعديل بيانات المستخدم',
        'Can delete user': 'حذف المستخدم',
        'Can view user': 'عرض تفاصيل المستخدم',

        # صلاحيات الأدوار
        'Can add role': 'إضافة دور جديد',
        'Can change role': 'تعديل بيانات الدور',
        'Can delete role': 'حذف الدور',
        'Can view role': 'عرض تفاصيل الدور',

        # صلاحيات الطلب
        'Can add order': 'إضافة طلب جديد',
        'Can change order': 'تعديل بيانات الطلب',
        'Can delete order': 'حذف الطلب',
        'Can view order': 'عرض تفاصيل الطلب',

        # صلاحيات عنصر الطلب
        'Can add order item': 'إضافة عنصر طلب جديد',
        'Can change order item': 'تعديل بيانات عنصر الطلب',
        'Can delete order item': 'حذف عنصر الطلب',
        'Can view order item': 'عرض تفاصيل عنصر الطلب',

        # صلاحيات طرق الدفع
        'Can add payment method': 'إضافة طريقة دفع جديدة',
        'Can change payment method': 'تعديل بيانات طريقة الدفع',
        'Can delete payment method': 'حذف طريقة الدفع',
        'Can view payment method': 'عرض تفاصيل طريقة الدفع',

        # صلاحيات إعدادات الموقع
        'Can add site settings': 'إضافة إعدادات الموقع',
        'Can change site settings': 'تعديل إعدادات الموقع',
        'Can delete site settings': 'حذف إعدادات الموقع',
        'Can view site settings': 'عرض إعدادات الموقع',

        # صلاحيات النشرة البريدية
        'Can add newsletter': 'إضافة اشتراك في النشرة البريدية',
        'Can change newsletter': 'تعديل اشتراك في النشرة البريدية',
        'Can delete newsletter': 'حذف اشتراك من النشرة البريدية',
        'Can view newsletter': 'عرض اشتراكات النشرة البريدية',

        # صلاحيات عناصر السلايدر
        'Can add slider item': 'إضافة عنصر سلايدر جديد',
        'Can change slider item': 'تعديل عنصر سلايدر',
        'Can delete slider item': 'حذف عنصر سلايدر',
        'Can view slider item': 'عرض عناصر السلايدر',

        # صلاحيات الفعاليات
        'Can add event': 'إضافة فعالية جديدة',
        'Can change event': 'تعديل بيانات الفعالية',
        'Can delete event': 'حذف الفعالية',
        'Can view event': 'عرض الفعاليات',

        # صلاحيات صور الفعاليات
        'Can add event image': 'إضافة صورة للفعالية',
        'Can change event image': 'تعديل صورة الفعالية',
        'Can delete event image': 'حذف صورة الفعالية',
        'Can view event image': 'عرض صور الفعاليات',
    }
    return translations.get(permission_name, permission_name)


@register.filter
def get_model_display_name(model_name):
    """الحصول على الاسم العربي للنموذج"""
    model_names = {
        'product': 'المنتج',
        'category': 'الفئة',
        'brand': 'العلامة التجارية',
        'user': 'المستخدم',
        'order': 'الطلب',
        'orderitem': 'عنصر الطلب',
        'paymentmethod': 'طريقة الدفع',
        'sitesettings': 'إعدادات النظام',
        'newsletter': 'النشرة البريدية',
        'slideritem': 'عنصر السلايدر',
        'event': 'الفعالية',
        'eventimage': 'صورة الفعالية',
    }
    return model_names.get(model_name, model_name.title())


@register.filter
def get_app_display_name(app_label):
    """الحصول على الاسم العربي للتطبيق"""
    app_names = {
        'products': 'المنتجات',
        'auth': 'المستخدمين',
        'orders': 'الطلبات',
        'checkout': 'المدفوعات',
        'core': 'الإعدادات',
        'events': 'الفعاليات',
    }
    return app_names.get(app_label, app_label.title())