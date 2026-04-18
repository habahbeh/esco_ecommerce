# dashboard/views/import_export.py
# ملف محسّن لوظائف الاستيراد والتصدير مع دعم المتغيرات

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils.text import slugify
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

import pandas as pd
import numpy as np
import uuid
import json
import os
import io
import xlsxwriter
from datetime import datetime
import threading
import time
from decimal import Decimal, ROUND_HALF_UP

from dashboard.forms.import_export import ProductImportForm
from products.models import Product, ProductVariant, Category, Brand, Tag
from django.db import transaction, connection


# ========================= دوال مساعدة =========================

def parse_attributes(attr_string):
    """
    تحويل الخصائص من الصيغة شبه المنظمة إلى قاموس JSON
    Semi-structured format: key:value|key:value
    Example: color:Black|storage:128GB -> {"color": "Black", "storage": "128GB"}
    """
    if not attr_string or pd.isna(attr_string):
        return {}

    attr_string = str(attr_string).strip()
    if not attr_string or attr_string == '-':
        return {}

    attributes = {}
    try:
        # تقسيم حسب الفاصل |
        pairs = attr_string.split('|')
        for pair in pairs:
            pair = pair.strip()
            if ':' in pair:
                key, value = pair.split(':', 1)
                key = key.strip()
                value = value.strip()
                if key and value:
                    attributes[key] = value
    except Exception:
        pass

    return attributes


def format_attributes(attributes):
    """
    تحويل الخصائص من JSON إلى نص شبه منظم
    Example: {"color": "Black", "storage": "128GB"} -> color:Black|storage:128GB
    """
    if not attributes or not isinstance(attributes, dict):
        return ''

    formatted_parts = []
    for key, value in attributes.items():
        if value:
            formatted_parts.append(f"{key}:{value}")
    return '|'.join(formatted_parts) if formatted_parts else ''


def round_decimal(value, decimal_places=2):
    """تقريب القيمة إلى عدد محدد من الخانات العشرية"""
    if value is None:
        return None

    try:
        decimal_value = Decimal(str(value))
        rounded_value = decimal_value.quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
        return rounded_value
    except Exception:
        return value


# ========================= توليد قالب الاستيراد =========================

