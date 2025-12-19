# في ملف dashboard/views/sliders.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from core.models import SliderItem
from dashboard.forms.slider_forms import SliderItemForm  # سنقوم بإنشاء هذا الملف لاحقاً


@login_required
@permission_required('core.view_slideritem')
def dashboard_sliders(request):
    """عرض قائمة عناصر السلايدر"""
    sliders = SliderItem.objects.all()
    context = {
        'sliders': sliders,
        'page_title': 'إدارة السلايدر',
        'current_page': 'إدارة السلايدر'
    }
    return render(request, 'dashboard/sliders/slider_list.html', context)


@login_required
@permission_required('core.add_slideritem')
def dashboard_slider_create(request):
    """إضافة عنصر سلايدر جديد"""
    if request.method == 'POST':
        form = SliderItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة عنصر السلايدر بنجاح')
            return redirect('dashboard:dashboard_sliders')
    else:
        form = SliderItemForm()

    context = {
        'form': form,
        'page_title': 'إضافة عنصر سلايدر',
        'current_page': 'إضافة عنصر سلايدر'
    }
    return render(request, 'dashboard/sliders/slider_form.html', context)


@login_required
@permission_required('core.change_slideritem')
def dashboard_slider_edit(request, pk):
    """تعديل عنصر سلايدر"""
    slider = get_object_or_404(SliderItem, pk=pk)

    if request.method == 'POST':
        form = SliderItemForm(request.POST, request.FILES, instance=slider)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث عنصر السلايدر بنجاح')
            return redirect('dashboard:dashboard_sliders')
    else:
        form = SliderItemForm(instance=slider)

    context = {
        'form': form,
        'slider': slider,
        'page_title': 'تعديل عنصر السلايدر',
        'current_page': 'تعديل عنصر السلايدر'
    }
    return render(request, 'dashboard/sliders/slider_form.html', context)


@login_required
@permission_required('core.delete_slideritem')
def dashboard_slider_delete(request, pk):
    """حذف عنصر سلايدر"""
    slider = get_object_or_404(SliderItem, pk=pk)

    if request.method == 'POST':
        slider.delete()
        messages.success(request, 'تم حذف عنصر السلايدر بنجاح')
        return redirect('dashboard:dashboard_sliders')

    context = {
        'slider': slider,
        'page_title': 'حذف عنصر السلايدر',
        'current_page': 'حذف عنصر السلايدر'
    }
    return render(request, 'dashboard/sliders/slider_confirm_delete.html', context)