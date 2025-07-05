# views/products.py
# عروض إدارة المنتجات والتصنيفات

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify
import uuid
import json
from django.views.decorators.http import require_POST
from dashboard.forms.products import ProductForm
from django.utils.translation import gettext as _
from datetime import datetime
import re
import os

from decimal import Decimal, InvalidOperation


from products.models import (
    Product, Category, Brand, Tag, ProductImage,
    ProductVariant, ProductAttribute, ProductAttributeValue,
    ProductReview, ProductDiscount
)
from .dashboard import DashboardAccessMixin

import pandas as pd
from dashboard.forms.import_export import ProductImportForm
import numpy as np  # أضف هذا السطر
from django.core.cache import cache  # أضف هذا السطر

from django.http import HttpResponse
from io import BytesIO
from datetime import datetime
import pandas as pd
import xlsxwriter


def generate_excel_template(request):
    """
    توليد قالب Excel فارغ للاستيراد
    """
    # إنشاء ملف Excel جديد في الذاكرة
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('منتجات')

    # تنسيق للعناوين
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D7E4BC',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    })

    # تنسيق للأعمدة الإلزامية
    required_format = workbook.add_format({
        'bold': True,
        'bg_color': '#FFC7CE',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    })

    # تنسيق للتوضيح
    info_format = workbook.add_format({
        'font_color': '#666666',
        'italic': True,
        'font_size': 9,
        'align': 'center',
    })

    # قائمة بالأعمدة المطلوبة - مع الاحتفاظ بالعنوان الإنجليزي كما هو للاستيراد
    columns = [
        {'name': 'name', 'title': 'الاسم *', 'width': 30, 'required': True, 'example': 'جوال سامسونج S21'},
        {'name': 'sku', 'title': 'SKU', 'width': 15, 'required': False, 'example': 'SM-G991B'},
        {'name': 'name_en', 'title': 'الاسم بالإنجليزية', 'width': 30, 'required': False,
         'example': 'Samsung Galaxy S21'},
        {'name': 'base_price', 'title': 'السعر الأساسي', 'width': 15, 'required': False, 'example': '3499.99'},
        {'name': 'compare_price', 'title': 'سعر المقارنة', 'width': 15, 'required': False, 'example': '3999.99'},
        {'name': 'cost', 'title': 'التكلفة', 'width': 15, 'required': False, 'example': '2800'},
        {'name': 'stock_quantity', 'title': 'كمية المخزون', 'width': 15, 'required': False, 'example': '50'},
        {'name': 'category', 'title': 'الفئة', 'width': 20, 'required': False, 'example': 'الأجهزة الذكية'},
        {'name': 'brand', 'title': 'العلامة التجارية', 'width': 20, 'required': False, 'example': 'سامسونج'},
        {'name': 'barcode', 'title': 'الباركود', 'width': 20, 'required': False, 'example': '8806090742286'},
        {'name': 'status', 'title': 'الحالة', 'width': 15, 'required': False, 'example': 'published'},
        {'name': 'stock_status', 'title': 'حالة المخزون', 'width': 15, 'required': False, 'example': 'in_stock'},
        {'name': 'is_active', 'title': 'نشط', 'width': 10, 'required': False, 'example': 'Yes'},
        {'name': 'is_featured', 'title': 'مميز', 'width': 10, 'required': False, 'example': 'No'},
        {'name': 'is_new', 'title': 'جديد', 'width': 10, 'required': False, 'example': 'Yes'},
        {'name': 'is_best_seller', 'title': 'الأكثر مبيعاً', 'width': 10, 'required': False, 'example': 'No'},
        {'name': 'short_description', 'title': 'وصف مختصر', 'width': 40, 'required': False,
         'example': 'هاتف ذكي من سلسلة جالاكسي S21 بشاشة 6.2 إنش'},
        {'name': 'description', 'title': 'الوصف', 'width': 50, 'required': False, 'example': 'وصف كامل للمنتج...'},
        {'name': 'tags', 'title': 'الوسوم', 'width': 20, 'required': False, 'example': 'هواتف ذكية,سامسونج,5G'},
    ]

    # كتابة صف العنوان الإنجليزي (سيتم استخدامه للاستيراد)
    for col, column in enumerate(columns):
        worksheet.write(0, col, column['name'], header_format)

    # كتابة صف العنوان العربي (للتوضيح فقط)
    for col, column in enumerate(columns):
        format_to_use = required_format if column['required'] else header_format
        worksheet.write(1, col, column['title'], format_to_use)

    # كتابة تنبيه صغير حول أهمية صف العناوين الإنجليزية
    worksheet.merge_range(2, 0, 2, len(columns) - 1,
                          "هام: لا تقم بتعديل أو حذف الصف الأول (العناوين الإنجليزية) لأنه ضروري لعملية الاستيراد",
                          info_format)

    # كتابة صف مثال
    example_format = workbook.add_format({
        'italic': True,
        'bg_color': '#E6F4EA',
        'border': 1
    })

    for col, column in enumerate(columns):
        worksheet.write(3, col, column['example'], example_format)

    # تعيين عرض الأعمدة
    for col, column in enumerate(columns):
        worksheet.set_column(col, col, column['width'])

    # تجميد الأعمدة
    worksheet.freeze_panes(4, 0)  # تجميد 3 صفوف علوية

    # كتابة ملاحظات استخدام القالب
    notes_row = 5
    note_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top'
    })

    notes = [
        'الحقول المميزة باللون الأحمر إلزامية (*)',
        'SKU: إذا تُرك فارغاً سيتم إنشاؤه تلقائياً',
        'الفئة: إذا لم تكن موجودة، سيتم إنشاؤها تلقائياً أو استخدام الفئة الافتراضية',
        'العلامة التجارية: إذا لم تكن موجودة، سيتم إنشاؤها تلقائياً',
        'الحالة: يمكن أن تكون published, draft, pending_review, archived',
        'حالة المخزون: يمكن أن تكون in_stock, out_of_stock, pre_order, discontinued',
        'الحقول البوليانية (نشط، مميز، الخ): يمكن استخدام Yes/No، نعم/لا، True/False، 1/0',
        'الوسوم: يمكن فصلها بفواصل مثل "وسم1,وسم2,وسم3"'
    ]

    for i, note in enumerate(notes):
        worksheet.merge_range(notes_row + i, 0, notes_row + i, 6, note, note_format)

    # إغلاق الملف
    workbook.close()

    # إرجاع الملف للتنزيل
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=product_import_template.xlsx'

    return response


def direct_import_view(request):
    """
    استيراد المنتجات - صفحة تحميل الملف والاستيراد المباشر
    """
    if request.method == 'POST':
        form = ProductImportForm(request.POST, request.FILES)

        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form[field].label}: {error}")
            return redirect('dashboard:product_import')

        # استرجاع بيانات النموذج
        excel_file = request.FILES['file']
        update_existing = form.cleaned_data.get('update_existing', True)
        default_category = form.cleaned_data.get('category')

        # التحقق من امتداد الملف
        file_name = excel_file.name
        if not (file_name.endswith('.xlsx') or file_name.endswith('.xls')):
            messages.error(request, "الملف المرفوع ليس بصيغة Excel المدعومة (.xlsx, .xls)")
            return redirect('dashboard:product_import')

        try:
            # قراءة ملف Excel
            df = pd.read_excel(excel_file, sheet_name=0)

            # التحقق من وجود البيانات
            if df.empty:
                messages.error(request, "ملف Excel فارغ - لا توجد بيانات للاستيراد")
                return redirect('dashboard:product_import')

            # التحقق من وجود الأعمدة المطلوبة
            required_columns = ['name']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                messages.error(request, f"الأعمدة التالية مفقودة في الملف: {', '.join(missing_columns)}")
                return redirect('dashboard:product_import')

            # حفظ الملف الأصلي للاستخدام لاحقاً إذا لزم الأمر
            import_id = uuid.uuid4().hex
            temp_dir = os.path.join('media', 'temp', 'imports')
            os.makedirs(temp_dir, exist_ok=True)
            original_file_path = os.path.join(temp_dir, f"{import_id}_{file_name}")

            with open(original_file_path, 'wb+') as destination:
                for chunk in excel_file.chunks():
                    destination.write(chunk)

            # تحويل DataFrame إلى قائمة قواميس
            df_records = []
            for index, row in df.iterrows():
                record = {}
                for column in df.columns:
                    value = row[column]
                    if pd.isna(value):
                        record[column] = ""
                    else:
                        record[column] = value
                df_records.append(record)

            # تخزين البيانات في cache
            cache_data = {
                'df': df_records,
                'update_existing': update_existing,
                'default_category_id': default_category.id if default_category else None,
                'original_file_path': original_file_path
            }

            # تخزين في cache لمدة ساعة
            cache.set(f'import_data_{import_id}', json.dumps(cache_data, default=str), 3600)

            # تخزين حالة التقدم الأولية
            progress_data = {
                'total': len(df),
                'processed': 0,
                'success': 0,
                'updated': 0,
                'errors': 0,
                'status': 'pending',
                'error_details': []
            }
            cache.set(f'import_progress_{import_id}', json.dumps(progress_data), 3600)

            # بدء عملية الاستيراد مباشرة
            import threading
            thread = threading.Thread(
                target=_import_products,
                args=(import_id, df_records, update_existing, default_category, request.user)
            )
            thread.daemon = True
            thread.start()

            # توجيه المستخدم إلى صفحة عرض النتائج
            messages.success(request, f"تم بدء استيراد {len(df)} منتج. يرجى الانتظار حتى اكتمال العملية.")
            return redirect('dashboard:import_results', import_id=import_id)

        except Exception as e:
            error_msg = f"{e}"
            messages.error(request, f"حدث خطأ أثناء معالجة ملف Excel: {error_msg}")
            return redirect('dashboard:product_import')
    else:
        # عرض نموذج الاستيراد
        form = ProductImportForm()

        context = {
            'form': form,
            'form_title': 'استيراد المنتجات من Excel',
        }

        return render(request, 'dashboard/products/product_import.html', context)

def direct_import_products(request):
    """
    استيراد المنتجات مباشرة دون معاينة
    """
    if request.method != 'POST':
        messages.error(request, "طريقة الطلب غير صحيحة")
        return redirect('dashboard:product_import')

    form = ProductImportForm(request.POST, request.FILES)

    if not form.is_valid():
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{form[field].label}: {error}")
        return redirect('dashboard:product_import')

    # استرجاع بيانات النموذج
    excel_file = request.FILES['file']
    update_existing = form.cleaned_data.get('update_existing', True)
    default_category = form.cleaned_data.get('category')

    # التحقق من امتداد الملف
    file_name = excel_file.name
    if not (file_name.endswith('.xlsx') or file_name.endswith('.xls')):
        messages.error(request, "الملف المرفوع ليس بصيغة Excel المدعومة (.xlsx, .xls)")
        return redirect('dashboard:product_import')

    try:
        # قراءة ملف Excel
        df = pd.read_excel(excel_file, sheet_name=0)

        # التحقق من وجود البيانات
        if df.empty:
            messages.error(request, "ملف Excel فارغ - لا توجد بيانات للاستيراد")
            return redirect('dashboard:product_import')

        # التحقق من وجود الأعمدة المطلوبة
        required_columns = ['name']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            messages.error(request, f"الأعمدة التالية مفقودة في الملف: {', '.join(missing_columns)}")
            return redirect('dashboard:product_import')

        # حفظ الملف الأصلي للاستخدام لاحقاً إذا لزم الأمر
        import_id = uuid.uuid4().hex
        temp_dir = os.path.join('media', 'temp', 'imports')
        os.makedirs(temp_dir, exist_ok=True)
        original_file_path = os.path.join(temp_dir, f"{import_id}_{file_name}")

        with open(original_file_path, 'wb+') as destination:
            for chunk in excel_file.chunks():
                destination.write(chunk)

        # تحويل DataFrame إلى قائمة قواميس
        df_records = []
        for index, row in df.iterrows():
            record = {}
            for column in df.columns:
                value = row[column]
                if pd.isna(value):
                    record[column] = ""
                else:
                    record[column] = value
            df_records.append(record)

        # تخزين البيانات في cache
        cache_data = {
            'df': df_records,
            'update_existing': update_existing,
            'default_category_id': default_category.id if default_category else None,
            'original_file_path': original_file_path
        }

        # تخزين في cache لمدة ساعة
        cache.set(f'import_data_{import_id}', json.dumps(cache_data, default=str), 3600)

        # تخزين حالة التقدم الأولية
        progress_data = {
            'total': len(df),
            'processed': 0,
            'success': 0,
            'updated': 0,
            'errors': 0,
            'status': 'pending',
            'error_details': []
        }
        cache.set(f'import_progress_{import_id}', json.dumps(progress_data), 3600)

        # بدء عملية الاستيراد مباشرة
        import threading
        thread = threading.Thread(
            target=_import_products,
            args=(import_id, df_records, update_existing, default_category, request.user)
        )
        thread.daemon = True
        thread.start()

        # توجيه المستخدم إلى صفحة عرض النتائج
        messages.success(request, f"تم بدء استيراد {len(df)} منتج. يرجى الانتظار حتى اكتمال العملية.")
        return redirect('dashboard:import_results', import_id=import_id)

    except Exception as e:
        error_msg = f"{e}"
        messages.error(request, f"حدث خطأ أثناء معالجة ملف Excel: {error_msg}")
        return redirect('dashboard:product_import')


