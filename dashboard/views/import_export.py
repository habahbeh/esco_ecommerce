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
from django.db import transaction, connection



def generate_csv_template(request):
    """
    توليد قالب CSV فارغ للاستيراد - مبسط مع الحقول الأساسية فقط
    """
    import csv
    from io import StringIO
    from django.http import HttpResponse

    # إنشاء ملف CSV في الذاكرة
    output = StringIO()
    writer = csv.writer(output)

    # كتابة العناوين - الحقول الأساسية فقط
    headers = [
        'name',  # إلزامي
        'name_en',  # إلزامي
        'base_price',  # إلزامي
        'cost',  # اختياري
        'category',  # إلزامي
        'brand',  # اختياري
        'barcode',  # اختياري
        'description'  # إلزامي
    ]
    writer.writerow(headers)

    # كتابة صف مثال
    example_row = [
        'جوال سامسونج S21',  # الاسم (إلزامي)
        'Samsung Galaxy S21',  # الاسم بالإنجليزية (إلزامي)
        '3499.99',  # السعر الأساسي (إلزامي)
        '2800',  # التكلفة (اختياري)
        'الأجهزة الذكية',  # الفئة (إلزامي)
        'سامسونج',  # العلامة التجارية (اختياري)
        '8806090742286',  # الباركود (اختياري)
        'هاتف ذكي من سلسلة جالاكسي S21 بشاشة 6.2 إنش مع كاميرا عالية الدقة ومعالج سريع ومميزات متطورة للاستخدام اليومي'
        # الوصف (إلزامي - 20 حرف على الأقل)
    ]
    writer.writerow(example_row)

    # كتابة صف إضافي فارغ للتوضيح
    empty_row = ['', '', '', '', '', '', '', '']
    writer.writerow(empty_row)

    # إرجاع الملف للتنزيل
    output.seek(0)
    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=product_import_template.csv'

    return response