def generate_import_template(request):
    """
    توليد قالب Excel محسّن للاستيراد مع دعم المتغيرات
    Enhanced Excel template with variant support
    """
    output = io.BytesIO()

    workbook = xlsxwriter.Workbook(output, {'in_memory': True})

    # ===== ورقة التعليمات =====
    instructions_sheet = workbook.add_worksheet('تعليمات')
    instructions_sheet.right_to_left()

    # تنسيقات
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'font_color': '#0077c8',
        'font_name': 'Arial',
    })
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'font_color': '#333',
        'font_name': 'Arial',
    })
    text_format = workbook.add_format({
        'font_size': 11,
        'font_name': 'Arial',
        'text_wrap': True,
    })
    code_format = workbook.add_format({
        'font_size': 10,
        'font_name': 'Consolas',
        'bg_color': '#f8f9fa',
        'border': 1,
    })

    # كتابة التعليمات
    instructions_sheet.set_column(0, 0, 80)
    row = 0

    instructions_sheet.write(row, 0, 'دليل استيراد المنتجات - ESCO', title_format)
    row += 2

    instructions_sheet.write(row, 0, '1. الأعمدة الإلزامية:', header_format)
    row += 1
    instructions_sheet.write(row, 0, '   • name: اسم المنتج (إلزامي)', text_format)
    row += 1
    instructions_sheet.write(row, 0, '   • base_price: السعر الأساسي (إلزامي)', text_format)
    row += 2

    instructions_sheet.write(row, 0, '2. صيغة الخصائص (attributes):', header_format)
    row += 1
    instructions_sheet.write(row, 0, '   استخدم الصيغة: key:value|key:value', text_format)
    row += 1
    instructions_sheet.write(row, 0, '   مثال: color:Black|storage:128GB|ram:8GB', code_format)
    row += 2

    instructions_sheet.write(row, 0, '3. ربط المتغيرات بالمنتجات:', header_format)
    row += 1
    instructions_sheet.write(row, 0, '   • لإضافة متغيرات لمنتج، استخدم نفس product_sku في صفوف مختلفة', text_format)
    row += 1
    instructions_sheet.write(row, 0, '   • كل صف يمثل متغير واحد للمنتج', text_format)
    row += 2

    instructions_sheet.write(row, 0, '4. أنواع الاستيراد:', header_format)
    row += 1
    instructions_sheet.write(row, 0, '   • استيراد كامل: منتجات + متغيرات', text_format)
    row += 1
    instructions_sheet.write(row, 0, '   • منتجات فقط: تجاهل أعمدة المتغيرات', text_format)
    row += 1
    instructions_sheet.write(row, 0, '   • متغيرات فقط: إضافة متغيرات لمنتجات موجودة', text_format)
    row += 1
    instructions_sheet.write(row, 0, '   • تحديث فقط: تحديث منتجات موجودة بدون إنشاء جديدة', text_format)

    # ===== ورقة البيانات =====
    data_sheet = workbook.add_worksheet('بيانات المنتجات')
    data_sheet.right_to_left()

    # تنسيق العناوين
    col_header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#0077c8',
        'font_color': 'white',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_name': 'Arial',
        'font_size': 10,
    })

    required_format = workbook.add_format({
        'bold': True,
        'bg_color': '#dc3545',
        'font_color': 'white',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_name': 'Arial',
        'font_size': 10,
    })

    cell_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_name': 'Arial',
        'font_size': 10,
    })

    example_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_name': 'Arial',
        'font_size': 10,
        'bg_color': '#f8f9fa',
    })

    attr_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_name': 'Consolas',
        'font_size': 9,
        'bg_color': '#fff3cd',
    })

    # تعريف الأعمدة
    columns = [
        # معلومات المنتج
        ('name', 'اسم المنتج *', 25, True),
        ('name_en', 'الاسم بالإنجليزية', 25, False),
        ('product_sku', 'SKU المنتج', 15, False),
        ('barcode', 'الباركود', 15, False),
        ('category', 'الفئة', 20, False),
        ('brand', 'العلامة التجارية', 20, False),
        ('base_price', 'السعر الأساسي *', 12, True),
        ('compare_price', 'سعر المقارنة', 12, False),
        ('cost', 'التكلفة', 12, False),
        ('description', 'الوصف', 40, False),
        # معلومات المتغير
        ('variant_name', 'اسم المتغير', 20, False),
        ('variant_sku', 'SKU المتغير', 15, False),
        ('attributes', 'الخصائص', 35, False),
        ('variant_price', 'سعر المتغير', 12, False),
        ('variant_stock', 'مخزون المتغير', 12, False),
        # إعدادات
        ('stock_quantity', 'المخزون الكلي', 12, False),
        ('status', 'الحالة', 12, False),
        ('is_active', 'نشط', 8, False),
    ]

    # كتابة العناوين
    for col, (key, label, width, required) in enumerate(columns):
        fmt = required_format if required else col_header_format
        data_sheet.write(0, col, label, fmt)
        data_sheet.set_column(col, col, width)

    # صف توضيحي للأعمدة الإنجليزية
    desc_format = workbook.add_format({
        'font_size': 8,
        'font_color': '#666',
        'italic': True,
        'border': 1,
        'bg_color': '#e9ecef',
    })
    for col, (key, label, width, required) in enumerate(columns):
        data_sheet.write(1, col, key, desc_format)

    # بيانات المثال
    example_data = [
        # منتج 1 مع متغيرات
        {
            'name': 'هاتف iPhone 15 Pro',
            'name_en': 'iPhone 15 Pro',
            'product_sku': 'IPHONE15PRO',
            'barcode': '1234567890123',
            'category': 'الهواتف الذكية',
            'brand': 'Apple',
            'base_price': '999.00',
            'compare_price': '1099.00',
            'cost': '850.00',
            'description': 'هاتف ذكي من Apple بمعالج A17 Pro',
            'variant_name': '128GB أسود',
            'variant_sku': 'IPHONE15PRO-128-BLK',
            'attributes': 'color:Black|storage:128GB',
            'variant_price': '999.00',
            'variant_stock': '50',
            'stock_quantity': '100',
            'status': 'published',
            'is_active': 'Yes',
        },
        {
            'name': 'هاتف iPhone 15 Pro',
            'name_en': 'iPhone 15 Pro',
            'product_sku': 'IPHONE15PRO',
            'barcode': '',
            'category': '',
            'brand': '',
            'base_price': '',
            'compare_price': '',
            'cost': '',
            'description': '',
            'variant_name': '256GB أبيض',
            'variant_sku': 'IPHONE15PRO-256-WHT',
            'attributes': 'color:White|storage:256GB',
            'variant_price': '1099.00',
            'variant_stock': '30',
            'stock_quantity': '',
            'status': '',
            'is_active': '',
        },
        # منتج 2 بدون متغيرات
        {
            'name': 'سماعة AirPods Pro',
            'name_en': 'AirPods Pro',
            'product_sku': 'AIRPODS-PRO',
            'barcode': '9876543210987',
            'category': 'الإكسسوارات',
            'brand': 'Apple',
            'base_price': '249.00',
            'compare_price': '299.00',
            'cost': '180.00',
            'description': 'سماعات لاسلكية مع إلغاء الضوضاء',
            'variant_name': '',
            'variant_sku': '',
            'attributes': '',
            'variant_price': '',
            'variant_stock': '',
            'stock_quantity': '200',
            'status': 'published',
            'is_active': 'Yes',
        },
        # منتج 3 - تيشيرت مع مقاسات
        {
            'name': 'تيشيرت قطني',
            'name_en': 'Cotton T-Shirt',
            'product_sku': 'TSHIRT-COTTON',
            'barcode': '',
            'category': 'الملابس',
            'brand': 'Fashion Brand',
            'base_price': '25.00',
            'compare_price': '35.00',
            'cost': '12.00',
            'description': 'تيشيرت قطني 100% بجودة عالية',
            'variant_name': 'Large أحمر',
            'variant_sku': 'TSHIRT-L-RED',
            'attributes': 'color:Red|size:L',
            'variant_price': '25.00',
            'variant_stock': '100',
            'stock_quantity': '500',
            'status': 'published',
            'is_active': 'Yes',
        },
        {
            'name': 'تيشيرت قطني',
            'name_en': '',
            'product_sku': 'TSHIRT-COTTON',
            'barcode': '',
            'category': '',
            'brand': '',
            'base_price': '',
            'compare_price': '',
            'cost': '',
            'description': '',
            'variant_name': 'Medium أزرق',
            'variant_sku': 'TSHIRT-M-BLUE',
            'attributes': 'color:Blue|size:M',
            'variant_price': '25.00',
            'variant_stock': '80',
            'stock_quantity': '',
            'status': '',
            'is_active': '',
        },
    ]

    # كتابة بيانات المثال
    for row_idx, row_data in enumerate(example_data, start=2):
        for col, (key, label, width, required) in enumerate(columns):
            value = row_data.get(key, '')
            if key == 'attributes' and value:
                data_sheet.write(row_idx, col, value, attr_format)
            else:
                data_sheet.write(row_idx, col, value, example_format)

    # تجميد الصفوف العليا
    data_sheet.freeze_panes(2, 0)

    workbook.close()
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="product_import_template.xlsx"'

    return response


def generate_csv_template(request):
    """
    توليد قالب CSV للاستيراد (للتوافق مع الإصدار القديم)
    """
    return generate_import_template(request)


# ========================= مدير الاستيراد =========================