def import_results(request, import_id):
    """
    عرض نتائج الاستيراد وتتبع التقدم
    """
    # استرجاع بيانات التقدم من cache
    progress_json = cache.get(f'import_progress_{import_id}')
    if not progress_json:
        messages.error(request, "انتهت صلاحية بيانات الاستيراد أو أن معرف الاستيراد غير صحيح")
        return redirect('dashboard:product_import')

    progress_data = json.loads(progress_json)

    # استرجاع بيانات الاستيراد
    import_data_json = cache.get(f'import_data_{import_id}')
    import_data = json.loads(import_data_json) if import_data_json else {}

    context = {
        'import_id': import_id,
        'progress': progress_data,
        'total_rows': progress_data.get('total', 0),
        'is_completed': progress_data.get('status') == 'completed',
        'has_errors': progress_data.get('errors', 0) > 0,
        'error_details': progress_data.get('error_details', [])[:50],  # عرض أول 50 خطأ فقط
        'error_count': len(progress_data.get('error_details', [])),
        'update_existing': import_data.get('update_existing', False),
        'default_category_id': import_data.get('default_category_id', None)
    }

    return render(request, 'dashboard/products/import_results.html', context)


def export_import_errors(request):
    """
    تصدير المنتجات التي فشل استيرادها إلى ملف Excel
    """
    import_id = request.GET.get('import_id')

    if not import_id:
        messages.error(request, 'معرف الاستيراد مفقود')
        return redirect('dashboard:product_import')

    # استرجاع بيانات التقدم من cache
    progress_json = cache.get(f'import_progress_{import_id}')
    if not progress_json:
        messages.error(request, 'انتهت صلاحية بيانات الاستيراد')
        return redirect('dashboard:product_import')

    progress_data = json.loads(progress_json)
    error_details = progress_data.get('error_details', [])

    if not error_details:
        messages.warning(request, 'لا توجد أخطاء للتصدير')
        return redirect('dashboard:import_results', import_id=import_id)

    # إنشاء DataFrame من بيانات الأخطاء
    error_rows = []
    for error in error_details:
        row_data = {
            'رقم_الصف': error.get('row', 0),
            'الاسم': error.get('name', 'غير معروف'),
            'SKU': error.get('sku', 'غير معروف'),
            'رسالة_الخطأ': error.get('error', 'خطأ غير معروف')
        }

        # إضافة بيانات الصف الأصلية إذا كانت متاحة
        if 'data' in error:
            for key, value in error.get('data', {}).items():
                if key not in row_data and key not in ['row', 'name', 'sku', 'error']:
                    row_data[key] = value

        error_rows.append(row_data)

    # إنشاء DataFrame
    df = pd.DataFrame(error_rows)

    # ترتيب الأعمدة
    columns = ['رقم_الصف', 'الاسم', 'SKU', 'رسالة_الخطأ']
    other_columns = [col for col in df.columns if col not in columns]
    df = df[columns + other_columns]

    # إنشاء ملف Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='أخطاء الاستيراد', index=False)

        # تنسيق الملف
        workbook = writer.book
        worksheet = writer.sheets['أخطاء الاستيراد']

        # تنسيق العناوين
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'
        })

        # تنسيق خلايا الأخطاء
        error_format = workbook.add_format({
            'bg_color': '#FFC7CE', 'text_wrap': True
        })

        # تطبيق التنسيق
        for idx, col in enumerate(df.columns):
            worksheet.write(0, idx, col, header_format)

        # تمييز عمود رسالة الخطأ
        error_col_idx = 3  # عمود رسالة الخطأ هو الرابع
        worksheet.set_column(error_col_idx, error_col_idx, 40)
        worksheet.conditional_format(1, error_col_idx, len(df) + 1, error_col_idx,
                                     {'type': 'no_blanks', 'format': error_format})

        # تعيين عرض الأعمدة
        column_widths = [10, 30, 15, 40]
        for i, width in enumerate(column_widths):
            if i < len(df.columns):
                worksheet.set_column(i, i, width)

    # إنشاء استجابة للتنزيل
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=import_errors_{timestamp}.xlsx'

    return response





@login_required
def product_import_direct(request, import_id):
    """وظيفة مباشرة للاستيراد (للاختبار)"""
    view = ProductImportView()
    view.execute_import(import_id, request)
    messages.success(request, "تم بدء عملية الاستيراد بنجاح")
    return redirect('dashboard:dashboard_products')


# def export_import_errors(request):
#     """تصدير المنتجات التي فشل استيرادها إلى ملف Excel"""
#     import_id = request.GET.get('import_id')
#
#     if not import_id:
#         messages.error(request, 'معرف الاستيراد مفقود')
#         return redirect('dashboard:product_import')
#
#     # استرجاع بيانات التقدم من cache
#     progress_json = cache.get(f'import_progress_{import_id}')
#     if not progress_json:
#         messages.error(request, 'انتهت صلاحية بيانات الاستيراد')
#         return redirect('dashboard:product_import')
#
#     progress_data = json.loads(progress_json)
#     error_details = progress_data.get('error_details', [])
#
#     if not error_details:
#         messages.warning(request, 'لا توجد أخطاء للتصدير')
#         return redirect('dashboard:product_import')
#
#     # إنشاء DataFrame من بيانات الأخطاء
#     error_rows = []
#     for error in error_details:
#         row_data = {
#             'رقم_الصف': error.get('row', 0),
#             'الاسم': error.get('name', 'غير معروف'),
#             'SKU': error.get('sku', 'غير معروف'),
#             'رسالة_الخطأ': error.get('error', 'خطأ غير معروف')
#         }
#
#         # إضافة بيانات الصف الأصلية إذا كانت متاحة
#         if 'data' in error:
#             for key, value in error.get('data', {}).items():
#                 if key not in row_data and key not in ['row', 'name', 'sku', 'error']:
#                     row_data[key] = value
#
#         error_rows.append(row_data)
#
#     # إنشاء DataFrame
#     import pandas as pd
#     df = pd.DataFrame(error_rows)
#
#     # ترتيب الأعمدة
#     columns = ['رقم_الصف', 'الاسم', 'SKU', 'رسالة_الخطأ']
#     other_columns = [col for col in df.columns if col not in columns]
#     df = df[columns + other_columns]
#
#     # إنشاء ملف Excel
#     output = BytesIO()
#     with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
#         df.to_excel(writer, sheet_name='أخطاء الاستيراد', index=False)
#
#         # تنسيق الملف
#         workbook = writer.book
#         worksheet = writer.sheets['أخطاء الاستيراد']
#
#         # تنسيق العناوين
#         header_format = workbook.add_format({
#             'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'
#         })
#
#         # تنسيق خلايا الأخطاء
#         error_format = workbook.add_format({
#             'bg_color': '#FFC7CE', 'text_wrap': True
#         })
#
#         # تطبيق التنسيق
#         for idx, col in enumerate(df.columns):
#             worksheet.write(0, idx, col, header_format)
#
#         # تمييز عمود رسالة الخطأ
#         error_col_idx = 3  # عمود رسالة الخطأ هو الرابع
#         worksheet.set_column(error_col_idx, error_col_idx, 40)
#         worksheet.conditional_format(1, error_col_idx, len(df) + 1, error_col_idx,
#                                      {'type': 'no_blanks', 'format': error_format})
#
#         # تعيين عرض الأعمدة
#         column_widths = [10, 30, 15, 40]
#         for i, width in enumerate(column_widths):
#             if i < len(df.columns):
#                 worksheet.set_column(i, i, width)
#
#     # إنشاء استجابة للتنزيل
#     output.seek(0)
#     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#     response = HttpResponse(
#         output.read(),
#         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#     )
#     response['Content-Disposition'] = f'attachment; filename=import_errors_{timestamp}.xlsx'
#
#     return response



