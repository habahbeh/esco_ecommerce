# File: esco_project/views.py
"""
Views for error handling and main project pages
معالجات الأخطاء والصفحات الرئيسية للمشروع
"""

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.cache import cache_page
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@requires_csrf_token
def page_not_found_view(request, exception):
    """
    Custom 404 page
    صفحة خطأ 404 مخصصة
    """
    logger.warning(f"404 error for URL: {request.path}")

    context = {
        'title': 'الصفحة غير موجودة',
        'message': 'عذراً، الصفحة التي تبحث عنها غير موجودة',
        'request_path': request.path,
    }

    response = render(request, 'errors/404.html', context)
    response.status_code = 404
    return response


def server_error_view(request):
    """
    Custom 500 page
    صفحة خطأ 500 مخصصة
    """
    logger.error(f"500 error for URL: {request.path}")

    context = {
        'title': 'خطأ في السيرفر',
        'message': 'عذراً، حدث خطأ في السيرفر. يرجى المحاولة لاحقاً',
    }

    response = render(request, 'errors/500.html', context)
    response.status_code = 500
    return response


def permission_denied_view(request, exception):
    """
    Custom 403 page
    صفحة خطأ 403 مخصصة
    """
    logger.warning(f"403 error for URL: {request.path}")

    context = {
        'title': 'ممنوع الوصول',
        'message': 'عذراً، ليس لديك صلاحية للوصول إلى هذه الصفحة',
    }

    response = render(request, 'errors/403.html', context)
    response.status_code = 403
    return response


def bad_request_view(request, exception):
    """
    Custom 400 page
    صفحة خطأ 400 مخصصة
    """
    logger.warning(f"400 error for URL: {request.path}")

    context = {
        'title': 'طلب غير صحيح',
        'message': 'عذراً، الطلب الذي أرسلته غير صحيح',
    }

    response = render(request, 'errors/400.html', context)
    response.status_code = 400
    return response


def health_check_view(request):
    """
    Health check endpoint
    نقطة التحقق من صحة النظام
    """
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "OK"
    except Exception as e:
        db_status = f"ERROR: {str(e)}"
        logger.error(f"Database health check failed: {e}")

    health_data = {
        'status': 'OK' if db_status == 'OK' else 'ERROR',
        'database': db_status,
        'timestamp': timezone.now().isoformat(),
    }

    status_code = 200 if health_data['status'] == 'OK' else 503

    if request.GET.get('format') == 'json':
        from django.http import JsonResponse
        return JsonResponse(health_data, status=status_code)

    return render(request, 'health.html', {
        'health_data': health_data
    }, status=status_code)


def maintenance_view(request):
    """
    Maintenance mode page
    صفحة وضع الصيانة
    """
    context = {
        'title': 'الموقع تحت الصيانة',
        'message': 'نعتذر، الموقع حالياً تحت الصيانة. سيعود قريباً.',
    }

    response = render(request, 'maintenance.html', context)
    response.status_code = 503
    return response