class ImportManager:
    """
    مدير عمليات استيراد المنتجات المحسّن مع دعم المتغيرات
    """

    def __init__(self, import_id=None):
        """تهيئة مدير الاستيراد"""
        self.import_id = import_id or uuid.uuid4().hex
        self.progress_data = {
            'total': 0,
            'processed': 0,
            'success': 0,
            'updated': 0,
            'errors': 0,
            'variants_created': 0,
            'variants_updated': 0,
            'status': 'pending',
            'error_details': []
        }
        self.import_data = {}

    def save_file(self, file_obj):
        """حفظ الملف المرفوع"""
        temp_dir = os.path.join('media', 'temp', 'imports')
        os.makedirs(temp_dir, exist_ok=True)

        file_path = os.path.join(temp_dir, f"{self.import_id}_{file_obj.name}")

        with open(file_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        self.import_data['file_path'] = file_path
        return file_path

    def read_file(self, file_path=None):
        """قراءة ملف البيانات (يدعم Excel وCSV)"""
        if file_path is None:
            file_path = self.import_data.get('file_path')

        if not file_path or not os.path.exists(file_path):
            raise ValueError("الملف غير موجود")

        try:
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            elif file_ext == '.xls':
                df = pd.read_excel(file_path, engine='xlrd')
            elif file_ext == '.xlsx':
                # محاولة قراءة ورقة البيانات المحددة، أو الورقة الأولى
                try:
                    df = pd.read_excel(file_path, engine='openpyxl', sheet_name='بيانات المنتجات')
                except ValueError:
                    # إذا لم تكن الورقة موجودة، قراءة الورقة الأولى
                    df = pd.read_excel(file_path, engine='openpyxl', sheet_name=0)
            else:
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except:
                    df = pd.read_excel(file_path)

            # معالجة القيم المفقودة
            df = df.fillna("")

            # إزالة صف أسماء الأعمدة الإنجليزية إذا كان موجوداً
            if len(df) > 0 and df.iloc[0].astype(str).str.match(r'^[a-z_]+$').all():
                df = df.iloc[1:].reset_index(drop=True)

            # إزالة الصفوف الفارغة
            df = df[~df.astype(str).apply(lambda x: x.str.strip().eq('').all(), axis=1)]

            # تحديث الإحصائيات
            self.progress_data['total'] = len(df)
            self.import_data['df'] = df

            return df
        except Exception as e:
            raise ValueError(f"خطأ في قراءة الملف: {str(e)}")

    def save_progress(self):
        """حفظ بيانات التقدم في ملف"""
        temp_dir = os.path.join('media', 'temp', 'imports')
        os.makedirs(temp_dir, exist_ok=True)

        file_path = os.path.join(temp_dir, f'progress_{self.import_id}.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.progress_data, f, ensure_ascii=False)

    def save_import_data(self):
        """حفظ بيانات الاستيراد في ملف"""
        if 'df' in self.import_data:
            df = self.import_data['df']
            records = []
            for _, row in df.iterrows():
                record = {}
                for col in df.columns:
                    val = row[col]
                    if pd.isna(val):
                        record[col] = ""
                    else:
                        record[col] = str(val)
                records.append(record)
            self.import_data['records'] = records
            del self.import_data['df']

        temp_dir = os.path.join('media', 'temp', 'imports')
        os.makedirs(temp_dir, exist_ok=True)

        file_path = os.path.join(temp_dir, f'data_{self.import_id}.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.import_data, f, default=str, ensure_ascii=False)

    def load_progress(self):
        """تحميل بيانات التقدم من ملف"""
        temp_dir = os.path.join('media', 'temp', 'imports')
        file_path = os.path.join(temp_dir, f'progress_{self.import_id}.json')

        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.progress_data = json.load(f)
                return self.progress_data
        except Exception:
            return None

    def load_import_data(self):
        """تحميل بيانات الاستيراد من ملف"""
        temp_dir = os.path.join('media', 'temp', 'imports')
        file_path = os.path.join(temp_dir, f'data_{self.import_id}.json')

        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.import_data = json.load(f)
                return self.import_data
        except Exception:
            return None

    def export_errors(self):
        """تصدير الأخطاء إلى ملف Excel"""
        if not self.progress_data.get('error_details'):
            return None

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('أخطاء الاستيراد')
        worksheet.right_to_left()

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#dc3545',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })

        error_format = workbook.add_format({
            'bg_color': '#fce4ec',
            'border': 1,
            'text_wrap': True,
        })

        # كتابة العناوين
        headers = ['رقم الصف', 'الاسم', 'SKU', 'رسالة الخطأ', 'البيانات الأصلية']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        # كتابة بيانات الأخطاء
        for row, error in enumerate(self.progress_data['error_details'], start=1):
            worksheet.write(row, 0, error.get('row', ''), error_format)
            worksheet.write(row, 1, error.get('name', ''), error_format)
            worksheet.write(row, 2, error.get('sku', ''), error_format)
            worksheet.write(row, 3, error.get('error', ''), error_format)

            if 'data' in error:
                worksheet.write(row, 4, json.dumps(error['data'], ensure_ascii=False), error_format)

        worksheet.set_column(0, 0, 10)
        worksheet.set_column(1, 2, 20)
        worksheet.set_column(3, 3, 50)
        worksheet.set_column(4, 4, 60)

        workbook.close()
        output.seek(0)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return {
            'data': output.getvalue(),
            'filename': f"import_errors_{timestamp}.xlsx"
        }


# ========================= عرض الاستيراد =========================

@login_required
def product_import_view(request):
    """
    عرض صفحة استيراد المنتجات المحسّنة
    """
    if request.method == 'POST':
        # التحقق من طلب AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        form = ProductImportForm(request.POST, request.FILES)

        if not form.is_valid():
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': str(form.errors)
                })
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form[field].label}: {error}")
            return redirect('dashboard:product_import')

        try:
            uploaded_file = request.FILES['file']
            import_mode = form.cleaned_data.get('import_mode', 'full')
            update_existing = form.cleaned_data.get('update_existing', True)
            skip_errors = form.cleaned_data.get('skip_errors', True)
            create_categories = form.cleaned_data.get('create_categories', True)
            create_brands = form.cleaned_data.get('create_brands', True)

            # الفلاتر
            filter_category = form.cleaned_data.get('filter_by_category')
            filter_brand = form.cleaned_data.get('filter_by_brand')
            default_category = form.cleaned_data.get('category')
            default_brand = form.cleaned_data.get('brand')

            # إنشاء مدير الاستيراد
            import_manager = ImportManager()
            import_manager.save_file(uploaded_file)

            # قراءة الملف
            try:
                df = import_manager.read_file()
            except Exception as e:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': str(e)})
                messages.error(request, str(e))
                return redirect('dashboard:product_import')

            # حفظ الإعدادات
            import_manager.import_data['import_mode'] = import_mode
            import_manager.import_data['update_existing'] = update_existing
            import_manager.import_data['skip_errors'] = skip_errors
            import_manager.import_data['create_categories'] = create_categories
            import_manager.import_data['create_brands'] = create_brands
            import_manager.import_data['filter_category_id'] = filter_category.id if filter_category else None
            import_manager.import_data['filter_brand_id'] = filter_brand.id if filter_brand else None
            import_manager.import_data['default_category_id'] = default_category.id if default_category else None
            import_manager.import_data['default_brand_id'] = default_brand.id if default_brand else None

            import_manager.save_import_data()
            import_manager.progress_data['status'] = 'processing'
            import_manager.save_progress()

            # بدء عملية الاستيراد في الخلفية
            threading.Thread(
                target=process_import_with_variants,
                args=(import_manager.import_id, request.user.id),
                daemon=True
            ).start()

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'import_id': import_manager.import_id,
                    'total': len(df)
                })

            messages.success(request, _('تم بدء استيراد %s صف. يرجى الانتظار حتى اكتمال العملية.') % len(df))
            return redirect('dashboard:import_results', import_id=import_manager.import_id)

        except Exception as e:
            if is_ajax:
                return JsonResponse({'success': False, 'error': str(e)})
            messages.error(request, _('حدث خطأ: %s') % str(e))
            return redirect('dashboard:product_import')

    # عرض النموذج
    form = ProductImportForm()
    categories = Category.objects.filter(is_active=True).order_by('tree_id', 'lft')
    brands = Brand.objects.filter(is_active=True).order_by('name')

    context = {
        'form': form,
        'categories': categories,
        'brands': brands,
        'form_title': _('استيراد المنتجات'),
    }

    return render(request, 'dashboard/products/product_import.html', context)