class ProductImportView(DashboardAccessMixin, View):
    """استيراد المنتجات من ملف Excel مع إمكانية تصدير الأخطاء"""

    def get(self, request):
        """عرض نموذج استيراد المنتجات"""
        form = ProductImportForm()

        context = {
            'form': form,
            'form_title': 'استيراد المنتجات من Excel',
        }

        return render(request, 'dashboard/products/product_import.html', context)

    def post(self, request):
        """معالجة عملية استيراد المنتجات"""

        # معالجة AJAX للمعاينة أو الاستيراد النهائي
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            action = request.POST.get('action', '')

            if action == 'import':
                # تنفيذ عملية الاستيراد
                preview_id = request.POST.get('preview_id')
                if not preview_id:
                    return JsonResponse({'success': False, 'error': 'معرف المعاينة مفقود'})
                return self.execute_import(preview_id, request)

            elif action == 'export_errors':
                # تصدير الأخطاء إلى ملف Excel
                preview_id = request.POST.get('preview_id')
                if not preview_id:
                    return JsonResponse({'success': False, 'error': 'معرف المعاينة مفقود'})
                return self.export_errors(preview_id, request)

        form = ProductImportForm(request.POST, request.FILES)

        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form[field].label}: {error}")
            return redirect('dashboard:product_import')

        # استرجاع بيانات النموذج
        excel_file = request.FILES['file']
        update_existing = form.cleaned_data.get('update_existing', True)
        default_category = form.cleaned_data.get('category')

        # التحقق من امتداد الملف
        file_name = excel_file.name
        if not (file_name.endswith('.xlsx') or file_name.endswith('.xls')):
            messages.error(request, "الملف المرفوع ليس بصيغة Excel المدعومة (.xlsx, .xls)")
            return redirect('dashboard:product_import')

        # قراءة ملف Excel للمعاينة
        try:
            df = pd.read_excel(excel_file, sheet_name=0)

            # التحقق من وجود البيانات
            if df.empty:
                messages.error(request, "ملف Excel فارغ - لا توجد بيانات للاستيراد")
                return redirect('dashboard:product_import')

            # التحقق من وجود الأعمدة المطلوبة
            required_columns = ['name']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                messages.error(request, f"الأعمدة التالية مفقودة في الملف: {', '.join(missing_columns)}")
                return redirect('dashboard:product_import')

            # حفظ الملف الأصلي للاستخدام لاحقاً إذا لزم الأمر
            import_id = uuid.uuid4().hex
            temp_dir = os.path.join('media', 'temp', 'imports')
            os.makedirs(temp_dir, exist_ok=True)
            original_file_path = os.path.join(temp_dir, f"{import_id}_{file_name}")

            with open(original_file_path, 'wb+') as destination:
                for chunk in excel_file.chunks():
                    destination.write(chunk)

            # تحضير البيانات للمعاينة
            preview_data = []
            validation_errors = []

            # حل بسيط لتحويل DataFrame إلى قاموس وتعامل مع القيم الفارغة
            df_records = []
            for index, row in df.iterrows():
                record = {}
                for column in df.columns:
                    value = row[column]
                    if pd.isna(value):
                        record[column] = ""
                    else:
                        record[column] = value
                df_records.append(record)

            # عملية المعاينة
            for index, row in enumerate(df_records):
                try:
                    # استخراج البيانات الأساسية
                    row_number = index + 2
                    name = row.get('name', '')
                    if not isinstance(name, str):
                        name = f"{name}"
                    name = name.strip()

                    sku = row.get('sku', '')
                    if not isinstance(sku, str):
                        sku = f"{sku}"
                    sku = sku.strip() or f"SKU-{uuid.uuid4().hex[:8].upper()}"

                    # فحص البيانات الإلزامية
                    if not name:
                        raise ValueError(f"اسم المنتج مطلوب في الصف {row_number}")

                    # التحقق من وجود المنتج بواسطة SKU
                    existing_product = None
                    if sku and not sku.startswith("SKU-"):
                        try:
                            existing_product = Product.objects.get(sku=sku)
                        except Product.DoesNotExist:
                            pass

                    # استخراج السعر
                    price = 0
                    price_value = row.get('base_price', 0)
                    if price_value is not None and price_value != "":
                        try:
                            price = float(price_value)
                        except (ValueError, TypeError):
                            price = 0

                    # إضافة الصف للمعاينة
                    preview_data.append({
                        'row': row_number,
                        'name': name,
                        'sku': sku,
                        'price': price,
                        'exists': existing_product is not None,
                        'status': _('موجود') if existing_product else _('جديد')
                    })

                except Exception as e:
                    error_msg = f"{e}"
                    validation_errors.append({
                        'row': index + 2,
                        'name': row.get('name', ''),
                        'sku': row.get('sku', ''),
                        'error': error_msg
                    })

            # حفظ البيانات للاستخدام لاحقًا
            # تخزين البيانات
            cache_data = {
                'df': df_records,
                'update_existing': update_existing,
                'default_category_id': default_category.id if default_category else None,
                'validation_errors': validation_errors,
                'original_file_path': original_file_path  # حفظ مسار الملف الأصلي
            }

            # تخزين في cache لمدة ساعة
            cache.set(f'import_data_{import_id}', json.dumps(cache_data, default=str), 3600)

            # تخزين حالة التقدم الأولية
            progress_data = {
                'total': len(df),
                'processed': 0,
                'success': 0,
                'updated': 0,
                'errors': 0,
                'status': 'pending',
                'error_details': []
            }
            cache.set(f'import_progress_{import_id}', json.dumps(progress_data), 3600)

            # عرض صفحة المعاينة
            return render(request, 'dashboard/products/product_preview.html', {
                'import_id': import_id,
                'preview_data': preview_data[:20],  # عرض أول 20 صف فقط
                'validation_errors': validation_errors[:10],  # عرض أول 10 أخطاء فقط
                'total_rows': len(df),
                'error_count': len(validation_errors),
                'form_data': {
                    'update_existing': update_existing,
                    'default_category': default_category.name if default_category else _("لا يوجد")
                }
            })

        except Exception as e:
            error_msg = f"{e}"
            messages.error(request, f"حدث خطأ أثناء معالجة ملف Excel: {error_msg}")
            return redirect('dashboard:product_import')

    def execute_import(self, import_id, request):
        """تنفيذ عملية استيراد المنتجات بناءً على بيانات المعاينة"""
        try:
            # استرجاع البيانات من cache
            import_data_json = cache.get(f'import_data_{import_id}')

            if not import_data_json:
                return JsonResponse({
                    'success': False,
                    'error': 'انتهت صلاحية بيانات الاستيراد. يرجى إعادة تحميل الملف'
                })

            # تحميل البيانات
            import_data = json.loads(import_data_json)
            df_dict = import_data['df']
            update_existing = import_data['update_existing']
            default_category_id = import_data['default_category_id']

            # الحصول على الفئة الافتراضية إذا كانت موجودة
            default_category = None
            if default_category_id:
                try:
                    default_category = Category.objects.get(id=default_category_id)
                except Category.DoesNotExist:
                    pass

            # تحديث حالة التقدم
            progress_data = {
                'total': len(df_dict),
                'processed': 0,
                'success': 0,
                'updated': 0,
                'errors': 0,
                'status': 'processing',
                'error_details': []
            }
            cache.set(f'import_progress_{import_id}', json.dumps(progress_data), 3600)

            # بدء عملية الاستيراد في خلفية منفصلة
            import threading
            thread = threading.Thread(
                target=self._import_products,
                args=(import_id, df_dict, update_existing, default_category, request.user)
            )
            thread.daemon = True
            thread.start()

            # إرجاع معرف الاستيراد للمتابعة
            return JsonResponse({
                'success': True,
                'import_id': import_id,
                'total_rows': len(df_dict)
            })

        except Exception as e:
            import traceback
            print(f"Error in execute_import: {e}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'error': f"حدث خطأ أثناء بدء الاستيراد: {e}"
            })

    def _import_products(import_id, df_dict, update_existing, default_category, user):
        """استيراد المنتجات في الخلفية"""
        from django.db import transaction  # إضافة هذا السطر لاستيراد transaction

        # استرجاع حالة التقدم
        progress_json = cache.get(f'import_progress_{import_id}')
        progress_data = json.loads(progress_json) if progress_json else {
            'total': len(df_dict),
            'processed': 0,
            'success': 0,
            'updated': 0,
            'errors': 0,
            'status': 'processing',
            'error_details': []
        }

        try:
            # معالجة كل صف
            for index, row in enumerate(df_dict):
                try:
                    row_number = index + 2  # +2 لأن الصف الأول هو العناوين والفهرس يبدأ من 0

                    with transaction.atomic():
                        # استخراج البيانات الأساسية
                        name_value = row.get('name', '')
                        name = f"{name_value}".strip() if name_value is not None else ""

                        sku_value = row.get('sku', '')
                        sku = f"{sku_value}".strip() if sku_value is not None else ""

                        # فحص البيانات الإلزامية
                        if not name:
                            raise ValueError(f"الصف {row_number}: اسم المنتج مطلوب")

                        if not sku:
                            # إنشاء SKU إذا لم يكن موجودًا
                            sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"

                        # البحث عن المنتج الموجود بواسطة SKU
                        existing_product = None
                        if update_existing:
                            try:
                                existing_product = Product.objects.get(sku=sku)
                            except Product.DoesNotExist:
                                pass

                        # تحديد ما إذا كنا سنقوم بالتحديث أو الإنشاء
                        if existing_product and update_existing:
                            product = existing_product
                            action = "update"
                        else:
                            product = Product()
                            action = "create"

                        # تعيين البيانات الأساسية
                        product.name = name
                        product.sku = sku

                        # البيانات الاختيارية
                        if 'barcode' in row and row['barcode'] is not None:
                            product.barcode = f"{row['barcode']}"

                        if 'name_en' in row and row['name_en'] is not None:
                            product.name_en = f"{row['name_en']}"

                        if 'description' in row and row['description'] is not None:
                            product.description = f"{row['description']}"

                        if 'short_description' in row and row['short_description'] is not None:
                            product.short_description = f"{row['short_description']}"

                        # معالجة الأسعار
                        if 'base_price' in row and row['base_price'] is not None:
                            try:
                                product.base_price = float(row['base_price'])
                            except (ValueError, TypeError):
                                raise ValueError(f"الصف {row_number}: قيمة السعر الأساسي غير صالحة")

                        if 'compare_price' in row and row['compare_price'] is not None:
                            try:
                                product.compare_price = float(row['compare_price'])
                            except (ValueError, TypeError):
                                raise ValueError(f"الصف {row_number}: قيمة سعر المقارنة غير صالحة")

                        if 'cost' in row and row['cost'] is not None:
                            try:
                                product.cost = float(row['cost'])
                            except (ValueError, TypeError):
                                raise ValueError(f"الصف {row_number}: قيمة التكلفة غير صالحة")

                        # معالجة المخزون
                        if 'stock_quantity' in row and row['stock_quantity'] is not None:
                            try:
                                product.stock_quantity = int(float(row['stock_quantity']))
                            except (ValueError, TypeError):
                                raise ValueError(f"الصف {row_number}: قيمة كمية المخزون غير صالحة")

                        # معالجة الفئة
                        if 'category' in row and row['category'] is not None:
                            category_value = row['category']
                            category_name = f"{category_value}".strip() if category_value is not None else ""
                            if category_name:
                                try:
                                    category = Category.objects.get(name=category_name)
                                    product.category = category
                                except Category.DoesNotExist:
                                    # محاولة البحث عن الفئة بالاسم الإنجليزي
                                    try:
                                        category = Category.objects.get(name_en=category_name)
                                        product.category = category
                                    except Category.DoesNotExist:
                                        if default_category:
                                            product.category = default_category
                                        else:
                                            # إنشاء فئة جديدة
                                            slug = slugify(category_name, allow_unicode=True)
                                            if Category.objects.filter(slug=slug).exists():
                                                slug = f"{slug}-{uuid.uuid4().hex[:6]}"

                                            new_category = Category.objects.create(
                                                name=category_name,
                                                slug=slug,
                                                is_active=True,
                                                created_by=user
                                            )
                                            product.category = new_category
                            elif default_category:
                                product.category = default_category
                        elif default_category:
                            product.category = default_category

                        # معالجة العلامة التجارية
                        if 'brand' in row and row['brand'] is not None:
                            brand_value = row['brand']
                            brand_name = f"{brand_value}".strip() if brand_value is not None else ""
                            if brand_name:
                                try:
                                    brand = Brand.objects.get(name=brand_name)
                                    product.brand = brand
                                except Brand.DoesNotExist:
                                    # محاولة البحث عن العلامة التجارية بالاسم الإنجليزي
                                    try:
                                        brand = Brand.objects.get(name_en=brand_name)
                                        product.brand = brand
                                    except Brand.DoesNotExist:
                                        # إنشاء علامة تجارية جديدة
                                        slug = slugify(brand_name, allow_unicode=True)
                                        if Brand.objects.filter(slug=slug).exists():
                                            slug = f"{slug}-{uuid.uuid4().hex[:6]}"

                                        new_brand = Brand.objects.create(
                                            name=brand_name,
                                            slug=slug,
                                            is_active=True,
                                            created_by=user
                                        )
                                        product.brand = new_brand

                        # معالجة حالة المنتج
                        if 'status' in row and row['status'] is not None:
                            status_value = row['status']
                            status = f"{status_value}".strip().lower() if status_value is not None else ""
                            if status in dict(Product.STATUS_CHOICES).keys():
                                product.status = status
                            else:
                                product.status = 'draft'

                        # معالجة حالة المخزون
                        if 'stock_status' in row and row['stock_status'] is not None:
                            stock_status_value = row['stock_status']
                            stock_status = f"{stock_status_value}".strip().lower() if stock_status_value is not None else ""
                            if stock_status in dict(Product.STOCK_STATUS_CHOICES).keys():
                                product.stock_status = stock_status
                            elif product.stock_quantity > 0:
                                product.stock_status = 'in_stock'
                            else:
                                product.stock_status = 'out_of_stock'
                        elif product.stock_quantity > 0:
                            product.stock_status = 'in_stock'
                        else:
                            product.stock_status = 'out_of_stock'

                        # معالجة الحقول البوليانية
                        for bool_field in ['is_active', 'is_featured', 'is_new', 'is_best_seller']:
                            if bool_field in row and row[bool_field] is not None:
                                value = row[bool_field]
                                if isinstance(value, bool):
                                    setattr(product, bool_field, value)
                                elif isinstance(value, str):
                                    value_lower = f"{value}".lower()
                                    setattr(product, bool_field, value_lower in ['yes', 'نعم', 'true', '1', 'y', 't'])

                        # إنشاء سلج للمنتجات الجديدة
                        if action == "create":
                            product.slug = slugify(name, allow_unicode=True)
                            if Product.objects.filter(slug=product.slug).exists():
                                product.slug = f"{product.slug}-{uuid.uuid4().hex[:6]}"

                            product.created_by = user

                        # حفظ المنتج
                        product.save()

                        # معالجة الوسوم (tags)
                        if 'tags' in row and row['tags'] is not None:
                            tags_value = row['tags']
                            tags_str = f"{tags_value}".strip() if tags_value is not None else ""
                            if tags_str:
                                # تقسيم الوسوم باستخدام الفواصل أو الفواصل المنقوطة
                                import re
                                tags_list = [tag.strip() for tag in re.split(r'[,;|]', tags_str) if tag.strip()]

                                for tag_name in tags_list:
                                    try:
                                        # البحث عن الوسم أو إنشائه
                                        tag, created = Tag.objects.get_or_create(
                                            name=tag_name,
                                            defaults={
                                                'slug': slugify(tag_name, allow_unicode=True),
                                                'is_active': True
                                            }
                                        )
                                        product.tags.add(tag)
                                    except Exception as tag_error:
                                        print(f"خطأ في إضافة الوسم {tag_name} للمنتج {name}: {tag_error}")

                        # تحديث الإحصائيات
                        if action == "create":
                            progress_data['success'] += 1
                        else:
                            progress_data['updated'] += 1

                except Exception as e:
                    # تسجيل الخطأ مع تفاصيل كاملة
                    error_message = f"{e}"

                    # طباعة معلومات الخطأ في السجل للتشخيص
                    print(f"خطأ في استيراد الصف {row_number}: {error_message}")
                    if 'name' in row:
                        print(f"اسم المنتج: {row['name']}")
                    if 'sku' in row:
                        print(f"SKU: {row['sku']}")

                    progress_data['errors'] += 1
                    progress_data['error_details'].append({
                        'row': row_number,
                        'name': f"{row.get('name', '')}" if row.get('name') is not None else "غير معروف",
                        'sku': f"{row.get('sku', '')}" if row.get('sku') is not None else "غير معروف",
                        'error': error_message,
                        'data': row  # حفظ كل بيانات الصف لاستخدامها في التصدير لاحقاً
                    })

                # تحديث التقدم
                progress_data['processed'] += 1

                # تحديث حالة التقدم في cache كل 5 صفوف أو عند الانتهاء
                if index % 5 == 0 or index == len(df_dict) - 1:
                    cache.set(f'import_progress_{import_id}', json.dumps(progress_data), 3600)

            # تحديث الحالة إلى مكتملة
            progress_data['status'] = 'completed'
            cache.set(f'import_progress_{import_id}', json.dumps(progress_data), 3600)

        except Exception as e:
            # تحديث الحالة إلى خطأ
            error_message = f"{e}"
            print(f"خطأ عام في عملية الاستيراد: {error_message}")

            progress_data['status'] = 'error'
            progress_data['error_message'] = error_message
            cache.set(f'import_progress_{import_id}', json.dumps(progress_data), 3600)

    def export_errors(self, import_id, request):
        """تصدير المنتجات التي تحتوي على أخطاء إلى ملف Excel"""
        try:
            # استرجاع بيانات التقدم من cache
            progress_json = cache.get(f'import_progress_{import_id}')
            if not progress_json:
                return JsonResponse({'success': False, 'error': 'انتهت صلاحية بيانات الاستيراد'})

            progress_data = json.loads(progress_json)
            error_details = progress_data.get('error_details', [])

            if not error_details:
                return JsonResponse({'success': False, 'error': 'لا توجد أخطاء للتصدير'})

            # إنشاء DataFrame لتصدير البيانات
            error_rows = []
            for error in error_details:
                row_data = error.get('data', {})
                row_data['error_message'] = error.get('error', 'خطأ غير معروف')
                row_data['row_number'] = error.get('row', 0)
                error_rows.append(row_data)

            # إنشاء DataFrame من قائمة الأخطاء
            df = pd.DataFrame(error_rows)

            # ترتيب الأعمدة بشكل منطقي
            # وضع رقم الصف ورسالة الخطأ في البداية
            columns = ['row_number', 'error_message']
            other_columns = [col for col in df.columns if col not in columns]
            df = df[columns + other_columns]

            # إنشاء ملف Excel في الذاكرة
            from io import BytesIO
            output = BytesIO()

            # استخدام ExcelWriter للحصول على مزيد من التحكم في التنسيق
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='أخطاء الاستيراد', index=False)

                # الحصول على ورقة العمل وضبط التنسيق
                worksheet = writer.sheets['أخطاء الاستيراد']

                # تنسيق العناوين
                header_format = writer.book.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'bg_color': '#D7E4BC',
                    'border': 1,
                    'align': 'center'
                })

                # تنسيق خلايا الأخطاء
                error_format = writer.book.add_format({
                    'bg_color': '#FFC7CE',
                    'text_wrap': True
                })

                # تطبيق التنسيق على عمود رسالة الخطأ
                worksheet.set_column('B:B', 40)  # تعيين عرض عمود رسالة الخطأ

                # تطبيق التنسيق على الخلايا
                for idx, col in enumerate(df.columns):
                    worksheet.write(0, idx, col, header_format)

                # تمييز عمود رسالة الخطأ
                error_col_idx = df.columns.get_loc('error_message')
                worksheet.conditional_format(1, error_col_idx, len(df) + 1, error_col_idx,
                                             {'type': 'no_blanks', 'format': error_format})

                # تنسيق إضافي لتحسين قراءة الملف
                for i, width in enumerate([10, 40]):  # عرض مخصص للأعمدة الأولى
                    worksheet.set_column(i, i, width)

            # استعادة الملف من الذاكرة
            output.seek(0)

            # إنشاء استجابة للتنزيل
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename=import_errors_{timestamp}.xlsx'

            return response

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': f'خطأ في تصدير الأخطاء: {str(e)}'})