def generate_excel_template(request):
    """
    توليد قالب CSV فارغ للاستيراد
    """
    import csv
    from io import StringIO

    # إنشاء ملف CSV في الذاكرة
    output = StringIO()
    writer = csv.writer(output)

    # كتابة العناوين
    headers = [
        'name', 'sku', 'name_en', 'base_price', 'compare_price',
        'cost', 'stock_quantity', 'category', 'brand', 'barcode',
        'status', 'stock_status', 'is_active', 'is_featured',
        'is_new', 'is_best_seller', 'short_description',
        'description', 'tags'
    ]
    writer.writerow(headers)

    # كتابة صف مثال
    example_row = [
        'جوال سامسونج S21',  # الاسم
        'SM-G991B',  # SKU
        'Samsung Galaxy S21',  # الاسم بالإنجليزية
        '3499.99',  # السعر الأساسي
        '3999.99',  # سعر المقارنة
        '2800',  # التكلفة
        '50',  # كمية المخزون
        'الأجهزة الذكية',  # الفئة
        'سامسونج',  # العلامة التجارية
        '8806090742286',  # الباركود
        'published',  # الحالة
        'in_stock',  # حالة المخزون
        'Yes',  # نشط
        'No',  # مميز
        'Yes',  # جديد
        'No',  # الأكثر مبيعاً
        'هاتف ذكي من سلسلة جالاكسي S21 بشاشة 6.2 إنش',  # وصف مختصر
        'وصف كامل للمنتج...',  # الوصف
        'هواتف ذكية,سامسونج,5G'  # الوسوم
    ]
    writer.writerow(example_row)

    # إرجاع الملف للتنزيل
    output.seek(0)
    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=product_import_template.csv'

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

    def read_csv(self, file_path=None):
        """قراءة ملف CSV"""
        import pandas as pd

        if file_path is None:
            file_path = self.import_data.get('file_path')

        if not file_path or not os.path.exists(file_path):
            raise ValueError("ملف CSV غير موجود")

        try:
            # قراءة الملف مع تحديد الترميز
            df = pd.read_csv(file_path, encoding='utf-8-sig')

            # معالجة القيم المفقودة
            df = df.fillna("")

            # التحقق من وجود البيانات
            if df.empty:
                raise ValueError("ملف CSV فارغ - لا توجد بيانات للاستيراد")

            # تحديث الإحصائيات
            self.progress_data['total'] = len(df)

            # تخزين DataFrame
            self.import_data['df'] = df

            return df
        except Exception as e:
            raise ValueError(f"خطأ في قراءة ملف CSV: {str(e)}")

    def save_file(self, file_obj):
        """حفظ الملف المرفوع"""
        file_path = os.path.join(self.temp_dir, f"{self.import_id}_{file_obj.name}")

        with open(file_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        self.import_data['file_path'] = file_path
        return file_path

    def read_excel(self, file_path=None):
        """قراءة ملف البيانات (يدعم Excel وCSV)"""
        if file_path is None:
            file_path = self.import_data.get('file_path')

        if not file_path or not os.path.exists(file_path):
            raise ValueError("الملف غير موجود")

        try:
            # تحديد نوع الملف من امتداده
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == '.csv':
                # قراءة ملف CSV
                df = pd.read_csv(file_path, encoding='utf-8')
            elif file_ext == '.xls':
                # قراءة ملف Excel بصيغة قديمة
                df = pd.read_excel(file_path, engine='xlrd')
            elif file_ext == '.xlsx':
                # قراءة ملف Excel بصيغة حديثة
                df = pd.read_excel(file_path, engine='openpyxl')
            else:
                # محاولة تخمين نوع الملف
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except:
                    try:
                        df = pd.read_excel(file_path, engine='openpyxl')
                    except:
                        try:
                            df = pd.read_excel(file_path, engine='xlrd')
                        except:
                            raise ValueError("صيغة الملف غير مدعومة. الرجاء استخدام CSV أو Excel.")

            # معالجة القيم المفقودة
            df = df.fillna("")

            # التحقق من وجود البيانات
            if df.empty:
                raise ValueError("الملف فارغ - لا توجد بيانات للاستيراد")

            # تحديث الإحصائيات
            self.progress_data['total'] = len(df)

            # تخزين DataFrame
            self.import_data['df'] = df

            return df
        except Exception as e:
            raise ValueError(f"خطأ في قراءة الملف: {str(e)}")

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
    عرض صفحة استيراد المنتجات وتنفيذ الاستيراد - يقبل CSV فقط
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
            csv_file = request.FILES['file']
            update_existing = form.cleaned_data.get('update_existing', True)
            default_category = form.cleaned_data.get('category')

            # التحقق من امتداد الملف
            file_name = csv_file.name
            if not file_name.endswith('.csv'):
                messages.error(request, "الملف المرفوع ليس بصيغة CSV المدعومة (.csv)")
                return redirect('dashboard:product_import')

            # إنشاء مدير الاستيراد
            import_manager = ImportManager()

            # حفظ الملف
            import_manager.save_file(csv_file)

            # قراءة الملف
            try:
                import pandas as pd
                df = pd.read_csv(import_manager.import_data['file_path'], encoding='utf-8-sig')

                # معالجة القيم المفقودة
                df = df.fillna("")

                # التحقق من وجود الأعمدة المطلوبة
                required_columns = ['name', 'name_en', 'base_price', 'category', 'description']
                missing_columns = [col for col in required_columns if col not in df.columns]

                if missing_columns:
                    messages.error(request, f"الأعمدة التالية مفقودة في الملف: {', '.join(missing_columns)}")
                    return redirect('dashboard:product_import')

            except Exception as e:
                messages.error(request, f"خطأ في قراءة ملف CSV: {str(e)}")
                return redirect('dashboard:product_import')

            # حفظ بيانات الاستيراد الإضافية
            import_manager.import_data['update_existing'] = update_existing
            import_manager.import_data['default_category_id'] = default_category.id if default_category else None
            import_manager.save_import_data()

            # حفظ بيانات التقدم
            import_manager.progress_data['total'] = len(df)
            import_manager.save_progress()

            # بدء عملية الاستيراد في الخلفية
            import threading
            threading.Thread(
                target=process_import,
                args=(import_manager.import_id, request.user.id),
                daemon=True
            ).start()

            # توجيه المستخدم إلى صفحة النتائج
            messages.success(request, f"تم بدء استيراد {len(df)} منتج. يرجى الانتظار حتى اكتمال العملية.")
            return redirect('dashboard:import_results', import_id=import_manager.import_id)

        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء معالجة ملف CSV: {str(e)}")
            return redirect('dashboard:product_import')
    else:
        # عرض نموذج الاستيراد
        form = ProductImportForm()

        context = {
            'form': form,
            'form_title': 'استيراد المنتجات من CSV',
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
    معالجة الاستيراد في الخلفية - حل مشكلة UUID
    """
    from django.contrib.auth import get_user_model
    from decimal import Decimal
    import pandas as pd
    import time
    import os
    import uuid
    from django.db import transaction
    from django.utils.text import slugify
    from django.utils import timezone
    from products.models import Product, Category, Brand

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

        # قراءة ملف CSV
        try:
            # تحديد نوع الملف من امتداده
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            else:
                # محاولة قراءة ملف Excel
                df = pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            import_manager.progress_data['status'] = 'error'
            import_manager.progress_data['error_message'] = f"خطأ في قراءة الملف: {str(e)}"
            import_manager.save_progress()
            return

        # معالجة القيم المفقودة
        df = df.fillna("")

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

                # استخراج البيانات الأساسية الإلزامية
                name = str(row_data.get('name', '')).strip()
                name_en = str(
                    row_data.get('name_en', '')).strip() or name  # استخدام الاسم العربي إذا كان الاسم الإنجليزي فارغاً
                base_price_str = str(row_data.get('base_price', '')).strip()
                category_name = str(row_data.get('category', '')).strip()
                description = str(row_data.get('description', '')).strip()

                # فحص البيانات الإلزامية
                if not name:
                    raise ValueError(f"اسم المنتج مطلوب في الصف {index + 2}")

                if not base_price_str:
                    raise ValueError(f"السعر الأساسي مطلوب في الصف {index + 2}")

                if not category_name and not default_category:
                    raise ValueError(f"الفئة مطلوبة في الصف {index + 2}")

                if not description:
                    # إنشاء وصف افتراضي إذا كان فارغاً - مع 20 حرف على الأقل
                    description = f"وصف تلقائي للمنتج: {name}. هذا وصف تم إنشاؤه تلقائياً خلال عملية الاستيراد."
                elif len(description) < 20:
                    # إطالة الوصف ليصل إلى 20 حرف
                    additional_text = " " + "هذا وصف تم تمديده تلقائياً."
                    description = description + additional_text

                # البيانات الاختيارية
                cost_str = str(row_data.get('cost', '')).strip()
                brand_name = str(row_data.get('brand', '')).strip()
                barcode = str(row_data.get('barcode', '')).strip()

                # تحويل السعر الأساسي
                try:
                    base_price = float(base_price_str.replace(',', '.'))
                except (ValueError, TypeError):
                    raise ValueError(f"قيمة السعر الأساسي غير صالحة في الصف {index + 2}")

                # تحويل التكلفة إذا وجدت
                cost = None
                if cost_str:
                    try:
                        cost = float(cost_str.replace(',', '.'))
                    except (ValueError, TypeError):
                        # تجاهل أخطاء التكلفة لأنها اختيارية
                        pass

                # معالجة الفئة
                category = None
                if category_name:
                    try:
                        category = Category.objects.get(name=category_name)
                    except Category.DoesNotExist:
                        # محاولة البحث بالاسم الإنجليزي
                        try:
                            category = Category.objects.get(name_en=category_name)
                        except Category.DoesNotExist:
                            if default_category:
                                category = default_category
                            else:
                                # إنشاء فئة جديدة مع slug
                                cat_slug = slugify(category_name, allow_unicode=True)
                                if not cat_slug:
                                    cat_slug = f"category-{uuid.uuid4().hex[:8]}"

                                if Category.objects.filter(slug=cat_slug).exists():
                                    cat_slug = f"{cat_slug}-{uuid.uuid4().hex[:6]}"

                                new_category = Category.objects.create(
                                    name=category_name,
                                    slug=cat_slug,
                                    is_active=True,
                                    created_by=user
                                )
                                category = new_category
                elif default_category:
                    category = default_category

                # معالجة العلامة التجارية (اختياري)
                brand = None
                if brand_name:
                    try:
                        brand = Brand.objects.get(name=brand_name)
                    except Brand.DoesNotExist:
                        # محاولة البحث بالاسم الإنجليزي
                        try:
                            brand = Brand.objects.get(name_en=brand_name)
                        except Brand.DoesNotExist:
                            # إنشاء علامة تجارية جديدة
                            brand_slug = slugify(brand_name, allow_unicode=True)
                            if not brand_slug:
                                brand_slug = f"brand-{uuid.uuid4().hex[:8]}"

                            if Brand.objects.filter(slug=brand_slug).exists():
                                brand_slug = f"{brand_slug}-{uuid.uuid4().hex[:6]}"

                            new_brand = Brand.objects.create(
                                name=brand_name,
                                slug=brand_slug,
                                is_active=True,
                                created_by=user
                            )
                            brand = new_brand

                # إنشاء SKU فريد
                sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"

                # إنشاء سلج فريد
                slug_base = slugify(name_en or name, allow_unicode=True)
                if not slug_base:
                    slug_base = f"product-{uuid.uuid4().hex[:8]}"

                slug = slug_base
                counter = 1

                # التأكد من أن السلج فريد
                while Product.objects.filter(slug=slug).exists():
                    slug = f"{slug_base}-{counter}"
                    counter += 1

                # أوجد إذا كان المنتج موجوداً بالفعل
                existing_product = None
                if update_existing:
                    # البحث بالاسم والفئة
                    existing_product = Product.objects.filter(
                        name=name,
                        category=category
                    ).first()

                # الحل النهائي: استخدام طريقة ORM مع منع التحقق
                with transaction.atomic():
                    if existing_product and update_existing:
                        # تحديث المنتج الموجود
                        existing_product.name = name
                        existing_product.name_en = name_en
                        existing_product.description = description
                        existing_product.base_price = base_price

                        if cost is not None:
                            existing_product.cost = cost

                        if barcode:
                            existing_product.barcode = barcode

                        existing_product.category = category
                        if brand:
                            existing_product.brand = brand

                        # حفظ المنتج مع منع التحقق
                        existing_product.save(validate=False)

                        # تحديث الإحصائيات
                        import_manager.progress_data['updated'] += 1
                    else:
                        # إنشاء منتج جديد
                        new_product = Product(
                            name=name,
                            name_en=name_en,
                            slug=slug,
                            sku=sku,
                            description=description,
                            base_price=base_price,
                            category=category,
                            brand=brand,
                            barcode=barcode,
                            status='published',
                            is_active=True,
                            stock_quantity=100,
                            stock_status='in_stock',
                            created_by=user
                        )

                        # إضافة التكلفة إذا وجدت
                        if cost is not None:
                            new_product.cost = cost

                        # حفظ المنتج مع منع التحقق
                        new_product.save(validate=False)

                        # تحديث الإحصائيات
                        import_manager.progress_data['success'] += 1

            except Exception as e:
                # تسجيل الخطأ
                error_message = str(e)
                print(f"خطأ في استيراد الصف {index + 2}: {error_message}")

                import_manager.progress_data['errors'] += 1
                import_manager.progress_data['error_details'].append({
                    'row': index + 2,
                    'name': str(row.get('name', '')) if not pd.isna(row.get('name', '')) else "غير معروف",
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