@login_required
def product_import_preview(request):
    """
    معاينة بيانات الاستيراد قبل التنفيذ
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': _('طريقة غير صحيحة')})

    try:
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return JsonResponse({'success': False, 'error': _('لم يتم اختيار ملف')})

        import_mode = request.POST.get('import_mode', 'full')

        # إنشاء مدير الاستيراد المؤقت
        import_manager = ImportManager()
        import_manager.save_file(uploaded_file)

        # قراءة الملف
        df = import_manager.read_file()

        # تحليل البيانات
        products_count = 0
        variants_count = 0
        errors_count = 0
        rows = []

        # تجميع المنتجات والمتغيرات
        seen_products = set()

        for index, row in df.iterrows():
            # تحويل البيانات إلى قاموس مع معالجة NaN
            row_data = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val) or val is None:
                    row_data[col] = ''
                else:
                    row_data[col] = str(val)

            # تحديد المنتج
            product_sku = row_data.get('product_sku', '') or row_data.get('sku', '')
            product_sku = product_sku.strip() if product_sku else ''
            product_name = row_data.get('name', '').strip()

            # التحقق من وجود اسم المنتج
            has_error = False
            if not product_name and not product_sku:
                has_error = True
                errors_count += 1

            # حساب المنتجات الفريدة
            product_key = product_sku or product_name
            if product_key and product_key not in seen_products:
                products_count += 1
                seen_products.add(product_key)

            # حساب المتغيرات
            variant_name = row_data.get('variant_name', '').strip()
            if variant_name and import_mode in ['full', 'variants_only']:
                variants_count += 1

            # إضافة للمعاينة (أول 100 صف فقط)
            if index < 100:
                row_data['has_error'] = has_error
                rows.append(row_data)

        return JsonResponse({
            'success': True,
            'products_count': products_count,
            'variants_count': variants_count,
            'errors_count': errors_count,
            'total_rows': len(df),
            'columns': list(df.columns),
            'rows': rows
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def import_results_view(request, import_id):
    """
    عرض نتائج الاستيراد
    """
    import_manager = ImportManager(import_id)
    progress_data = import_manager.load_progress()
    import_data = import_manager.load_import_data()

    if not progress_data or not import_data:
        messages.error(request, _('انتهت صلاحية بيانات الاستيراد أو أن معرف الاستيراد غير صحيح'))
        return redirect('dashboard:product_import')

    context = {
        'import_id': import_id,
        'progress': progress_data,
        'total_rows': progress_data.get('total', 0),
        'is_completed': progress_data.get('status') == 'completed',
        'has_errors': progress_data.get('errors', 0) > 0,
        'error_details': progress_data.get('error_details', [])[:50],
        'error_count': len(progress_data.get('error_details', [])),
    }

    return render(request, 'dashboard/products/import_results.html', context)


@login_required
def import_progress_view(request):
    """
    الحصول على تقدم الاستيراد عبر AJAX
    """
    import_id = request.GET.get('import_id')

    if not import_id:
        return JsonResponse({'success': False, 'error': _('معرف الاستيراد مفقود')})

    import_manager = ImportManager(import_id)
    progress_data = import_manager.load_progress()

    if not progress_data:
        return JsonResponse({'success': False, 'error': _('بيانات الاستيراد غير موجودة')})

    return JsonResponse({
        'success': True,
        'progress': progress_data
    })


@login_required
def export_errors_view(request):
    """
    تصدير المنتجات التي فشل استيرادها
    """
    import_id = request.GET.get('import_id')
    export_format = request.GET.get('format', 'excel')

    if not import_id:
        messages.error(request, _('معرف الاستيراد مفقود'))
        return redirect('dashboard:product_import')

    import_manager = ImportManager(import_id)
    progress_data = import_manager.load_progress()

    if not progress_data:
        messages.error(request, _('بيانات الاستيراد غير موجودة'))
        return redirect('dashboard:product_import')

    if not progress_data.get('error_details'):
        messages.warning(request, _('لا توجد أخطاء للتصدير'))
        return redirect('dashboard:import_results', import_id=import_id)

    export_data = import_manager.export_errors()

    if not export_data:
        messages.error(request, _('فشل في تصدير الأخطاء'))
        return redirect('dashboard:import_results', import_id=import_id)

    response = HttpResponse(
        export_data['data'],
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={export_data["filename"]}'

    return response


# ========================= معالجة الاستيراد مع المتغيرات =========================

def process_import_with_variants(import_id, user_id):
    """
    معالجة الاستيراد مع دعم المتغيرات
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    import_manager = ImportManager(import_id)

    try:
        user = User.objects.get(id=user_id)

        import_manager.load_progress()
        import_data = import_manager.load_import_data()

        if not import_data:
            import_manager.progress_data['status'] = 'error'
            import_manager.progress_data['error_message'] = "بيانات الاستيراد غير موجودة"
            import_manager.save_progress()
            return

        # استرجاع الإعدادات
        import_mode = import_data.get('import_mode', 'full')
        update_existing = import_data.get('update_existing', True)
        skip_errors = import_data.get('skip_errors', True)
        create_categories = import_data.get('create_categories', True)
        create_brands = import_data.get('create_brands', True)
        filter_category_id = import_data.get('filter_category_id')
        filter_brand_id = import_data.get('filter_brand_id')
        default_category_id = import_data.get('default_category_id')
        default_brand_id = import_data.get('default_brand_id')
        file_path = import_data.get('file_path')

        # تحميل الفلاتر والافتراضيات
        filter_category = Category.objects.get(id=filter_category_id) if filter_category_id else None
        filter_brand = Brand.objects.get(id=filter_brand_id) if filter_brand_id else None
        default_category = Category.objects.get(id=default_category_id) if default_category_id else None
        default_brand = Brand.objects.get(id=default_brand_id) if default_brand_id else None

        # قراءة البيانات
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.csv':
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        elif file_ext == '.xlsx':
            try:
                df = pd.read_excel(file_path, engine='openpyxl', sheet_name='بيانات المنتجات')
            except:
                df = pd.read_excel(file_path, engine='openpyxl')
        else:
            df = pd.read_excel(file_path)

        df = df.fillna("")

        # إزالة صف أسماء الأعمدة الإنجليزية
        if len(df) > 0:
            first_row = df.iloc[0].astype(str)
            if first_row.str.match(r'^[a-z_]+$').all():
                df = df.iloc[1:].reset_index(drop=True)

        df = df[~df.astype(str).apply(lambda x: x.str.strip().eq('').all(), axis=1)]

        import_manager.progress_data['total'] = len(df)
        import_manager.progress_data['status'] = 'processing'
        import_manager.save_progress()

        # تجميع الصفوف حسب المنتج
        products_map = {}  # product_sku -> list of rows

        for index, row in df.iterrows():
            row_data = {col: ('' if pd.isna(row[col]) else row[col]) for col in df.columns}

            product_sku = str(row_data.get('product_sku', '') or row_data.get('sku', '')).strip()
            product_name = str(row_data.get('name', '')).strip()

            # إنشاء مفتاح فريد للمنتج
            product_key = product_sku or product_name

            if not product_key:
                import_manager.progress_data['errors'] += 1
                import_manager.progress_data['error_details'].append({
                    'row': index + 2,
                    'name': '',
                    'sku': '',
                    'error': 'اسم المنتج أو SKU مطلوب',
                    'data': row_data
                })
                import_manager.progress_data['processed'] += 1
                continue

            if product_key not in products_map:
                products_map[product_key] = {
                    'main_row': row_data,
                    'row_index': index + 2,
                    'variants': []
                }
            else:
                # هذا صف متغير
                products_map[product_key]['variants'].append({
                    'row_data': row_data,
                    'row_index': index + 2
                })

        # معالجة كل منتج
        for product_key, product_info in products_map.items():
            time.sleep(0.01)  # تجنب استهلاك CPU

            main_row = product_info['main_row']
            row_index = product_info['row_index']
            variant_rows = product_info['variants']

            try:
                with transaction.atomic():
                    # استخراج بيانات المنتج
                    name = str(main_row.get('name', '')).strip()
                    name_en = str(main_row.get('name_en', '')).strip() or name
                    product_sku = str(main_row.get('product_sku', '') or main_row.get('sku', '')).strip()
                    barcode = str(main_row.get('barcode', '')).strip()
                    base_price_str = str(main_row.get('base_price', '')).strip()
                    compare_price_str = str(main_row.get('compare_price', '')).strip()
                    cost_str = str(main_row.get('cost', '')).strip()
                    description = str(main_row.get('description', '')).strip()
                    stock_str = str(main_row.get('stock_quantity', '')).strip()
                    status = str(main_row.get('status', 'published')).strip() or 'published'
                    is_active_str = str(main_row.get('is_active', 'Yes')).strip()

                    # التحقق من البيانات الإلزامية
                    if not name:
                        raise ValueError("اسم المنتج مطلوب")

                    if not base_price_str and import_mode != 'variants_only':
                        raise ValueError("السعر الأساسي مطلوب")

                    # تحويل السعر
                    base_price = None
                    if base_price_str:
                        try:
                            base_price = round_decimal(float(base_price_str.replace(',', '.')))
                        except:
                            raise ValueError("قيمة السعر الأساسي غير صالحة")

                    compare_price = None
                    if compare_price_str:
                        try:
                            compare_price = round_decimal(float(compare_price_str.replace(',', '.')))
                        except:
                            pass

                    cost = None
                    if cost_str:
                        try:
                            cost = round_decimal(float(cost_str.replace(',', '.')))
                        except:
                            pass

                    stock_quantity = 0
                    if stock_str:
                        try:
                            stock_quantity = int(float(stock_str))
                        except:
                            pass

                    is_active = is_active_str.lower() in ['yes', 'true', '1', 'نعم']

                    # معالجة الفئة
                    category = filter_category or default_category
                    category_name = str(main_row.get('category', '')).strip()
                    if category_name and not filter_category:
                        try:
                            category = Category.objects.get(name=category_name)
                        except Category.DoesNotExist:
                            try:
                                category = Category.objects.get(name_en=category_name)
                            except Category.DoesNotExist:
                                if create_categories:
                                    cat_slug = slugify(category_name, allow_unicode=True) or f"cat-{uuid.uuid4().hex[:8]}"
                                    if Category.objects.filter(slug=cat_slug).exists():
                                        cat_slug = f"{cat_slug}-{uuid.uuid4().hex[:6]}"
                                    category = Category.objects.create(
                                        name=category_name,
                                        slug=cat_slug,
                                        is_active=True,
                                        created_by=user
                                    )

                    # معالجة العلامة التجارية
                    brand = filter_brand or default_brand
                    brand_name = str(main_row.get('brand', '')).strip()
                    if brand_name and not filter_brand:
                        try:
                            brand = Brand.objects.get(name=brand_name)
                        except Brand.DoesNotExist:
                            try:
                                brand = Brand.objects.get(name_en=brand_name)
                            except Brand.DoesNotExist:
                                if create_brands:
                                    brand_slug = slugify(brand_name, allow_unicode=True) or f"brand-{uuid.uuid4().hex[:8]}"
                                    if Brand.objects.filter(slug=brand_slug).exists():
                                        brand_slug = f"{brand_slug}-{uuid.uuid4().hex[:6]}"
                                    brand = Brand.objects.create(
                                        name=brand_name,
                                        slug=brand_slug,
                                        is_active=True,
                                        created_by=user
                                    )

                    # البحث عن منتج موجود
                    existing_product = None
                    if update_existing or import_mode in ['update', 'variants_only']:
                        if product_sku:
                            existing_product = Product.objects.filter(sku=product_sku).first()
                        if not existing_product and name:
                            existing_product = Product.objects.filter(name=name, category=category).first()

                    # إنشاء أو تحديث المنتج
                    if import_mode == 'variants_only':
                        if not existing_product:
                            raise ValueError("المنتج غير موجود - يجب أن يكون موجوداً لإضافة متغيرات")
                        product = existing_product
                    elif existing_product and update_existing:
                        # تحديث المنتج
                        existing_product.name = name
                        existing_product.name_en = name_en
                        if description:
                            existing_product.description = description
                        if base_price:
                            existing_product.base_price = base_price
                        if compare_price:
                            existing_product.compare_price = compare_price
                        if cost:
                            existing_product.cost = cost
                        if barcode:
                            existing_product.barcode = barcode
                        if category:
                            existing_product.category = category
                        if brand:
                            existing_product.brand = brand
                        existing_product.stock_quantity = stock_quantity
                        existing_product.status = status
                        existing_product.is_active = is_active
                        existing_product.save()

                        product = existing_product
                        import_manager.progress_data['updated'] += 1
                    elif import_mode != 'update':
                        # إنشاء منتج جديد
                        sku = product_sku or f"SKU-{uuid.uuid4().hex[:8].upper()}"

                        slug_base = slugify(name_en or name, allow_unicode=True)
                        if not slug_base:
                            slug_base = f"product-{uuid.uuid4().hex[:8]}"
                        slug = slug_base
                        counter = 1
                        while Product.objects.filter(slug=slug).exists():
                            slug = f"{slug_base}-{counter}"
                            counter += 1

                        if not description or len(description) < 20:
                            description = f"وصف تلقائي للمنتج: {name}. هذا وصف تم إنشاؤه تلقائياً."

                        product = Product.objects.create(
                            name=name,
                            name_en=name_en,
                            slug=slug,
                            sku=sku,
                            description=description,
                            base_price=base_price or Decimal('0'),
                            compare_price=compare_price,
                            cost=cost,
                            barcode=barcode,
                            category=category,
                            brand=brand,
                            status=status,
                            is_active=is_active,
                            stock_quantity=stock_quantity,
                            stock_status='in_stock' if stock_quantity > 0 else 'out_of_stock',
                            created_by=user
                        )

                        import_manager.progress_data['success'] += 1
                    else:
                        # وضع التحديث فقط ولم يتم العثور على المنتج
                        raise ValueError("المنتج غير موجود - وضع التحديث فقط")

                    # معالجة المتغيرات
                    if import_mode in ['full', 'variants_only', 'update']:
                        # في وضع التحديث فقط، لا نُنشئ متغيرات جديدة
                        update_only_variants = (import_mode == 'update')

                        # المتغير من الصف الرئيسي
                        main_variant_name = str(main_row.get('variant_name', '')).strip()
                        main_variant_sku = str(main_row.get('variant_sku', '')).strip()
                        # في وضع التحديث، يمكن استخدام variant_sku للعثور على المتغير حتى بدون اسم
                        if main_variant_name or main_variant_sku:
                            process_variant(
                                product=product,
                                row_data=main_row,
                                import_manager=import_manager,
                                row_index=row_index,
                                update_only=update_only_variants
                            )

                        # المتغيرات الإضافية
                        for variant_info in variant_rows:
                            process_variant(
                                product=product,
                                row_data=variant_info['row_data'],
                                import_manager=import_manager,
                                row_index=variant_info['row_index'],
                                update_only=update_only_variants
                            )

                        # إعادة حفظ المنتج لتحديث حالة المخزون بناءً على المتغيرات
                        product.save()

            except Exception as e:
                if not skip_errors:
                    raise

                import_manager.progress_data['errors'] += 1
                import_manager.progress_data['error_details'].append({
                    'row': row_index,
                    'name': str(main_row.get('name', '')),
                    'sku': str(main_row.get('product_sku', '') or main_row.get('sku', '')),
                    'error': str(e),
                    'data': main_row
                })

            import_manager.progress_data['processed'] += 1 + len(variant_rows)

            # حفظ التقدم
            if import_manager.progress_data['processed'] % 5 == 0:
                import_manager.save_progress()

        import_manager.progress_data['status'] = 'completed'
        import_manager.save_progress()

    except Exception as e:
        import_manager = ImportManager(import_id)
        import_manager.load_progress()
        import_manager.progress_data['status'] = 'error'
        import_manager.progress_data['error_message'] = str(e)
        import_manager.save_progress()
        print(f"خطأ عام في عملية الاستيراد: {str(e)}")