@method_decorator(login_required, name='dispatch')
class ProductImportProgressView(View):
    """التحقق من حالة تقدم استيراد المنتجات"""

    def get(self, request):
        import_id = request.GET.get('import_id')

        if not import_id:
            return JsonResponse({'success': False, 'error': 'معرف الاستيراد مفقود'})

        # استرجاع حالة التقدم من cache
        progress_json = cache.get(f'import_progress_{import_id}')

        if not progress_json:
            return JsonResponse({'success': False, 'error': 'معرف الاستيراد غير صالح أو منتهي الصلاحية'})

        progress_data = json.loads(progress_json)
        return JsonResponse({
            'success': True,
            'progress': progress_data
        })


@method_decorator(login_required, name='dispatch')
class ProductImportProgressView(View):
    """التحقق من حالة تقدم استيراد المنتجات"""

    def get(self, request):
        import_id = request.GET.get('import_id')

        if not import_id:
            return JsonResponse({'success': False, 'error': 'معرف الاستيراد مفقود'})

        # استرجاع حالة التقدم من cache
        progress_json = cache.get(f'import_progress_{import_id}')

        if not progress_json:
            return JsonResponse({'success': False, 'error': 'معرف الاستيراد غير صالح أو منتهي الصلاحية'})

        progress_data = json.loads(progress_json)
        return JsonResponse({
            'success': True,
            'progress': progress_data
        })



# ========================= إدارة المنتجات =========================

class ProductDataTableView(DashboardAccessMixin, View):
    """واجهة برمجية لجدول المنتجات بالتحميل الجزئي"""

    def post(self, request):
        # استلام معلمات DataTables
        draw = int(request.POST.get('draw', 1))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 25))
        search_value = request.POST.get('search[value]', '')
        order_column = request.POST.get('order[0][column]', 7)  # العمود 7 هو التاريخ
        order_dir = request.POST.get('order[0][dir]', 'desc')

        # معلمات التصفية الإضافية
        category_filter = request.POST.get('category', '')
        brand_filter = request.POST.get('brand', '')
        status_filter = request.POST.get('status', '')

        # بناء الاستعلام
        queryset = Product.objects.select_related('category', 'brand')

        # تطبيق البحث
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(sku__icontains=search_value) |
                Q(description__icontains=search_value) |
                Q(search_keywords__icontains=search_value)
            )

        # تطبيق التصفية
        if category_filter:
            category = Category.objects.get(id=category_filter)
            # الحصول على جميع الفئات الفرعية
            subcategories = category.get_all_children(include_self=True)
            queryset = queryset.filter(category__in=subcategories)

        if brand_filter:
            queryset = queryset.filter(brand_id=brand_filter)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # تطبيق فلتر السعر
        price_min = request.POST.get('price_min', '')
        price_max = request.POST.get('price_max', '')

        if price_min:
            try:
                price_min = float(price_min)
                queryset = queryset.filter(base_price__gte=price_min)
            except (ValueError, TypeError):
                pass

        if price_max:
            try:
                price_max = float(price_max)
                queryset = queryset.filter(base_price__lte=price_max)
            except (ValueError, TypeError):
                pass

        # تطبيق فلتر المخزون
        stock_filter = request.POST.get('stock', '')
        if stock_filter:
            if stock_filter == 'in_stock':
                queryset = queryset.filter(stock_status='in_stock')
            elif stock_filter == 'out_of_stock':
                queryset = queryset.filter(stock_status='out_of_stock')
            elif stock_filter == 'low_stock':
                # يمكن تعديل هذا حسب كيفية تعريف "كمية منخفضة" في النظام
                queryset = queryset.filter(
                    stock_status='in_stock',
                    low_stock=True
                )
            elif stock_filter == 'pre_order':
                queryset = queryset.filter(stock_status='pre_order')

        # تطبيق فلتر التاريخ
        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')

        if date_from:
            try:
                # تحويل التاريخ إلى كائن date
                from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                # إضافة فلتر من بداية اليوم
                queryset = queryset.filter(created_at__date__gte=from_date)
            except (ValueError, TypeError):
                pass

        if date_to:
            try:
                # تحويل التاريخ إلى كائن date
                to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                # إضافة فلتر حتى نهاية اليوم
                queryset = queryset.filter(created_at__date__lte=to_date)
            except (ValueError, TypeError):
                pass

        # إجمالي السجلات قبل التصفية
        total_records = Product.objects.count()
        # إجمالي السجلات بعد التصفية
        total_filtered = queryset.count()

        # تطبيق الترتيب
        order_columns = [
            'id', 'name', 'sku', 'category__name',
            'base_price', 'stock_quantity', 'status', 'created_at'
        ]
        if int(order_column) < len(order_columns):
            order_field = order_columns[int(order_column)]
            if order_dir == 'desc':
                order_field = f"-{order_field}"
            queryset = queryset.order_by(order_field)

        # تطبيق التقسيم
        queryset = queryset[start:start + length]

        # إعداد البيانات للعرض
        data = []
        for product in queryset:
            data.append({
                'id': str(product.id),
                'name': product.name,
                'sku': product.sku,
                'category_name': product.category.name if product.category else '',
                'brand_name': product.brand.name if product.brand else '',
                'current_price': str(product.current_price),
                'compare_price': str(product.compare_price) if product.compare_price else '',
                'available_quantity': product.available_quantity,
                'low_stock': product.low_stock,
                'stock_status': product.stock_status,
                'status': product.status,
                'is_active': product.is_active,
                'is_featured': product.is_featured,
                'created_at': product.created_at.strftime('%Y/%m/%d'),
                'published_at': product.published_at.strftime('%Y/%m/%d') if product.published_at else '',
                'has_image': product.default_image is not None,
                'image_url': product.default_image.image.url if product.default_image else ''
            })

        # إرجاع النتيجة بتنسيق DataTables
        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_filtered,
            'data': data
        })

class ProductListView(DashboardAccessMixin, View):
    """عرض قائمة المنتجات مع البحث والتصفية"""

    def get(self, request):
        # البحث والتصفية
        query = request.GET.get('q', '')
        category_filter = request.GET.get('category', '')
        brand_filter = request.GET.get('brand', '')
        status_filter = request.GET.get('status', '')

        # قائمة المنتجات مع استعلام مُحسّن
        products = Product.objects.select_related('category', 'brand').prefetch_related('images').order_by(
            '-created_at')

        # تطبيق البحث
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(sku__icontains=query) |
                Q(description__icontains=query) |
                Q(search_keywords__icontains=query)
            )

        # تطبيق التصفية
        if category_filter:
            category = Category.objects.get(id=category_filter)
            # الحصول على جميع الفئات الفرعية أيضًا
            subcategories = category.get_all_children(include_self=True)
            products = products.filter(category__in=subcategories)

        if brand_filter:
            products = products.filter(brand_id=brand_filter)

        if status_filter:
            products = products.filter(status=status_filter)

        # التصفح الجزئي
        paginator = Paginator(products, 20)  # 20 منتج في كل صفحة
        page = request.GET.get('page', 1)
        products_page = paginator.get_page(page)

        # جلب قوائم التصفية
        categories = Category.objects.filter(level=0)  # الفئات الرئيسية فقط
        brands = Brand.objects.all().order_by('name')

        # الإحصائيات
        stats = {
            'total': Product.objects.count(),
            'active': Product.objects.filter(is_active=True).count(),
            'out_of_stock': Product.objects.filter(stock_status='out_of_stock').count(),
            'featured': Product.objects.filter(is_featured=True).count(),
        }

        context = {
            'products': products_page,
            'categories': categories,
            'brands': brands,
            'query': query,
            'category_filter': category_filter,
            'brand_filter': brand_filter,
            'status_filter': status_filter,
            'stats': stats,
            'status_choices': Product.STATUS_CHOICES,
        }

        # إذا كان الطلب AJAX، نعيد جزء الجدول فقط
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('dashboard/products/products_table.html', context, request)
            return JsonResponse({
                'html': html,
                'has_next': products_page.has_next(),
                'has_prev': products_page.has_previous(),
                'page': products_page.number,
                'pages': paginator.num_pages,
                'total': paginator.count
            })

        return render(request, 'dashboard/products/product_list.html', context)


class ProductDetailView(DashboardAccessMixin, View):
    """عرض تفاصيل المنتج"""

    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)

        # جلب البيانات المرتبطة
        variants = product.variants.all()
        images = product.images.all().order_by('sort_order')
        reviews = product.reviews.select_related('user').order_by('-created_at')[:10]
        attributes = product.attribute_values.select_related('attribute').all()
        related_products = product.related_products.all()

        # إحصائيات المبيعات
        sales_data = {
            'total_sales': product.sales_count,
            'avg_rating': product.rating,
            'review_count': product.review_count,
            'views': product.views_count,
            'wishlist_count': product.wishlist_count,
        }

        # معلومات المخزون
        stock_info = {
            'available': product.available_quantity,
            'reserved': product.reserved_quantity,
            'min_stock_level': product.min_stock_level,
            'total': product.stock_quantity,
            'status': product.stock_status,
            'low_stock': product.low_stock,
        }

        context = {
            'product': product,
            'variants': variants,
            'images': images,
            'reviews': reviews,
            'attributes': attributes,
            'related_products': related_products,
            'sales_data': sales_data,
            'stock_info': stock_info,
        }

        return render(request, 'dashboard/products/product_detail.html', context)


class ProductFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث المنتج باستخدام نموذج Django"""

    def get(self, request, product_id=None):
        """عرض نموذج إنشاء أو تحديث المنتج"""
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            form = ProductForm(instance=product)
            form_title = _('تحديث المنتج')
            images = product.images.all().order_by('sort_order')

            # تحميل المواصفات والميزات إلى النموذج
            form.initial['specifications_json'] = json.dumps(product.specifications, indent=4, ensure_ascii=False)

            # تحميل الميزات
            if product.features:
                if isinstance(product.features, list):
                    form.initial['features_json'] = json.dumps(product.features, indent=4, ensure_ascii=False)
                else:
                    # تحويل من أشكال أخرى إلى قائمة
                    try:
                        form.initial['features_json'] = json.dumps(list(product.features), indent=4, ensure_ascii=False)
                    except:
                        form.initial['features_json'] = '[]'

            # تحميل المنتجات ذات الصلة
            form.initial['related_products'] = product.related_products.all()

            # تحميل منتجات البيع المتقاطع والتصاعدي
            cross_sell_products = product.cross_sell_products.all()
            upsell_products = product.upsell_products.all()

            # تحميل صفات المنتج
            product_attributes = []
            for attr_value in product.attribute_values.select_related('attribute').all():
                form.initial[f'attribute_{attr_value.attribute_id}'] = attr_value.value
                product_attributes.append(attr_value.attribute)

            # تحميل متغيرات المنتج
            product_variants = product.variants.all().order_by('sort_order')
            # تحويل المتغيرات إلى JSON لاستخدامها في JavaScript
            variants_json = self.prepare_variants_json(product_variants)

        else:
            product = None
            form = ProductForm()
            form_title = _('إنشاء منتج جديد')
            images = []
            cross_sell_products = []
            upsell_products = []
            product_variants = []
            variants_json = '[]'
            product_attributes = []

        # تحميل البيانات اللازمة للقالب
        context = {
            'form': form,
            'product': product,
            'form_title': form_title,
            'images': images,
            'cross_sell_products': cross_sell_products,
            'upsell_products': upsell_products,
            'product_variants': product_variants,
            'variants_json': variants_json,
            'product_attributes': product_attributes,  # إضافة صفات المنتج إلى السياق
            'status_choices': Product.STATUS_CHOICES,
            'stock_status_choices': Product.STOCK_STATUS_CHOICES,
            'condition_choices': Product.CONDITION_CHOICES,
        }

        return render(request, 'dashboard/products/product_form.html', context)

    def post(self, request, product_id=None):
        """معالجة نموذج إنشاء أو تحديث المنتج"""
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            form = ProductForm(request.POST, request.FILES, instance=product)
        else:
            product = None
            form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                # حفظ المنتج
                product = form.save(commit=True, user=request.user)

                # معالجة صور المنتج
                images = request.FILES.getlist('product_images')
                if images:
                    for i, image_file in enumerate(images):
                        is_primary = i == 0 and not product.images.filter(is_primary=True).exists()
                        ProductImage.objects.create(
                            product=product,
                            image=image_file,
                            alt_text=product.name,
                            is_primary=is_primary,
                            sort_order=i
                        )

                # إذا تم تعيين صورة رئيسية جديدة
                primary_image_id = request.POST.get('primary_image')
                if primary_image_id:
                    # إلغاء تحديد جميع الصور الرئيسية
                    product.images.update(is_primary=False)
                    # تعيين الصورة الجديدة كرئيسية
                    ProductImage.objects.filter(id=primary_image_id).update(is_primary=True)

                # معالجة صفات المنتج
                self.process_product_attributes(request, product)

                # معالجة متغيرات المنتج
                self.process_product_variants(request, product)


                # حفظ منتجات البيع المتقاطع إذا تم إرسالها
                cross_sell_ids = request.POST.getlist('cross_sell_products')
                if cross_sell_ids:
                    product.cross_sell_products.set(Product.objects.filter(id__in=cross_sell_ids))

                # حفظ منتجات البيع التصاعدي إذا تم إرسالها
                upsell_ids = request.POST.getlist('upsell_products')
                if upsell_ids:
                    product.upsell_products.set(Product.objects.filter(id__in=upsell_ids))

                messages.success(request, _('تم حفظ المنتج بنجاح'))

                # تحديد ما إذا كان يجب الاستمرار في التحرير أم العودة إلى صفحة التفاصيل
                if 'save_and_continue' in request.POST:
                    return redirect('dashboard:dashboard_product_edit', product_id=str(product.id))
                else:
                    return redirect('dashboard:dashboard_product_detail', product_id=str(product.id))

            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء حفظ المنتج: {str(e)}')
        else:
            # في حالة وجود أخطاء في النموذج
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form[field].label}: {error}")

        # تحميل البيانات اللازمة للقالب في حالة وجود خطأ
        images = []
        cross_sell_products = []
        upsell_products = []
        product_variants = []
        variants_json = '[]'
        product_attributes = []

        if product:
            images = product.images.all().order_by('sort_order')
            cross_sell_products = product.cross_sell_products.all()
            upsell_products = product.upsell_products.all()
            product_variants = product.variants.all().order_by('sort_order')
            variants_json = self.prepare_variants_json(product_variants)

            # تحميل صفات المنتج
            for attr_value in product.attribute_values.select_related('attribute').all():
                product_attributes.append(attr_value.attribute)

        context = {
            'form': form,
            'product': product,
            'form_title': _('تحديث المنتج') if product_id else _('إنشاء منتج جديد'),
            'images': images,
            'cross_sell_products': cross_sell_products,
            'upsell_products': upsell_products,
            'product_variants': product_variants,
            'variants_json': variants_json,
            'product_attributes': product_attributes,
            'status_choices': Product.STATUS_CHOICES,
            'stock_status_choices': Product.STOCK_STATUS_CHOICES,
            'condition_choices': Product.CONDITION_CHOICES,
        }

        return render(request, 'dashboard/products/product_form.html', context)

    def prepare_variants_json(self, variants):
        """تحويل متغيرات المنتج إلى تنسيق JSON للاستخدام في JavaScript"""
        variants_data = []
        for variant in variants:
            variant_data = {
                'id': variant.id,
                'name': variant.name,
                'sku': variant.sku,
                'attributes': variant.attributes,
                'base_price': float(variant.base_price) if variant.base_price else None,
                'stock_quantity': variant.stock_quantity,
                'is_active': variant.is_active,
                'is_default': variant.is_default,
                'sort_order': variant.sort_order
            }
            variants_data.append(variant_data)
        return json.dumps(variants_data, ensure_ascii=False)

    def process_product_attributes(self, request, product):
        """معالجة صفات المنتج من النموذج"""
        # البحث عن جميع حقول صفات المنتج في النموذج
        attribute_fields = [field for field in request.POST if field.startswith('attribute_')]

        # جمع معرفات الخصائص المحذوفة
        deleted_attributes = []
        if request.POST.get('deleted_attributes'):
            try:
                deleted_attributes = json.loads(request.POST.get('deleted_attributes'))
            except json.JSONDecodeError:
                pass

        # حذف قيم الخصائص المحذوفة
        if deleted_attributes:
            ProductAttributeValue.objects.filter(
                product=product,
                attribute_id__in=deleted_attributes
            ).delete()

        # معالجة الخصائص الجديدة
        new_attribute_fields = [field for field in attribute_fields if field.startswith('attribute_new_')]
        for field in new_attribute_fields:
            try:
                # استخراج معرف الخاصية المؤقت من اسم الحقل (attribute_new_123456789 -> new_123456789)
                temp_id = field.split('_', 1)[1]

                # الحصول على اسم ونوع الخاصية الجديدة
                name = request.POST.get(f'new_attribute_name_{temp_id}', '').strip()
                attr_type = request.POST.get(f'new_attribute_type_{temp_id}', 'text').strip()
                options = request.POST.get(f'new_attribute_options_{temp_id}', '').strip()
                value = request.POST.get(field, '').strip()

                if name and value:
                    # إنشاء خاصية جديدة
                    options_list = []
                    if options and (attr_type == 'select' or attr_type == 'multiselect'):
                        options_list = [opt.strip() for opt in options.split(',') if opt.strip()]

                    # إنشاء سلج فريد للخاصية
                    slug = slugify(name, allow_unicode=True)
                    if ProductAttribute.objects.filter(slug=slug).exists():
                        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

                    # إنشاء الخاصية
                    attribute = ProductAttribute.objects.create(
                        name=name,
                        slug=slug,
                        attribute_type=attr_type,
                        options=options_list if options_list else []
                    )

                    # إنشاء قيمة الخاصية للمنتج
                    ProductAttributeValue.objects.create(
                        product=product,
                        attribute=attribute,
                        value=value
                    )
            except Exception as e:
                # تسجيل الخطأ ومتابعة المعالجة
                print(f"خطأ في معالجة الخاصية الجديدة: {str(e)}")

        # معالجة الخصائص الموجودة
        for field in attribute_fields:
            if field.startswith('attribute_new_'):
                continue  # تمت معالجة الخصائص الجديدة بالفعل

            try:
                # استخراج معرف الصفة من اسم الحقل (attribute_123 -> 123)
                attribute_id = field.split('_')[1]
                if attribute_id in deleted_attributes:
                    continue  # تخطي الخصائص المحذوفة

                value = request.POST.get(field, '').strip()

                if value:  # تخطي القيم الفارغة
                    # التحقق من وجود الصفة
                    try:
                        attribute = ProductAttribute.objects.get(id=attribute_id)

                        # إنشاء أو تحديث قيمة الصفة
                        ProductAttributeValue.objects.update_or_create(
                            product=product,
                            attribute=attribute,
                            defaults={'value': value}
                        )
                    except ProductAttribute.DoesNotExist:
                        pass  # تجاهل الصفات غير الموجودة
            except (ValueError, IndexError):
                pass  # تجاهل الأخطاء في تنسيق اسم الحقل

    def process_product_variants(self, request, product):
        """معالجة متغيرات المنتج من النموذج مع منع تكرار الأسماء"""
        import json

        # الحصول على المتغيرات من النموذج
        variants_json = request.POST.get('product_variants_json', '[]')
        deleted_variants_json = request.POST.get('deleted_variants_json', '[]')

        try:
            # تحويل البيانات من JSON
            variants_data = json.loads(variants_json) if variants_json.strip() else []
            deleted_variants = json.loads(deleted_variants_json) if deleted_variants_json.strip() else []

            # حذف المتغيرات المحددة للحذف
            if deleted_variants:
                ProductVariant.objects.filter(id__in=deleted_variants, product=product).delete()

            # الحصول على المتغيرات الموجودة للمنتج لمنع تكرار الأسماء
            existing_variants = {}
            for variant in ProductVariant.objects.filter(product=product):
                existing_variants[variant.name] = variant.id

            # تحديث/إنشاء المتغيرات
            for variant_data in variants_data:
                variant_id = variant_data.get('id')
                variant_name = variant_data.get('name', '').strip()

                # تخطي المتغيرات بدون اسم
                if not variant_name:
                    continue

                # تخطي المتغيرات ذات المعرفات السالبة (المتغيرات المؤقتة)
                if variant_id and int(variant_id) < 0:
                    variant_id = None

                # منع تكرار الأسماء للمتغيرات الجديدة
                if not variant_id and variant_name in existing_variants:
                    # إضافة رقم للاسم لمنع التكرار
                    base_name = variant_name
                    counter = 1
                    while variant_name in existing_variants:
                        variant_name = f"{base_name} ({counter})"
                        counter += 1

                # الإعدادات الافتراضية للمتغير
                defaults = {
                    'name': variant_name,
                    'sku': variant_data.get('sku', ''),
                    'attributes': variant_data.get('attributes', {}),
                    'is_active': variant_data.get('is_active', True),
                    'is_default': variant_data.get('is_default', False),
                    'sort_order': variant_data.get('sort_order', 0),
                }

                # إضافة السعر إذا تم توفيره
                if 'base_price' in variant_data and variant_data.get('base_price') not in [None, '']:
                    try:
                        defaults['base_price'] = float(variant_data.get('base_price'))
                    except (ValueError, TypeError):
                        pass

                # إضافة كمية المخزون
                if 'stock_quantity' in variant_data and variant_data.get('stock_quantity') not in [None, '']:
                    try:
                        defaults['stock_quantity'] = int(variant_data.get('stock_quantity'))
                    except (ValueError, TypeError):
                        defaults['stock_quantity'] = 0

                # تحديث أو إنشاء المتغير
                if variant_id and int(variant_id) > 0:
                    # تحديث متغير موجود
                    try:
                        variant = ProductVariant.objects.get(id=variant_id, product=product)

                        # منع تكرار الأسماء عند التحديث
                        if variant.name != variant_name and variant_name in existing_variants and existing_variants[
                            variant_name] != variant_id:
                            base_name = variant_name
                            counter = 1
                            while variant_name in existing_variants and existing_variants[variant_name] != variant_id:
                                variant_name = f"{base_name} ({counter})"
                                counter += 1
                            defaults['name'] = variant_name

                        # تحديث المتغير
                        for key, value in defaults.items():
                            setattr(variant, key, value)
                        variant.save()

                        # تحديث القاموس
                        existing_variants[variant_name] = variant.id

                    except ProductVariant.DoesNotExist:
                        # إنشاء متغير جديد
                        defaults['product'] = product
                        new_variant = ProductVariant.objects.create(**defaults)
                        existing_variants[variant_name] = new_variant.id
                else:
                    # إنشاء متغير جديد
                    # إنشاء SKU إذا لم يتم توفيره
                    if not defaults.get('sku'):
                        base_sku = product.sku
                        variant_count = product.variants.count() + 1
                        defaults['sku'] = f"{base_sku}-{variant_count}"

                    # إنشاء المتغير
                    defaults['product'] = product
                    new_variant = ProductVariant.objects.create(**defaults)
                    existing_variants[variant_name] = new_variant.id

            # التأكد من وجود متغير افتراضي واحد فقط
            default_variants = product.variants.filter(is_default=True)
            if default_variants.count() > 1:
                first_default = default_variants.first()
                product.variants.filter(is_default=True).exclude(id=first_default.id).update(is_default=False)

            return True

        except Exception as e:
            # تسجيل الخطأ
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"خطأ في معالجة متغيرات المنتج: {str(e)}")
            print(f"خطأ في معالجة متغيرات المنتج: {str(e)}")
            print(traceback.format_exc())
            raise Exception(f"خطأ في معالجة متغيرات المنتج: {str(e)}")


class ProductDeleteView(DashboardAccessMixin, View):
    """حذف المنتج"""

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)

        try:
            product_name = product.name
            product.delete()
            messages.success(request, f'تم حذف المنتج "{product_name}" بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف المنتج: {str(e)}')

        return redirect('dashboard:dashboard_products')


class ProductBulkActionsView(DashboardAccessMixin, View):
    """عمليات مجمعة على المنتجات"""

    def post(self, request):
        action = request.POST.get('action')
        product_ids = request.POST.getlist('selected_products')

        if not product_ids:
            messages.error(request, 'لم يتم تحديد أي منتجات')
            return redirect('dashboard_products')

        products = Product.objects.filter(id__in=product_ids)
        count = products.count()

        if action == 'activate':
            products.update(is_active=True)
            messages.success(request, f'تم تفعيل {count} منتج بنجاح')

        elif action == 'deactivate':
            products.update(is_active=False)
            messages.success(request, f'تم إلغاء تفعيل {count} منتج بنجاح')

        elif action == 'publish':
            products.update(status='published', published_at=timezone.now())
            messages.success(request, f'تم نشر {count} منتج بنجاح')

        elif action == 'draft':
            products.update(status='draft')
            messages.success(request, f'تم تحويل {count} منتج إلى مسودة بنجاح')

        elif action == 'delete':
            try:
                products.delete()
                messages.success(request, f'تم حذف {count} منتج بنجاح')
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء حذف المنتجات: {str(e)}')

        elif action == 'update_stock':
            # هذا سيعيدنا إلى صفحة تحديث المخزون للمنتجات المحددة
            product_ids_str = ','.join(product_ids)
            return redirect(f'dashboard_update_stock?products={product_ids_str}')

        return redirect('dashboard_products')


# ========================= إدارة الفئات =========================

class CategoryListView(DashboardAccessMixin, View):
    """عرض قائمة الفئات"""

    def get(self, request):
        # استرجاع معلمة البحث
        query = request.GET.get('q', '')

        # تحديد إذا كان المستخدم يستخدم العرض الشجري أو الشبكي
        view_mode = request.GET.get('view_mode', 'tree')

        # تعريف context أولاً
        context = {
            'query': query,
            'view_mode': view_mode,
        }

        if query:
            # في حالة البحث
            from django.db.models import Q

            if view_mode == 'grid':
                # للعرض الشبكي، نعرض فقط الفئات التي تطابق معايير البحث
                categories = Category.objects.filter(
                    Q(name__icontains=query) |
                    Q(name_en__icontains=query) |
                    Q(description__icontains=query)
                ).distinct()
            else:
                # للعرض الشجري، نعرض الفئات التي تطابق معايير البحث مع فئاتها الأم
                matched_categories = Category.objects.filter(
                    Q(name__icontains=query) |
                    Q(name_en__icontains=query) |
                    Q(description__icontains=query)
                ).distinct()

                # إضافة علامة خاصة للفئات المطابقة للبحث
                for category in matched_categories:
                    category.matched_by_search = True

                # استرجاع الفئات الجذرية مع الفئات الفرعية المطابقة
                categories = Category.objects.filter(
                    level=0  # فقط الفئات الجذرية
                ).distinct()

                # إعداد قائمة بجميع الفئات المطابقة ومعرفاتها
                matched_ids = list(matched_categories.values_list('id', flat=True))

                # الآن يمكننا استخدام context بأمان
                context['matched_categories'] = matched_categories
                context['matched_ids'] = matched_ids
        else:
            # استرجاع جميع الفئات مرتبة حسب الهيكل الشجري
            categories = Category.objects.all().order_by('tree_id', 'lft')

        # الإحصائيات
        stats = {
            'total': Category.objects.count(),
            'active': Category.objects.filter(is_active=True).count(),
            'featured': Category.objects.filter(is_featured=True).count(),
            'root_categories': Category.objects.filter(level=0).count(),
        }

        # تحديث context بباقي البيانات
        context.update({
            'categories': categories,
            'stats': stats,
        })

        return render(request, 'dashboard/products/category_list.html', context)


class CategoryFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث الفئة"""

    def get(self, request, category_id=None):
        if category_id:
            category = get_object_or_404(Category, id=category_id)
            form_title = 'تحديث الفئة'
        else:
            category = None
            form_title = 'إنشاء فئة جديدة'

        # الحصول على قائمة الفئات للاختيار كأب
        parent_categories = Category.objects.exclude(id=category_id if category_id else None)

        context = {
            'category': category,
            'form_title': form_title,
            'parent_categories': parent_categories,
        }

        return render(request, 'dashboard/products/category_form.html', context)

    def post(self, request, category_id=None):
        """معالجة طلب إنشاء أو تحديث الفئة"""
        # استرجاع الفئة إذا كنا في وضع التحرير
        if category_id:
            category = get_object_or_404(Category, id=category_id)
            form_title = 'تحديث الفئة'
        else:
            category = None
            form_title = 'إنشاء فئة جديدة'

        # جمع البيانات من النموذج
        form_data = request.POST.copy()
        form_files = request.FILES.copy()

        # قائمة للأخطاء
        errors = []

        # التحقق من الحقول المطلوبة
        name = form_data.get('name', '').strip()
        if not name:
            errors.append("اسم الفئة مطلوب")
        elif len(name) < 2:
            errors.append("اسم الفئة يجب أن يكون على الأقل حرفين")

        # طباعة بيانات النموذج للتشخيص
        print("بيانات النموذج المستلمة:")
        for key, value in form_data.items():
            print(f"{key}: {value}")

        # التحقق من الوصف إذا تم إدخاله
        description = form_data.get('description', '').strip()
        if description and len(description) < 10:
            errors.append("الوصف يجب أن يكون على الأقل 10 أحرف أو تركه فارغًا")

        description_en = form_data.get('description_en', '').strip()
        if description_en and len(description_en) < 10:
            errors.append("الوصف الإنجليزي يجب أن يكون على الأقل 10 أحرف أو تركه فارغًا")

        # التحقق من تنسيق اللون إذا تم إدخاله
        color = form_data.get('color', '').strip()
        if color and not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            errors.append("اللون يجب أن يكون بصيغة سداسية عشرية صحيحة (مثل #FF5733)")

        # التحقق من الأيقونة إذا تم إدخالها
        icon = form_data.get('icon', '').strip()
        if icon and not re.match(r'^[a-zA-Z\s\-]+$', icon):
            errors.append("صيغة الأيقونة غير صحيحة")

        # التحقق من نسبة العمولة إذا تم إدخالها
        commission_rate_str = form_data.get('commission_rate', '').strip()
        if commission_rate_str:
            try:
                commission_rate = Decimal(commission_rate_str.replace(',', '.'))
                if commission_rate < 0 or commission_rate > 100:
                    errors.append("نسبة العمولة يجب أن تكون بين 0 و 100")
            except (ValueError, InvalidOperation):
                errors.append("صيغة نسبة العمولة غير صحيحة")

        # إذا كانت هناك أخطاء، نعيد عرض النموذج مع رسائل الخطأ
        if errors:
            for error in errors:
                messages.error(request, error)

            # الحصول على قائمة الفئات للاختيار كأب
            parent_categories = Category.objects.exclude(id=category_id if category_id else None)

            context = {
                'category': category,
                'form_title': form_title,
                'parent_categories': parent_categories,
                'form_data': form_data,
                'form_files': form_files,
            }

            return render(request, 'dashboard/products/category_form.html', context)

        # إذا لم تكن هناك أخطاء، نستمر في حفظ الفئة
        try:
            # استخراج البيانات
            name_en = form_data.get('name_en', '').strip()
            parent_id = form_data.get('parent') or None
            description = form_data.get('description', '').strip()
            description_en = form_data.get('description_en', '').strip()
            sort_order_str = form_data.get('sort_order', '0').strip()
            sort_order = int(sort_order_str) if sort_order_str else 0
            icon = form_data.get('icon', '').strip()
            color = form_data.get('color', '').strip()

            # البيانات البوليانية
            is_active = 'is_active' in form_data
            is_featured = 'is_featured' in form_data
            show_in_menu = 'show_in_menu' in form_data
            show_prices = 'show_prices' in form_data

            # معالجة نسبة العمولة
            commission_rate_str = form_data.get('commission_rate', '0').strip()
            commission_rate = Decimal(commission_rate_str.replace(',', '.')) if commission_rate_str else Decimal('0')

            # معالجة محتوى JSON
            content_blocks = {}
            content_blocks_str = form_data.get('content_blocks', '{}').strip()
            if content_blocks_str:
                try:
                    content_blocks = json.loads(content_blocks_str)
                except json.JSONDecodeError:
                    messages.warning(request, 'حدث خطأ في معالجة بيانات كتل المحتوى')

            # معالجة الصور
            image = form_files.get('image')
            banner_image = form_files.get('banner_image')

            # إنشاء أو تحديث الفئة
            if category_id:
                # تحديث فئة موجودة
                category.name = name
                category.name_en = name_en
                category.parent_id = parent_id
                category.description = description
                category.description_en = description_en
                category.sort_order = sort_order
                category.icon = icon
                category.color = color
                category.is_active = is_active
                category.is_featured = is_featured
                category.show_in_menu = show_in_menu
                category.show_prices = show_prices
                category.commission_rate = commission_rate
                category.content_blocks = content_blocks

                if image:
                    category.image = image

                if banner_image:
                    category.banner_image = banner_image

                category.save()
                messages.success(request, 'تم تحديث الفئة بنجاح')
            else:
                # إنشاء سلج من الاسم
                slug = slugify(name, allow_unicode=True)
                if Category.objects.filter(slug=slug).exists():
                    slug = f"{slug}-{uuid.uuid4().hex[:6]}"

                # إنشاء فئة جديدة
                try:
                    # محاولة إنشاء الفئة مباشرة
                    category = Category()
                    category.name = name
                    category.name_en = name_en
                    category.slug = slug
                    category.parent_id = parent_id
                    category.description = description
                    category.description_en = description_en
                    category.sort_order = sort_order
                    category.icon = icon
                    category.color = color
                    category.is_active = is_active
                    category.is_featured = is_featured
                    category.show_in_menu = show_in_menu
                    category.show_prices = show_prices
                    category.commission_rate = commission_rate
                    category.content_blocks = content_blocks
                    category.created_by = request.user

                    if image:
                        category.image = image
                    if banner_image:
                        category.banner_image = banner_image

                    # حفظ الفئة
                    category.save()

                    # طباعة رسالة تأكيد في سجل التطبيق
                    print(f"تم إنشاء الفئة بنجاح: {category.id} - {category.name}")

                except Exception as creation_error:
                    # طباعة الخطأ الدقيق في سجل التطبيق
                    print(f"خطأ في إنشاء الفئة: {str(creation_error)}")
                    raise

                messages.success(request, 'تم إنشاء الفئة بنجاح')

            # تحديد ما إذا كان يجب الاستمرار في التحرير أم العودة إلى صفحة القائمة
            if 'save_and_continue' in form_data:
                return redirect('dashboard:dashboard_category_edit', category_id=str(category.id))
            else:
                return redirect('dashboard:dashboard_categories')

        except Exception as e:
            # طباعة الخطأ الدقيق في سجل التطبيق
            print(f"خطأ عام أثناء حفظ الفئة: {str(e)}")
            messages.error(request, f'حدث خطأ أثناء حفظ الفئة: {str(e)}')

            # الحصول على قائمة الفئات للاختيار كأب
            parent_categories = Category.objects.exclude(id=category_id if category_id else None)

            context = {
                'category': category,
                'form_title': form_title,
                'parent_categories': parent_categories,
                'form_data': form_data,
                'form_files': form_files,
            }

            return render(request, 'dashboard/products/category_form.html', context)


