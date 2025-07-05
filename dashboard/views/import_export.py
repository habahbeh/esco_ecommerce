# dashboard/views/import_export.py
# ملف جديد مخصص لوظائف الاستيراد والتصدير

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils.text import slugify
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone

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

from dashboard.forms.import_export import ProductImportForm
from products.models import Product, Category, Brand, Tag


def generate_excel_template(request):
    """
    توليد قالب Excel فارغ للاستيراد
    """
    # إنشاء ملف Excel جديد في الذاكرة
    output = io.BytesIO()
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

    # قائمة بالأعمدة المطلوبة (الحقول الإلزامية مميزة)
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
        {'name': 'is_active', 'title': 'نشط', 'width': 10, 'required': False, 'example': 'Yes/No'},
        {'name': 'is_featured', 'title': 'مميز', 'width': 10, 'required': False, 'example': 'Yes/No'},
        {'name': 'is_new', 'title': 'جديد', 'width': 10, 'required': False, 'example': 'Yes/No'},
        {'name': 'is_best_seller', 'title': 'الأكثر مبيعاً', 'width': 10, 'required': False, 'example': 'Yes/No'},
        {'name': 'short_description', 'title': 'وصف مختصر', 'width': 40, 'required': False,
         'example': 'هاتف ذكي من سلسلة جالاكسي S21 بشاشة 6.2 إنش'},
        {'name': 'description', 'title': 'الوصف', 'width': 50, 'required': False, 'example': 'وصف كامل للمنتج...'},
        {'name': 'tags', 'title': 'الوسوم', 'width': 20, 'required': False, 'example': 'هواتف ذكية,سامسونج,5G'},
    ]

    # كتابة العناوين
    for col, column in enumerate(columns):
        format_to_use = required_format if column['required'] else header_format
        worksheet.write(0, col, column['name'], format_to_use)
        worksheet.write(1, col, column['title'], header_format)
        worksheet.set_column(col, col, column['width'])

    # كتابة صف مثال
    example_format = workbook.add_format({
        'italic': True,
        'bg_color': '#E6F4EA',
        'border': 1
    })

    for col, column in enumerate(columns):
        worksheet.write(2, col, column['example'], example_format)

    # كتابة ملاحظات استخدام القالب
    notes_row = 4
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