def process_variant(product, row_data, import_manager, row_index, update_only=False):
    """
    معالجة متغير واحد
    update_only: إذا كان True، يتم التحديث فقط بدون إنشاء متغيرات جديدة
    """
    variant_name = str(row_data.get('variant_name', '')).strip()
    variant_sku = str(row_data.get('variant_sku', '')).strip()

    # يجب أن يكون هناك اسم أو SKU للمتغير
    if not variant_name and not variant_sku:
        return

    attributes_str = str(row_data.get('attributes', '')).strip()
    variant_price_str = str(row_data.get('variant_price', '')).strip()
    variant_stock_str = str(row_data.get('variant_stock', '')).strip()

    # تحويل الخصائص
    attributes = parse_attributes(attributes_str)

    # تحويل السعر
    variant_price = None
    if variant_price_str:
        try:
            variant_price = round_decimal(float(variant_price_str.replace(',', '.')))
        except:
            pass

    # تحويل المخزون
    variant_stock = None
    if variant_stock_str:
        try:
            variant_stock = int(float(variant_stock_str))
        except:
            pass

    # البحث عن متغير موجود - بالـ SKU أولاً ثم بالاسم
    existing_variant = None
    if variant_sku:
        existing_variant = ProductVariant.objects.filter(sku=variant_sku).first()

    if not existing_variant and variant_name:
        existing_variant = ProductVariant.objects.filter(
            product=product,
            name=variant_name
        ).first()

    if existing_variant:
        # تحديث المتغير
        if variant_name:
            existing_variant.name = variant_name
        if attributes:
            existing_variant.attributes = attributes
        if variant_price is not None:
            existing_variant.base_price = variant_price
        if variant_stock is not None:
            existing_variant.stock_quantity = variant_stock
        existing_variant.save()
        import_manager.progress_data['variants_updated'] += 1
    elif not update_only:
        # إنشاء متغير جديد (فقط إذا لم نكن في وضع التحديث فقط)
        if not variant_name:
            return  # لا يمكن إنشاء متغير بدون اسم

        # إنشاء SKU إذا لم يكن موجوداً
        if not variant_sku:
            variant_sku = f"{product.sku}-{uuid.uuid4().hex[:6].upper()}"

        ProductVariant.objects.create(
            product=product,
            name=variant_name,
            sku=variant_sku,
            attributes=attributes,
            base_price=variant_price or product.base_price,
            stock_quantity=variant_stock or 0,
            is_active=True
        )
        import_manager.progress_data['variants_created'] += 1