class CategoryDeleteView(DashboardAccessMixin, View):
    """حذف الفئة"""

    def post(self, request, category_id):
        category = get_object_or_404(Category, id=category_id)

        # التحقق من وجود منتجات في هذه الفئة
        products_count = category.products.count()
        if products_count > 0:
            messages.error(request, f'لا يمكن حذف الفئة لأنها تحتوي على {products_count} منتج')
            return redirect('dashboard:dashboard_categories')

        # التحقق من وجود فئات فرعية
        if category.children.exists():
            messages.error(request, 'لا يمكن حذف الفئة لأنها تحتوي على فئات فرعية')
            return redirect('dashboard:dashboard_categories')

        try:
            category_name = category.name
            category.delete()
            messages.success(request, f'تم حذف الفئة "{category_name}" بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف الفئة: {str(e)}')

        return redirect('dashboard:dashboard_categories')


# ========================= إدارة العلامات التجارية =========================

class BrandListView(DashboardAccessMixin, View):
    """عرض قائمة العلامات التجارية"""

    def get(self, request):
        # البحث
        query = request.GET.get('q', '')

        # قائمة العلامات التجارية
        brands = Brand.objects.all().order_by('name')

        # تطبيق البحث
        if query:
            brands = brands.filter(
                Q(name__icontains=query) |
                Q(name_en__icontains=query) |
                Q(country__icontains=query)
            )

        # التصفح الجزئي
        paginator = Paginator(brands, 20)  # 20 علامة تجارية في كل صفحة
        page = request.GET.get('page', 1)
        brands_page = paginator.get_page(page)

        # الإحصائيات
        stats = {
            'total': Brand.objects.count(),
            'featured': Brand.objects.filter(is_featured=True).count(),
            'verified': Brand.objects.filter(is_verified=True).count(),
        }

        context = {
            'brands': brands_page,
            'query': query,
            'stats': stats,
        }

        # إذا كان الطلب AJAX، نعيد جزء الجدول فقط
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('dashboard/products/brands_table.html', context, request)
            return JsonResponse({
                'html': html,
                'has_next': brands_page.has_next(),
                'has_prev': brands_page.has_previous(),
                'page': brands_page.number,
                'pages': paginator.num_pages,
                'total': paginator.count
            })

        return render(request, 'dashboard/products/brand_list.html', context)


class BrandFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث العلامة التجارية"""

    def get(self, request, brand_id=None):
        if brand_id:
            brand = get_object_or_404(Brand, id=brand_id)
            form_title = 'تحديث العلامة التجارية'
        else:
            brand = None
            form_title = 'إنشاء علامة تجارية جديدة'

        context = {
            'brand': brand,
            'form_title': form_title,
        }

        return render(request, 'dashboard/products/brand_form.html', context)

    def post(self, request, brand_id=None):
        # جمع البيانات من النموذج
        name = request.POST.get('name')
        name_en = request.POST.get('name_en', '')
        description = request.POST.get('description', '')
        country = request.POST.get('country', '')
        city = request.POST.get('city', '')
        website = request.POST.get('website', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        is_verified = request.POST.get('is_verified') == 'on'
        sort_order = request.POST.get('sort_order', 0)

        # الحقول SEO
        meta_title = request.POST.get('meta_title', '')
        meta_description = request.POST.get('meta_description', '')
        meta_keywords = request.POST.get('meta_keywords', '')

        # روابط التواصل الاجتماعي
        social_links = {}
        social_platforms = ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube']
        for platform in social_platforms:
            social_links[platform] = request.POST.get(f'social_{platform}', '')

        # التحقق من البيانات المطلوبة
        if not name:
            messages.error(request, 'اسم العلامة التجارية مطلوب')
            return redirect(request.path)

        # إنشاء سلج (slug) من الاسم
        slug = request.POST.get('slug') or slugify(name, allow_unicode=True)

        try:
            if brand_id:
                # تحديث علامة تجارية موجودة
                brand = get_object_or_404(Brand, id=brand_id)

                # تحديث البيانات
                brand.name = name
                brand.name_en = name_en
                brand.description = description
                brand.country = country
                brand.city = city
                brand.website = website
                brand.email = email
                brand.phone = phone
                brand.is_active = is_active
                brand.is_featured = is_featured
                brand.is_verified = is_verified
                brand.sort_order = sort_order
                brand.meta_title = meta_title
                brand.meta_description = meta_description
                brand.meta_keywords = meta_keywords
                brand.social_links = social_links

                # تحديث السلج إذا تغير
                if slug != brand.slug:
                    # التحقق من فريدية السلج
                    if Brand.objects.filter(slug=slug).exclude(id=brand_id).exists():
                        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
                    brand.slug = slug

                brand.save()
                messages.success(request, 'تم تحديث العلامة التجارية بنجاح')
            else:
                # التحقق من فريدية السلج
                if Brand.objects.filter(slug=slug).exists():
                    slug = f"{slug}-{uuid.uuid4().hex[:6]}"

                # إنشاء علامة تجارية جديدة
                brand = Brand.objects.create(
                    name=name,
                    name_en=name_en,
                    slug=slug,
                    description=description,
                    country=country,
                    city=city,
                    website=website,
                    email=email,
                    phone=phone,
                    is_active=is_active,
                    is_featured=is_featured,
                    is_verified=is_verified,
                    sort_order=sort_order,
                    meta_title=meta_title,
                    meta_description=meta_description,
                    meta_keywords=meta_keywords,
                    social_links=social_links,
                    created_by=request.user,
                )
                messages.success(request, 'تم إنشاء العلامة التجارية بنجاح')

            # معالجة الصور المرفوعة
            logo = request.FILES.get('logo')
            if logo:
                brand.logo = logo

            banner_image = request.FILES.get('banner_image')
            if banner_image:
                brand.banner_image = banner_image

            # حفظ التغييرات على الصور
            if logo or banner_image:
                brand.save()

            return redirect('dashboard_brands')

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ العلامة التجارية: {str(e)}')
            return redirect(request.path)


class BrandDeleteView(DashboardAccessMixin, View):
    """حذف العلامة التجارية"""

    def post(self, request, brand_id):
        brand = get_object_or_404(Brand, id=brand_id)

        # التحقق من وجود منتجات لهذه العلامة التجارية
        products_count = brand.products.count()
        if products_count > 0:
            messages.error(request, f'لا يمكن حذف العلامة التجارية لأنها مرتبطة بـ {products_count} منتج')
            return redirect('dashboard_brands')

        try:
            brand_name = brand.name
            brand.delete()
            messages.success(request, f'تم حذف العلامة التجارية "{brand_name}" بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف العلامة التجارية: {str(e)}')

        return redirect('dashboard_brands')


# ========================= إدارة الخصومات =========================

class DiscountListView(DashboardAccessMixin, View):
    """عرض قائمة الخصومات"""

    def get(self, request):
        # البحث والتصفية
        query = request.GET.get('q', '')
        type_filter = request.GET.get('type', '')
        status_filter = request.GET.get('status', '')

        # قائمة الخصومات
        discounts = ProductDiscount.objects.all().order_by('-priority', '-start_date')

        # تطبيق البحث
        if query:
            discounts = discounts.filter(
                Q(name__icontains=query) |
                Q(code__icontains=query) |
                Q(description__icontains=query)
            )

        # تطبيق التصفية
        if type_filter:
            discounts = discounts.filter(discount_type=type_filter)

        if status_filter == 'active':
            discounts = discounts.filter(is_active=True)
        elif status_filter == 'inactive':
            discounts = discounts.filter(is_active=False)
        elif status_filter == 'expired':
            discounts = discounts.filter(end_date__lt=timezone.now())
        elif status_filter == 'upcoming':
            discounts = discounts.filter(start_date__gt=timezone.now())

        # التصفح الجزئي
        paginator = Paginator(discounts, 20)  # 20 خصم في كل صفحة
        page = request.GET.get('page', 1)
        discounts_page = paginator.get_page(page)

        # الإحصائيات
        stats = {
            'total': ProductDiscount.objects.count(),
            'active': ProductDiscount.objects.filter(is_active=True).count(),
            'expired': ProductDiscount.objects.filter(end_date__lt=timezone.now()).count(),
        }

        context = {
            'discounts': discounts_page,
            'query': query,
            'type_filter': type_filter,
            'status_filter': status_filter,
            'stats': stats,
            'discount_types': ProductDiscount.DISCOUNT_TYPE_CHOICES,
        }

        # إذا كان الطلب AJAX، نعيد جزء الجدول فقط
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('dashboard/products/discounts_table.html', context, request)
            return JsonResponse({
                'html': html,
                'has_next': discounts_page.has_next(),
                'has_prev': discounts_page.has_previous(),
                'page': discounts_page.number,
                'pages': paginator.num_pages,
                'total': paginator.count
            })

        return render(request, 'dashboard/products/discount_list.html', context)


class DiscountFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث الخصم"""

    def get(self, request, discount_id=None):
        if discount_id:
            discount = get_object_or_404(ProductDiscount, id=discount_id)
            form_title = 'تحديث الخصم'
            selected_products = discount.products.all()
        else:
            discount = None
            form_title = 'إنشاء خصم جديد'
            selected_products = []

        # جلب الفئات والمنتجات
        categories = Category.objects.filter(is_active=True)
        products = Product.objects.filter(is_active=True, status='published').order_by('name')[
                   :100]  # عرض أول 100 منتج فقط للاختيار

        context = {
            'discount': discount,
            'form_title': form_title,
            'selected_products': selected_products,
            'categories': categories,
            'products': products,
            'discount_types': ProductDiscount.DISCOUNT_TYPE_CHOICES,
            'application_types': ProductDiscount.APPLICATION_TYPE_CHOICES,
        }

        return render(request, 'dashboard/products/discount_form.html', context)

    def post(self, request, discount_id=None):
        # جمع البيانات من النموذج
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        code = request.POST.get('code', '')
        discount_type = request.POST.get('discount_type')
        value = request.POST.get('value')
        max_discount_amount = request.POST.get('max_discount_amount') or None

        application_type = request.POST.get('application_type')
        category_id = request.POST.get('category') or None
        product_ids = request.POST.getlist('products')

        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') or None

        min_purchase_amount = request.POST.get('min_purchase_amount') or None
        min_quantity = request.POST.get('min_quantity') or None
        max_uses = request.POST.get('max_uses') or None
        max_uses_per_user = request.POST.get('max_uses_per_user') or None

        buy_quantity = request.POST.get('buy_quantity') or None
        get_quantity = request.POST.get('get_quantity') or None
        get_discount_percentage = request.POST.get('get_discount_percentage', 100) or 100

        is_active = request.POST.get('is_active') == 'on'
        is_stackable = request.POST.get('is_stackable') == 'on'
        requires_coupon_code = request.POST.get('requires_coupon_code') == 'on'
        priority = request.POST.get('priority', 0)

        # التحقق من البيانات المطلوبة
        if not name or not discount_type or not value:
            messages.error(request, 'الرجاء ملء جميع الحقول المطلوبة: الاسم، نوع الخصم، قيمة الخصم')
            return redirect(request.path)

        # تحويل التواريخ من نص إلى كائنات datetime
        import datetime
        try:
            start_date = timezone.make_aware(datetime.datetime.strptime(start_date, '%Y-%m-%dT%H:%M'))
            if end_date:
                end_date = timezone.make_aware(datetime.datetime.strptime(end_date, '%Y-%m-%dT%H:%M'))
        except ValueError:
            messages.error(request, 'صيغة التاريخ غير صحيحة')
            return redirect(request.path)

        try:
            if discount_id:
                # تحديث خصم موجود
                discount = get_object_or_404(ProductDiscount, id=discount_id)

                # تحديث البيانات
                discount.name = name
                discount.description = description
                discount.code = code
                discount.discount_type = discount_type
                discount.value = value
                discount.max_discount_amount = max_discount_amount
                discount.application_type = application_type
                discount.category_id = category_id
                discount.start_date = start_date
                discount.end_date = end_date
                discount.min_purchase_amount = min_purchase_amount
                discount.min_quantity = min_quantity
                discount.max_uses = max_uses
                discount.max_uses_per_user = max_uses_per_user
                discount.buy_quantity = buy_quantity
                discount.get_quantity = get_quantity
                discount.get_discount_percentage = get_discount_percentage
                discount.is_active = is_active
                discount.is_stackable = is_stackable
                discount.requires_coupon_code = requires_coupon_code
                discount.priority = priority

                discount.save()
                messages.success(request, 'تم تحديث الخصم بنجاح')
            else:
                # إنشاء خصم جديد
                discount = ProductDiscount.objects.create(
                    name=name,
                    description=description,
                    code=code,
                    discount_type=discount_type,
                    value=value,
                    max_discount_amount=max_discount_amount,
                    application_type=application_type,
                    category_id=category_id,
                    start_date=start_date,
                    end_date=end_date,
                    min_purchase_amount=min_purchase_amount,
                    min_quantity=min_quantity,
                    max_uses=max_uses,
                    max_uses_per_user=max_uses_per_user,
                    buy_quantity=buy_quantity,
                    get_quantity=get_quantity,
                    get_discount_percentage=get_discount_percentage,
                    is_active=is_active,
                    is_stackable=is_stackable,
                    requires_coupon_code=requires_coupon_code,
                    priority=priority,
                    created_by=request.user,
                )
                messages.success(request, 'تم إنشاء الخصم بنجاح')

            # تحديث المنتجات المرتبطة
            if product_ids and application_type == 'specific_products':
                discount.products.set(Product.objects.filter(id__in=product_ids))
            else:
                discount.products.clear()

            return redirect('dashboard_discounts')

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ الخصم: {str(e)}')
            return redirect(request.path)


class DiscountDeleteView(DashboardAccessMixin, View):
    """حذف الخصم"""

    def post(self, request, discount_id):
        discount = get_object_or_404(ProductDiscount, id=discount_id)

        try:
            discount_name = discount.name
            discount.delete()
            messages.success(request, f'تم حذف الخصم "{discount_name}" بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف الخصم: {str(e)}')

        return redirect('dashboard_discounts')


# ========================= إدارة التقييمات =========================

class ReviewListView(DashboardAccessMixin, View):
    """عرض قائمة تقييمات المنتجات"""

    def get(self, request):
        # البحث والتصفية
        query = request.GET.get('q', '')
        rating_filter = request.GET.get('rating', '')
        status_filter = request.GET.get('status', '')

        # قائمة التقييمات
        reviews = ProductReview.objects.select_related('user', 'product').order_by('-created_at')

        # تطبيق البحث
        if query:
            reviews = reviews.filter(
                Q(product__name__icontains=query) |
                Q(user__username__icontains=query) |
                Q(title__icontains=query) |
                Q(content__icontains=query)
            )

        # تطبيق التصفية
        if rating_filter:
            reviews = reviews.filter(rating=rating_filter)

        if status_filter == 'approved':
            reviews = reviews.filter(is_approved=True)
        elif status_filter == 'pending':
            reviews = reviews.filter(is_approved=False)
        elif status_filter == 'featured':
            reviews = reviews.filter(is_featured=True)
        elif status_filter == 'reported':
            reviews = reviews.filter(report_count__gt=0)

        # التصفح الجزئي
        paginator = Paginator(reviews, 20)  # 20 تقييم في كل صفحة
        page = request.GET.get('page', 1)
        reviews_page = paginator.get_page(page)

        # الإحصائيات
        stats = {
            'total': ProductReview.objects.count(),
            'approved': ProductReview.objects.filter(is_approved=True).count(),
            'pending': ProductReview.objects.filter(is_approved=False).count(),
            'reported': ProductReview.objects.filter(report_count__gt=0).count(),
        }

        context = {
            'reviews': reviews_page,
            'query': query,
            'rating_filter': rating_filter,
            'status_filter': status_filter,
            'stats': stats,
        }

        # إذا كان الطلب AJAX، نعيد جزء الجدول فقط
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('dashboard/products/reviews_table.html', context, request)
            return JsonResponse({
                'html': html,
                'has_next': reviews_page.has_next(),
                'has_prev': reviews_page.has_previous(),
                'page': reviews_page.number,
                'pages': paginator.num_pages,
                'total': paginator.count
            })

        return render(request, 'dashboard/products/review_list.html', context)


