from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from core.models import Newsletter
from dashboard.forms.newsletter_forms import NewsletterForm


@login_required
@permission_required('core.view_newsletter')
def dashboard_newsletters(request):
    """عرض قائمة اشتراكات النشرة البريدية"""
    newsletters = Newsletter.objects.all().order_by('-created_at')
    context = {
        'newsletters': newsletters,
        'page_title': 'اشتراكات النشرة البريدية',
        'current_page': 'اشتراكات النشرة البريدية'
    }
    return render(request, 'dashboard/newsletters/newsletter_list.html', context)


@login_required
@permission_required('core.add_newsletter')
def dashboard_newsletter_create(request):
    """إضافة اشتراك جديد في النشرة البريدية"""
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة الاشتراك بنجاح')
            return redirect('dashboard:dashboard_newsletters')
    else:
        form = NewsletterForm()

    context = {
        'form': form,
        'page_title': 'إضافة اشتراك جديد',
        'current_page': 'إضافة اشتراك جديد'
    }
    return render(request, 'dashboard/newsletters/newsletter_form.html', context)


@login_required
@permission_required('core.change_newsletter')
def dashboard_newsletter_edit(request, pk):
    """تعديل اشتراك في النشرة البريدية"""
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if request.method == 'POST':
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الاشتراك بنجاح')
            return redirect('dashboard:dashboard_newsletters')
    else:
        form = NewsletterForm(instance=newsletter)

    context = {
        'form': form,
        'newsletter': newsletter,
        'page_title': 'تعديل اشتراك',
        'current_page': 'تعديل اشتراك'
    }
    return render(request, 'dashboard/newsletters/newsletter_form.html', context)


@login_required
@permission_required('core.delete_newsletter')
def dashboard_newsletter_delete(request, pk):
    """حذف اشتراك من النشرة البريدية"""
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if request.method == 'POST':
        newsletter.delete()
        messages.success(request, 'تم حذف الاشتراك بنجاح')
        return redirect('dashboard:dashboard_newsletters')

    context = {
        'newsletter': newsletter,
        'page_title': 'حذف اشتراك',
        'current_page': 'حذف اشتراك'
    }
    return render(request, 'dashboard/newsletters/newsletter_confirm_delete.html', context)