# ========================= تصدير المنتجات =========================

EXPORT_BATCH_SIZE = 500
EXCEL_CHUNK_SIZE = 1000
PDF_PRINT_MAX_RECORDS = 5000


def _get_export_columns(include_variants=True, include_images=False):
    """إرجاع أعمدة التصدير"""
    from collections import OrderedDict

    columns_list = [
        ('product_id', 'معرف المنتج'),
        ('product_sku', 'SKU المنتج'),
        ('barcode', 'الباركود'),
        ('product_name', 'اسم المنتج'),
        ('product_name_en', 'الاسم بالإنجليزية'),
        ('category', 'الفئة'),
        ('brand', 'العلامة التجارية'),
    ]

    if include_variants:
        columns_list.extend([
            ('variant_id', 'معرف المتغير'),
            ('variant_name', 'اسم المتغير'),
            ('variant_sku', 'SKU المتغير'),
            ('variant_attributes', 'الخصائص'),
            ('variant_price', 'السعر (د.أ)'),
            ('variant_stock', 'المخزون'),
        ])
    else:
        columns_list.extend([
            ('base_price', 'السعر (د.أ)'),
            ('stock_quantity', 'المخزون'),
        ])

    columns_list.extend([
        ('product_status', 'الحالة'),
        ('variant_active', 'نشط'),
        ('created_at', 'تاريخ الإنشاء'),
    ])

    if include_images:
        columns_list.append(('image_url', 'رابط الصورة'))

    return OrderedDict(columns_list)