class ReviewDetailView(DashboardAccessMixin, View):
    """عرض تفاصيل التقييم"""

    def get(self, request, review_id):
        review = get_object_or_404(ProductReview, id=review_id)

        # جلب الصور المرتبطة بالتقييم
        images = review.images.all()

        context = {
            'review': review,
            'images': images,
            'product': review.product,
        }

        return render(request, 'dashboard/products/review_detail.html', context)


@require_POST
def review_action(request, review_id):
    """إجراءات على التقييم (موافقة، رفض، تمييز)"""
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'غير مصرح لك بهذا الإجراء'}, status=403)

    review = get_object_or_404(ProductReview, id=review_id)
    action = request.POST.get('action')

    if action == 'approve':
        review.is_approved = True
        review.approved_at = timezone.now()
        review.approved_by = request.user
        review.save()
        return JsonResponse({'success': True, 'message': 'تمت الموافقة على التقييم بنجاح'})

    elif action == 'reject':
        review.is_approved = False
        review.save()
        return JsonResponse({'success': True, 'message': 'تم رفض التقييم بنجاح'})

    elif action == 'feature':
        review.is_featured = True
        review.save()
        return JsonResponse({'success': True, 'message': 'تم تمييز التقييم بنجاح'})

    elif action == 'unfeature':
        review.is_featured = False
        review.save()
        return JsonResponse({'success': True, 'message': 'تم إلغاء تمييز التقييم بنجاح'})

    elif action == 'delete':
        review.delete()
        return JsonResponse({'success': True, 'message': 'تم حذف التقييم بنجاح'})

    return JsonResponse({'success': False, 'message': 'إجراء غير صالح'}, status=400)


# ========================= إدارة الوسوم =========================

class TagListView(DashboardAccessMixin, View):
    """عرض قائمة الوسوم"""

    def get(self, request):
        # البحث
        query = request.GET.get('q', '')

        # قائمة الوسوم
        tags = Tag.objects.all().order_by('-usage_count', 'name')

        # تطبيق البحث
        if query:
            tags = tags.filter(name__icontains=query)

        # الإحصائيات
        stats = {
            'total': Tag.objects.count(),
            'featured': Tag.objects.filter(is_featured=True).count(),
            'most_used': Tag.objects.order_by('-usage_count').first(),
        }

        context = {
            'tags': tags,
            'query': query,
            'stats': stats,
        }

        return render(request, 'dashboard/products/tag_list.html', context)


class TagFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث الوسم"""

    def get(self, request, tag_id=None):
        if tag_id:
            tag = get_object_or_404(Tag, id=tag_id)
            form_title = 'تحديث الوسم'
        else:
            tag = None
            form_title = 'إنشاء وسم جديد'

        context = {
            'tag': tag,
            'form_title': form_title,
        }

        return render(request, 'dashboard/products/tag_form.html', context)

    def post(self, request, tag_id=None):
        # جمع البيانات من النموذج
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        color = request.POST.get('color', '')
        icon = request.POST.get('icon', '')
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'

        # التحقق من البيانات المطلوبة
        if not name:
            messages.error(request, 'اسم الوسم مطلوب')
            return redirect(request.path)

        # إنشاء سلج (slug) من الاسم
        slug = slugify(name, allow_unicode=True)

        try:
            if tag_id:
                # تحديث وسم موجود
                tag = get_object_or_404(Tag, id=tag_id)

                # تحديث البيانات
                tag.name = name
                tag.description = description
                tag.color = color
                tag.icon = icon
                tag.is_active = is_active
                tag.is_featured = is_featured

                # تحديث السلج إذا تغير الاسم
                if tag.name != name:
                    # التحقق من فريدية السلج
                    if Tag.objects.filter(slug=slug).exclude(id=tag_id).exists():
                        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
                    tag.slug = slug

                tag.save()
                messages.success(request, 'تم تحديث الوسم بنجاح')
            else:
                # التحقق من فريدية السلج
                if Tag.objects.filter(slug=slug).exists():
                    slug = f"{slug}-{uuid.uuid4().hex[:6]}"

                # إنشاء وسم جديد
                tag = Tag.objects.create(
                    name=name,
                    slug=slug,
                    description=description,
                    color=color,
                    icon=icon,
                    is_active=is_active,
                    is_featured=is_featured,
                )
                messages.success(request, 'تم إنشاء الوسم بنجاح')

            return redirect('dashboard_tags')

        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ الوسم: {str(e)}')
            return redirect(request.path)


class TagDeleteView(DashboardAccessMixin, View):
    """حذف الوسم"""

    def post(self, request, tag_id):
        tag = get_object_or_404(Tag, id=tag_id)

        # التحقق من وجود منتجات مرتبطة بهذا الوسم
        products_count = tag.products.count()
        if products_count > 0:
            messages.error(request, f'لا يمكن حذف الوسم لأنه مرتبط بـ {products_count} منتج')
            return redirect('dashboard_tags')

        try:
            tag_name = tag.name
            tag.delete()
            messages.success(request, f'تم حذف الوسم "{tag_name}" بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف الوسم: {str(e)}')

        return redirect('dashboard_tags')


#======================
class ProductVariantFormView(DashboardAccessMixin, View):
    """عرض إنشاء وتحديث متغيرات المنتج"""

    def get(self, request, product_id, variant_id=None):
        """عرض نموذج إنشاء أو تحديث متغير المنتج"""
        product = get_object_or_404(Product, id=product_id)

        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
            form = ProductVariantForm(instance=variant, product=product)
            form_title = _('تعديل متغير المنتج')
        else:
            variant = None
            form = ProductVariantForm(product=product)
            form_title = _('إضافة متغير جديد للمنتج')

        context = {
            'form': form,
            'product': product,
            'variant': variant,
            'form_title': form_title,
        }

        return render(request, 'dashboard/products/product_variant_form.html', context)

    def post(self, request, product_id, variant_id=None):
        """معالجة نموذج إنشاء أو تحديث متغير المنتج"""
        product = get_object_or_404(Product, id=product_id)

        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
            form = ProductVariantForm(request.POST, instance=variant, product=product)
        else:
            variant = None
            form = ProductVariantForm(request.POST, product=product)

        if form.is_valid():
            try:
                variant = form.save(commit=False)
                variant.product = product

                # تحديث SKU إذا لم يتم توفيره
                if not variant.sku:
                    # توليد SKU للمتغير اعتمادًا على SKU المنتج الأساسي
                    base_sku = product.sku
                    variant_count = product.variants.count() + 1
                    variant.sku = f"{base_sku}-{variant_count}"

                variant.save()

                messages.success(request, _('تم حفظ متغير المنتج بنجاح'))
                return redirect('dashboard:dashboard_product_detail', product_id=product.id)

            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء حفظ متغير المنتج: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form[field].label}: {error}")

        context = {
            'form': form,
            'product': product,
            'variant': variant,
            'form_title': _('تعديل متغير المنتج') if variant_id else _('إضافة متغير جديد للمنتج'),
        }

        return render(request, 'dashboard/products/product_variant_form.html', context)


class ProductVariantDeleteView(DashboardAccessMixin, View):
    """حذف متغير المنتج"""

    def post(self, request, product_id, variant_id):
        product = get_object_or_404(Product, id=product_id)
        variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

        try:
            variant_name = variant.name
            variant.delete()
            messages.success(request, f'تم حذف متغير المنتج "{variant_name}" بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف متغير المنتج: {str(e)}')

        return redirect('dashboard:dashboard_product_detail', product_id=product.id)


class ProductVariantBulkActionsView(DashboardAccessMixin, View):
    """عمليات جماعية على متغيرات المنتج"""

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        action = request.POST.get('action')
        variant_ids = request.POST.getlist('selected_variants')

        if not variant_ids:
            messages.error(request, 'لم يتم تحديد أي متغيرات للمنتج')
            return redirect('dashboard:dashboard_product_detail', product_id=product.id)

        variants = ProductVariant.objects.filter(id__in=variant_ids, product=product)
        count = variants.count()

        if action == 'activate':
            variants.update(is_active=True)
            messages.success(request, f'تم تفعيل {count} متغير بنجاح')

        elif action == 'deactivate':
            variants.update(is_active=False)
            messages.success(request, f'تم إلغاء تفعيل {count} متغير بنجاح')

        elif action == 'delete':
            try:
                variants.delete()
                messages.success(request, f'تم حذف {count} متغير بنجاح')
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء حذف المتغيرات: {str(e)}')

        elif action == 'update_stock':
            # تحويل لصفحة تحديث المخزون للمتغيرات المحددة
            variant_ids_str = ','.join(variant_ids)
            return redirect(f'dashboard_update_variant_stock?variants={variant_ids_str}')

        return redirect('dashboard:dashboard_product_detail', product_id=product.id)


@login_required
@permission_required('products.add_product')
def duplicate_product(request, product_id):
    """نسخ منتج موجود مع الاحتفاظ بمعظم بياناته"""
    # الحصول على المنتج الأصلي
    original_product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        # إنشاء نسخة جديدة من المنتج
        new_product = Product()

        # نسخ الحقول الأساسية
        for field in original_product._meta.fields:
            if field.name not in ['id', 'pk', 'created_at', 'updated_at', 'published_at', 'slug']:
                setattr(new_product, field.name, getattr(original_product, field.name))

        # تعديل البيانات التي يجب تغييرها
        new_product.name = f"{original_product.name} (copy)"  # استخدام كلمة إنجليزية لتجنب مشاكل الـ slug
        new_product.sku = f"{original_product.sku}_copy" if original_product.sku else ""
        new_product.slug = None  # سيتم إنشاء slug جديد تلقائياً
        new_product.sales_count = 0
        new_product.views_count = 0
        new_product.wishlist_count = 0
        new_product.status = 'draft'
        new_product.published_at = None
        new_product.created_by = request.user

        # نسخ البيانات المخزنة في حقول JSON
        if hasattr(original_product, 'features_json') and original_product.features_json:
            new_product.features_json = original_product.features_json

        if hasattr(original_product, 'specifications_json') and original_product.specifications_json:
            new_product.specifications_json = original_product.specifications_json

        # حفظ المنتج الجديد
        new_product.save()

        # نسخ العلاقات المتعددة (ManyToMany)
        if hasattr(original_product, 'tags'):
            new_product.tags.set(original_product.tags.all())

        if hasattr(original_product, 'related_products'):
            new_product.related_products.set(original_product.related_products.all())

        # نسخ الصور مع محتوى الملفات الفعلية
        from django.core.files.base import ContentFile
        import os

        for image in original_product.images.all():
            # فتح الملف الأصلي وقراءة محتواه
            image_path = image.image.path if os.path.exists(image.image.path) else None

            if image_path:
                # إنشاء صورة جديدة مع نسخ الملف
                new_image = ProductImage(
                    product=new_product,
                    alt_text=image.alt_text,
                    is_primary=image.is_primary,
                    sort_order=image.sort_order
                )

                # نسخ محتوى الملف
                with open(image_path, 'rb') as f:
                    file_content = f.read()
                    file_name = os.path.basename(image.image.name)
                    new_image.image.save(file_name, ContentFile(file_content), save=False)

                new_image.save()

        # نسخ الخصائص والقيم
        for attr_value in original_product.attribute_values.all():
            new_attr_value = ProductAttributeValue(
                product=new_product,
                attribute=attr_value.attribute,
                value=attr_value.value
            )
            new_attr_value.save()

        # نسخ متغيرات المنتج بكامل تفاصيلها
        for variant in original_product.variants.all():
            # إنشاء نسخة جديدة من المتغير
            new_variant = ProductVariant()

            # نسخ جميع حقول المتغير (باستثناء الحقول المحددة)
            for field in variant._meta.fields:
                if field.name not in ['id', 'pk', 'product']:
                    setattr(new_variant, field.name, getattr(variant, field.name))

            new_variant.product = new_product
            new_variant.sku = f"{variant.sku}_copy" if variant.sku else ""
            new_variant.save()

            # نسخ صور المتغير إذا وجدت
            if hasattr(variant, 'images'):
                for var_image in variant.images.all():
                    var_image_path = var_image.image.path if os.path.exists(var_image.image.path) else None

                    if var_image_path:
                        new_var_image = ProductVariantImage(
                            variant=new_variant,
                            alt_text=var_image.alt_text
                        )

                        with open(var_image_path, 'rb') as f:
                            file_content = f.read()
                            file_name = os.path.basename(var_image.image.name)
                            new_var_image.image.save(file_name, ContentFile(file_content), save=False)

                        new_var_image.save()

            # نسخ خصائص المتغير
            if hasattr(variant, 'attribute_values'):
                for var_attr in variant.attribute_values.all():
                    new_var_attr = ProductVariantAttributeValue(
                        variant=new_variant,
                        attribute=var_attr.attribute,
                        value=var_attr.value
                    )
                    new_var_attr.save()

        messages.success(request, _('تم نسخ المنتج بنجاح، يمكنك الآن تعديل النسخة الجديدة'))
        return redirect('dashboard:dashboard_product_edit', product_id=new_product.id)

    # في حالة GET، اعرض صفحة تأكيد
    return render(request, 'dashboard/products/product_duplicate_confirm.html', {
        'product': original_product
    })