class ImportManager:
    """
    مدير عمليات استيراد المنتجات
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
            'status': 'pending',
            'error_details': []
        }
        self.import_data = {}

        # إنشاء مجلد مؤقت للاستيراد إذا لم يكن موجوداً
        self.temp_dir = os.path.join('media', 'temp', 'imports')
        os.makedirs(self.temp_dir, exist_ok=True)

    def save_file(self, file_obj):
        """حفظ الملف المرفوع"""
        file_path = os.path.join(self.temp_dir, f"{self.import_id}_{file_obj.name}")

        with open(file_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        self.import_data['file_path'] = file_path
        return file_path

    def read_excel(self, file_path=None):
        """قراءة ملف Excel"""
        if file_path is None:
            file_path = self.import_data.get('file_path')

        if not file_path or not os.path.exists(file_path):
            raise ValueError("ملف Excel غير موجود")

        try:
            df = pd.read_excel(file_path, sheet_name=0)

            # التحقق من وجود البيانات
            if df.empty:
                raise ValueError("ملف Excel فارغ - لا توجد بيانات للاستيراد")

            # تحديث الإحصائيات
            self.progress_data['total'] = len(df)

            # تخزين DataFrame
            self.import_data['df'] = df

            return df
        except Exception as e:
            raise ValueError(f"خطأ في قراءة ملف Excel: {str(e)}")

    def save_progress(self):
        """حفظ بيانات التقدم"""
        progress_path = os.path.join(self.temp_dir, f"{self.import_id}_progress.json")
        with open(progress_path, 'w', encoding='utf-8') as f:
            json.dump(self.progress_data, f, ensure_ascii=False)

    def save_import_data(self):
        """حفظ بيانات الاستيراد"""
        # استبدال DataFrame بقائمة للتخزين
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

        # حفظ البيانات
        data_path = os.path.join(self.temp_dir, f"{self.import_id}_data.json")
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(self.import_data, f, ensure_ascii=False)

    def load_progress(self):
        """تحميل بيانات التقدم"""
        progress_path = os.path.join(self.temp_dir, f"{self.import_id}_progress.json")
        if os.path.exists(progress_path):
            with open(progress_path, 'r', encoding='utf-8') as f:
                self.progress_data = json.load(f)
                return self.progress_data
        return None

    def load_import_data(self):
        """تحميل بيانات الاستيراد"""
        data_path = os.path.join(self.temp_dir, f"{self.import_id}_data.json")
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                self.import_data = json.load(f)
                return self.import_data
        return None

    def export_errors(self):
        """تصدير الأخطاء إلى ملف Excel"""
        if not self.progress_data.get('error_details'):
            return None

        # إنشاء ملف Excel جديد
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('أخطاء الاستيراد')

        # تنسيق للعناوين
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D7E4BC',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True
        })

        # تنسيق للأخطاء
        error_format = workbook.add_format({
            'bg_color': '#FFC7CE',
            'border': 1,
            'text_wrap': True
        })

        # كتابة العناوين
        headers = ['رقم الصف', 'الاسم', 'SKU', 'رسالة الخطأ', 'name', 'sku', 'name_en', 'base_price', 'category',
                   'brand', 'stock_quantity']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        # كتابة بيانات الأخطاء
        for row, error in enumerate(self.progress_data['error_details']):
            worksheet.write(row + 1, 0, error.get('row', ''), error_format)
            worksheet.write(row + 1, 1, error.get('name', ''), error_format)
            worksheet.write(row + 1, 2, error.get('sku', ''), error_format)
            worksheet.write(row + 1, 3, error.get('error', ''), error_format)

            # كتابة بيانات المنتج
            if 'data' in error:
                data = error['data']
                worksheet.write(row + 1, 4, data.get('name', ''))
                worksheet.write(row + 1, 5, data.get('sku', ''))
                worksheet.write(row + 1, 6, data.get('name_en', ''))
                worksheet.write(row + 1, 7, data.get('base_price', ''))
                worksheet.write(row + 1, 8, data.get('category', ''))
                worksheet.write(row + 1, 9, data.get('brand', ''))
                worksheet.write(row + 1, 10, data.get('stock_quantity', ''))

        # تنسيق عرض الأعمدة
        worksheet.set_column(0, 0, 10)
        worksheet.set_column(1, 2, 20)
        worksheet.set_column(3, 3, 40)
        worksheet.set_column(4, 10, 15)

        # إغلاق الملف
        workbook.close()

        # تجهيز البيانات للتنزيل
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        return {
            'data': output.getvalue(),
            'filename': f"import_errors_{timestamp}.xlsx"
        }


def product_import_view(request):
    """
    عرض صفحة استيراد المنتجات وتنفيذ الاستيراد
    """
    if request.method == 'POST':
        form = ProductImportForm(request.POST, request.FILES)

        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form[field].label}: {error}")
            return redirect('dashboard:product_import')

        try:
            # استرجاع بيانات النموذج
            excel_file = request.FILES['file']
            update_existing = form.cleaned_data.get('update_existing', True)
            default_category = form.cleaned_data.get('category')

            # التحقق من امتداد الملف
            file_name = excel_file.name
            if not (file_name.endswith('.xlsx') or file_name.endswith('.xls')):
                messages.error(request, "الملف المرفوع ليس بصيغة Excel المدعومة (.xlsx, .xls)")
                return redirect('dashboard:product_import')

            # إنشاء مدير الاستيراد
            import_manager = ImportManager()

            # حفظ الملف
            import_manager.save_file(excel_file)

            # قراءة الملف
            df = import_manager.read_excel()

            # التحقق من وجود الأعمدة المطلوبة
            required_columns = ['name']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                messages.error(request, f"الأعمدة التالية مفقودة في الملف: {', '.join(missing_columns)}")
                return redirect('dashboard:product_import')

            # حفظ بيانات الاستيراد الإضافية
            import_manager.import_data['update_existing'] = update_existing
            import_manager.import_data['default_category_id'] = default_category.id if default_category else None
            import_manager.save_import_data()

            # حفظ بيانات التقدم
            import_manager.save_progress()

            # بدء عملية الاستيراد في الخلفية
            threading.Thread(
                target=process_import,
                args=(import_manager.import_id, request.user.id),
                daemon=True
            ).start()

            # توجيه المستخدم إلى صفحة النتائج
            messages.success(request, f"تم بدء استيراد {len(df)} منتج. يرجى الانتظار حتى اكتمال العملية.")
            return redirect('dashboard:import_results', import_id=import_manager.import_id)

        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء معالجة ملف Excel: {str(e)}")
            return redirect('dashboard:product_import')
    else:
        # عرض نموذج الاستيراد
        form = ProductImportForm()

        context = {
            'form': form,
            'form_title': 'استيراد المنتجات من Excel',
        }

        return render(request, 'dashboard/products/product_import.html', context)


def import_results_view(request, import_id):
    """
    عرض نتائج الاستيراد
    """
    # استرجاع مدير الاستيراد
    import_manager = ImportManager(import_id)
    progress_data = import_manager.load_progress()
    import_data = import_manager.load_import_data()

    if not progress_data or not import_data:
        messages.error(request, "انتهت صلاحية بيانات الاستيراد أو أن معرف الاستيراد غير صحيح")
        return redirect('dashboard:product_import')

    # تحضير بيانات السياق
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


def export_errors_view(request):
    """
    تصدير المنتجات التي فشل استيرادها إلى ملف Excel
    """
    import_id = request.GET.get('import_id')

    if not import_id:
        messages.error(request, "معرف الاستيراد مفقود")
        return redirect('dashboard:product_import')

    # استرجاع مدير الاستيراد
    import_manager = ImportManager(import_id)
    progress_data = import_manager.load_progress()

    if not progress_data:
        messages.error(request, "انتهت صلاحية بيانات الاستيراد أو أن معرف الاستيراد غير صحيح")
        return redirect('dashboard:product_import')

    if not progress_data.get('error_details'):
        messages.warning(request, "لا توجد أخطاء للتصدير")
        return redirect('dashboard:import_results', import_id=import_id)

    # تصدير الأخطاء
    excel_data = import_manager.export_errors()

    if not excel_data:
        messages.error(request, "حدث خطأ أثناء تصدير الأخطاء")
        return redirect('dashboard:import_results', import_id=import_id)

    # إرجاع الملف للتنزيل
    response = HttpResponse(
        excel_data['data'],
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={excel_data["filename"]}'

    return response


def import_progress_view(request):
    """
    الحصول على تقدم الاستيراد عبر AJAX
    """
    import_id = request.GET.get('import_id')

    if not import_id:
        return JsonResponse({'success': False, 'error': "معرف الاستيراد مفقود"})

    # استرجاع مدير الاستيراد
    import_manager = ImportManager(import_id)
    progress_data = import_manager.load_progress()

    if not progress_data:
        return JsonResponse({'success': False, 'error': "انتهت صلاحية بيانات الاستيراد أو أن معرف الاستيراد غير صحيح"})

    return JsonResponse({
        'success': True,
        'progress': progress_data
    })


def process_import(import_id, user_id):
    """
    معالجة الاستيراد في الخلفية
    """
    from django.contrib.auth import get_user_model
    from decimal import Decimal, ROUND_HALF_UP
    User = get_user_model()

    # إنشاء مدير الاستيراد
    import_manager = ImportManager(import_id)

    try:
        # الحصول على المستخدم
        user = User.objects.get(id=user_id)

        # استرجاع مدير الاستيراد
        import_manager.load_progress()
        import_data = import_manager.load_import_data()

        if not import_data:
            import_manager.progress_data['status'] = 'error'
            import_manager.progress_data['error_message'] = "بيانات الاستيراد غير موجودة"
            import_manager.save_progress()
            return

        # استرجاع الإعدادات
        update_existing = import_data.get('update_existing', True)
        default_category_id = import_data.get('default_category_id')
        file_path = import_data.get('file_path')

        # استرجاع الفئة الافتراضية
        default_category = None
        if default_category_id:
            try:
                default_category = Category.objects.get(id=default_category_id)
            except Category.DoesNotExist:
                pass

        # قراءة الملف مباشرة
        df = pd.read_excel(file_path, sheet_name=0)

        # تحديث حالة التقدم
        import_manager.progress_data['total'] = len(df)
        import_manager.progress_data['status'] = 'processing'
        import_manager.save_progress()

        # معالجة كل صف
        for index, row in df.iterrows():
            # مهلة صغيرة لتجنب استهلاك موارد CPU
            time.sleep(0.01)

            try:
                # استخراج البيانات
                row_data = {}
                for col in df.columns:
                    val = row[col]
                    if pd.isna(val):
                        row_data[col] = ""
                    else:
                        row_data[col] = val

                # حفظ المنتج
                with transaction.atomic():
                    # استخراج البيانات الأساسية
                    name = str(row_data.get('name', '')).strip()
                    sku = str(row_data.get('sku', '')).strip()

                    # فحص البيانات الإلزامية
                    if not name:
                        raise ValueError(f"اسم المنتج مطلوب في الصف {index + 2}")

                    # إنشاء SKU إذا لم يكن موجوداً
                    if not sku:
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
                    name_en = row_data.get('name_en', '')
                    if name_en:
                        product.name_en = str(name_en)

                    description = row_data.get('description', '')
                    if description:
                        product.description = str(description)

                    short_description = row_data.get('short_description', '')
                    if short_description:
                        product.short_description = str(short_description)

                    barcode = row_data.get('barcode', '')
                    if barcode:
                        product.barcode = str(barcode)

                        # معالجة الأسعار مع تقريب الخانات العشرية
                        base_price = row_data.get('base_price', '')
                        if base_price:
                            try:
                                # تقريب القيمة إلى خانتين عشريتين
                                product.base_price = round(float(base_price), 2)
                            except (ValueError, TypeError):
                                raise ValueError(f"قيمة السعر الأساسي غير صالحة في الصف {index + 2}")

                        compare_price = row_data.get('compare_price', '')
                        if compare_price:
                            try:
                                # تقريب القيمة إلى خانتين عشريتين
                                product.compare_price = round(float(compare_price), 2)
                            except (ValueError, TypeError):
                                raise ValueError(f"قيمة سعر المقارنة غير صالحة في الصف {index + 2}")

                        cost = row_data.get('cost', '')
                        if cost:
                            try:
                                # تقريب القيمة إلى خانتين عشريتين
                                product.cost = round(float(cost), 2)
                            except (ValueError, TypeError):
                                raise ValueError(f"قيمة التكلفة غير صالحة في الصف {index + 2}")

                    # معالجة المخزون
                    stock_quantity = row_data.get('stock_quantity', '')
                    if stock_quantity:
                        try:
                            product.stock_quantity = int(float(stock_quantity))
                        except (ValueError, TypeError):
                            raise ValueError(f"قيمة كمية المخزون غير صالحة في الصف {index + 2}")

                    # معالجة الفئة
                    category_name = row_data.get('category', '')
                    if category_name:
                        category_name = str(category_name).strip()
                        try:
                            category = Category.objects.get(name=category_name)
                            product.category = category
                        except Category.DoesNotExist:
                            # محاولة البحث بالاسم الإنجليزي
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

                    # معالجة العلامة التجارية
                    brand_name = row_data.get('brand', '')
                    if brand_name:
                        brand_name = str(brand_name).strip()
                        try:
                            brand = Brand.objects.get(name=brand_name)
                            product.brand = brand
                        except Brand.DoesNotExist:
                            # محاولة البحث بالاسم الإنجليزي
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
                    status = row_data.get('status', '')
                    if status:
                        status = str(status).strip().lower()
                        if status in dict(Product.STATUS_CHOICES).keys():
                            product.status = status
                        else:
                            product.status = 'draft'

                    # معالجة حالة المخزون
                    stock_status = row_data.get('stock_status', '')
                    if stock_status:
                        stock_status = str(stock_status).strip().lower()
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
                        field_value = row_data.get(bool_field, '')
                        if field_value:
                            if isinstance(field_value, bool):
                                setattr(product, bool_field, field_value)
                            else:
                                value_str = str(field_value).lower()
                                setattr(product, bool_field, value_str in ['yes', 'نعم', 'true', '1', 'y', 't'])

                    # إنشاء سلج للمنتجات الجديدة
                    if action == "create":
                        product.slug = slugify(name, allow_unicode=True)
                        if Product.objects.filter(slug=product.slug).exists():
                            product.slug = f"{product.slug}-{uuid.uuid4().hex[:6]}"

                        product.created_by = user

                    # حفظ المنتج
                    product.save()

                    # معالجة الوسوم
                    tags_str = row_data.get('tags', '')
                    if tags_str:
                        tags_str = str(tags_str).strip()
                        tags_list = [tag.strip() for tag in str(tags_str).split(',') if tag.strip()]

                        for tag_name in tags_list:
                            # البحث عن الوسم أو إنشائه
                            tag, created = Tag.objects.get_or_create(
                                name=tag_name,
                                defaults={
                                    'slug': slugify(tag_name, allow_unicode=True),
                                    'is_active': True
                                }
                            )
                            product.tags.add(tag)

                    # تحديث الإحصائيات
                    if action == "create":
                        import_manager.progress_data['success'] += 1
                    else:
                        import_manager.progress_data['updated'] += 1

            except Exception as e:
                # تسجيل الخطأ
                error_message = str(e)
                print(f"خطأ في استيراد الصف {index + 2}: {error_message}")

                import_manager.progress_data['errors'] += 1
                import_manager.progress_data['error_details'].append({
                    'row': index + 2,
                    'name': str(row.get('name', '')) if not pd.isna(row.get('name', '')) else "غير معروف",
                    'sku': str(row.get('sku', '')) if not pd.isna(row.get('sku', '')) else "غير معروف",
                    'error': error_message,
                    'data': row_data
                })

            # تحديث التقدم
            import_manager.progress_data['processed'] += 1

            # حفظ التقدم كل بضعة صفوف
            if index % 5 == 0 or index == len(df) - 1:
                import_manager.save_progress()

        # تحديث الحالة إلى مكتملة
        import_manager.progress_data['status'] = 'completed'
        import_manager.save_progress()

    except Exception as e:
        # تسجيل الخطأ العام
        import_manager = ImportManager(import_id)
        import_manager.load_progress()
        import_manager.progress_data['status'] = 'error'
        import_manager.progress_data['error_message'] = str(e)
        import_manager.save_progress()

        print(f"خطأ عام في عملية الاستيراد: {str(e)}")


# بدل الدالة الأصلية round، استخدم هذا الكود:
def round_decimal(value, decimal_places=2):
    """تقريب القيمة إلى عدد محدد من الخانات العشرية باستخدام Decimal"""
    from decimal import Decimal, ROUND_HALF_UP

    if value is None:
        return None

    try:
        # تحويل القيمة إلى Decimal
        decimal_value = Decimal(str(value))

        # تقريب القيمة باستخدام ROUND_HALF_UP
        rounded_value = decimal_value.quantize(
            Decimal('0.01'),  # 0.01 للتقريب إلى خانتين عشريتين
            rounding=ROUND_HALF_UP
        )

        return rounded_value
    except Exception:
        # إذا حدث خطأ، إرجاع القيمة الأصلية
        return value

        # واستخدم هذه الدالة بدلاً من round عند معالجة الأسعار:
        base_price = row_data.get('base_price', '')
        if base_price:
            try:
                # تقريب القيمة إلى خانتين عشريتين
                product.base_price = round_decimal(base_price)
            except (ValueError, TypeError):
                raise ValueError(f"قيمة السعر الأساسي غير صالحة في الصف {index + 2}")

        compare_price = row_data.get('compare_price', '')
        if compare_price:
            try:
                # تقريب القيمة إلى خانتين عشريتين
                product.compare_price = round_decimal(compare_price)
            except (ValueError, TypeError):
                raise ValueError(f"قيمة سعر المقارنة غير صالحة في الصف {index + 2}")

        cost = row_data.get('cost', '')
        if cost:
            try:
                # تقريب القيمة إلى خانتين عشريتين
                product.cost = round_decimal(cost)
            except (ValueError, TypeError):
                raise ValueError(f"قيمة التكلفة غير صالحة في الصف {index + 2}")