def _build_export_queryset(request, include_images=False):
    """بناء استعلام التصدير مع التصفية"""
    from products.models import Product, ProductVariant, ProductImage
    from django.db.models import Q, Prefetch

    category_filter = request.GET.get('category', '')
    brand_filter = request.GET.get('brand', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')
    export_scope = request.GET.get('scope', 'all')
    selected_ids = request.GET.get('selected', '')

    prefetch_list = [
        Prefetch(
            'variants',
            queryset=ProductVariant.objects.filter(is_active=True)
                .only('id', 'name', 'sku', 'base_price', 'stock_quantity', 'is_active', 'sort_order', 'product_id', 'attributes')
                .order_by('sort_order')
        )
    ]

    if include_images:
        prefetch_list.append(
            Prefetch(
                'images',
                queryset=ProductImage.objects.all()
                    .only('id', 'image', 'product_id', 'is_primary')
                    .order_by('-is_primary', 'sort_order')
            )
        )

    queryset = Product.objects.select_related('category', 'brand').prefetch_related(
        *prefetch_list
    ).only(
        'id', 'name', 'name_en', 'sku', 'barcode', 'base_price', 'stock_quantity',
        'status', 'is_active', 'created_at', 'category_id', 'brand_id'
    )

    if export_scope == 'selected' and selected_ids:
        ids_list = [int(id.strip()) for id in selected_ids.split(',') if id.strip().isdigit()]
        if ids_list:
            queryset = queryset.filter(id__in=ids_list)
    elif export_scope == 'category_only' and category_filter:
        queryset = queryset.filter(category_id=category_filter)
    elif export_scope == 'brand_only' and brand_filter:
        queryset = queryset.filter(brand_id=brand_filter)
    else:
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(name_en__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(barcode__icontains=search_query)
            )
        if category_filter:
            try:
                category = Category.objects.get(id=category_filter)
                subcategories = category.get_all_children(include_self=True)
                queryset = queryset.filter(category__in=subcategories)
            except Category.DoesNotExist:
                pass
        if brand_filter:
            queryset = queryset.filter(brand_id=brand_filter)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

    return queryset.order_by('-created_at')


def _generate_export_data_iterator(queryset, include_variants=True, include_images=False, base_url=''):
    """مولد لبيانات التصدير"""
    from django.core.paginator import Paginator

    status_display = dict(Product.STATUS_CHOICES)
    paginator = Paginator(queryset, EXPORT_BATCH_SIZE)

    def get_product_image_url(product):
        if include_images and hasattr(product, 'images'):
            images = list(product.images.all())
            if images:
                return base_url + images[0].image.url if images[0].image else ''
        return ''

    for page_num in range(1, paginator.num_pages + 1):
        page = paginator.page(page_num)

        for product in page.object_list:
            image_url = get_product_image_url(product) if include_images else ''

            if include_variants:
                variants = list(product.variants.all())

                if variants:
                    for variant in variants:
                        row_data = {
                            'product_id': str(product.id),
                            'product_sku': product.sku or '',
                            'barcode': product.barcode or '',
                            'product_name': product.name,
                            'product_name_en': product.name_en or '',
                            'category': product.category.name if product.category else '',
                            'brand': product.brand.name if product.brand else '',
                            'variant_id': str(variant.id),
                            'variant_name': variant.name,
                            'variant_sku': variant.sku or '',
                            'variant_attributes': format_attributes(variant.attributes),
                            'variant_price': str(variant.base_price) if variant.base_price else str(product.base_price),
                            'variant_stock': variant.stock_quantity,
                            'product_status': status_display.get(product.status, product.status),
                            'variant_active': 'نعم' if variant.is_active else 'لا',
                            'created_at': product.created_at.strftime('%Y-%m-%d') if product.created_at else '',
                        }
                        if include_images:
                            row_data['image_url'] = image_url
                        yield row_data
                else:
                    row_data = {
                        'product_id': str(product.id),
                        'product_sku': product.sku or '',
                        'barcode': product.barcode or '',
                        'product_name': product.name,
                        'product_name_en': product.name_en or '',
                        'category': product.category.name if product.category else '',
                        'brand': product.brand.name if product.brand else '',
                        'variant_id': '-',
                        'variant_name': '-',
                        'variant_sku': '-',
                        'variant_attributes': '-',
                        'variant_price': str(product.base_price),
                        'variant_stock': product.stock_quantity,
                        'product_status': status_display.get(product.status, product.status),
                        'variant_active': '-',
                        'created_at': product.created_at.strftime('%Y-%m-%d') if product.created_at else '',
                    }
                    if include_images:
                        row_data['image_url'] = image_url
                    yield row_data
            else:
                row_data = {
                    'product_id': str(product.id),
                    'product_sku': product.sku or '',
                    'barcode': product.barcode or '',
                    'product_name': product.name,
                    'product_name_en': product.name_en or '',
                    'category': product.category.name if product.category else '',
                    'brand': product.brand.name if product.brand else '',
                    'base_price': str(product.base_price),
                    'stock_quantity': product.stock_quantity,
                    'product_status': status_display.get(product.status, product.status),
                    'variant_active': 'نعم' if product.is_active else 'لا',
                    'created_at': product.created_at.strftime('%Y-%m-%d') if product.created_at else '',
                }
                if include_images:
                    row_data['image_url'] = image_url
                yield row_data


@login_required
def export_products_view(request):
    """تصدير المنتجات"""
    export_format = request.GET.get('format', 'excel').lower()
    include_variants = request.GET.get('include_variants', 'true').lower() == 'true'
    include_images = request.GET.get('include_images', 'false').lower() == 'true'

    queryset = _build_export_queryset(request, include_images=include_images)
    columns = _get_export_columns(include_variants, include_images)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    base_url = request.build_absolute_uri('/')[:-1] if include_images else ''

    if export_format == 'excel':
        return _export_products_excel_streaming(queryset, columns, timestamp, include_variants, include_images, base_url)
    elif export_format == 'csv':
        return _export_products_csv_streaming(queryset, columns, timestamp, include_variants, include_images, base_url)
    elif export_format == 'pdf':
        export_data = []
        for i, item in enumerate(_generate_export_data_iterator(queryset, include_variants, include_images, base_url)):
            if i >= PDF_PRINT_MAX_RECORDS:
                break
            export_data.append(item)
        return _export_products_pdf(export_data, columns, timestamp)
    elif export_format == 'print':
        export_data = []
        for i, item in enumerate(_generate_export_data_iterator(queryset, include_variants, include_images, base_url)):
            if i >= PDF_PRINT_MAX_RECORDS:
                break
            export_data.append(item)
        return _export_products_print(export_data, columns, request)
    else:
        return _export_products_excel_streaming(queryset, columns, timestamp, include_variants, include_images, base_url)


def _export_products_excel_streaming(queryset, columns, timestamp, include_variants=True, include_images=False, base_url=''):
    """تصدير Excel مع streaming"""
    output = io.BytesIO()

    workbook = xlsxwriter.Workbook(output, {
        'in_memory': True,
        'constant_memory': True,
    })
    worksheet = workbook.add_worksheet('المنتجات')
    worksheet.right_to_left()

    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#0077c8',
        'font_color': 'white',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_name': 'Arial',
        'font_size': 11,
    })

    cell_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_name': 'Arial',
        'font_size': 10,
    })

    number_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_name': 'Arial',
        'font_size': 10,
        'num_format': '#,##0.00',
    })

    url_format = workbook.add_format({
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'font_name': 'Arial',
        'font_size': 9,
        'font_color': 'blue',
        'underline': True,
    })

    col_keys = list(columns.keys())
    for col_num, key in enumerate(col_keys):
        worksheet.write(0, col_num, columns[key], header_format)
        if 'name' in key:
            worksheet.set_column(col_num, col_num, 25)
        elif 'id' in key:
            worksheet.set_column(col_num, col_num, 12)
        elif 'image_url' in key:
            worksheet.set_column(col_num, col_num, 50)
        elif 'attributes' in key:
            worksheet.set_column(col_num, col_num, 40)
        else:
            worksheet.set_column(col_num, col_num, 15)

    row_num = 0
    price_keys = ['variant_price', 'base_price']
    stock_keys = ['variant_stock', 'stock_quantity']

    for row_data in _generate_export_data_iterator(queryset, include_variants, include_images, base_url):
        row_num += 1
        for col_num, key in enumerate(col_keys):
            value = row_data.get(key, '')
            if key in price_keys:
                try:
                    worksheet.write_number(row_num, col_num, float(value) if value else 0, number_format)
                except (ValueError, TypeError):
                    worksheet.write(row_num, col_num, value, cell_format)
            elif key in stock_keys:
                try:
                    worksheet.write_number(row_num, col_num, int(value) if value else 0, cell_format)
                except (ValueError, TypeError):
                    worksheet.write(row_num, col_num, value, cell_format)
            elif key == 'image_url' and value:
                worksheet.write_url(row_num, col_num, value, url_format, value)
            else:
                worksheet.write(row_num, col_num, str(value), cell_format)

    worksheet.freeze_panes(1, 0)
    if row_num > 0:
        worksheet.autofilter(0, 0, row_num, len(col_keys) - 1)

    workbook.close()
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="products_export_{timestamp}.xlsx"'

    return response


def _export_products_csv_streaming(queryset, columns, timestamp, include_variants=True, include_images=False, base_url=''):
    """تصدير CSV مع streaming"""
    from django.http import StreamingHttpResponse

    col_keys = list(columns.keys())

    def generate_csv():
        yield '\ufeff'
        header_row = ','.join([f'"{columns[key]}"' for key in col_keys])
        yield header_row + '\n'

        for row_data in _generate_export_data_iterator(queryset, include_variants, include_images, base_url):
            row_values = []
            for key in col_keys:
                value = str(row_data.get(key, '')).replace('"', '""')
                row_values.append(f'"{value}"')
            yield ','.join(row_values) + '\n'

    response = StreamingHttpResponse(
        generate_csv(),
        content_type='text/csv; charset=utf-8-sig'
    )
    response['Content-Disposition'] = f'attachment; filename="products_export_{timestamp}.csv"'

    return response


def _export_products_pdf(data, columns, timestamp):
    """تصدير PDF"""
    from django.template.loader import render_to_string

    html_content = render_to_string('dashboard/products/export_pdf.html', {
        'data': data,
        'columns': columns,
        'title': 'قائمة المنتجات',
        'timestamp': timestamp,
        'total_count': len(data),
    })

    response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="products_export_{timestamp}.html"'

    return response


def _export_products_print(data, columns, request):
    """صفحة طباعة"""
    return render(request, 'dashboard/products/export_print.html', {
        'data': data,
        'columns': columns,
        'title': 'قائمة المنتجات',
        'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M'),
        'total_count': len(data),
    })
