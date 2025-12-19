from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from events.models import Event, EventImage
from dashboard.forms.event_forms import EventForm, EventImageForm


@login_required
@permission_required('events.view_event')
def dashboard_events(request):
    """عرض قائمة الفعاليات"""
    events = Event.objects.all().order_by('order', '-start_date')
    context = {
        'events': events,
        'page_title': 'إدارة الفعاليات',
        'current_page': 'إدارة الفعاليات'
    }
    return render(request, 'dashboard/events/event_list.html', context)


@login_required
@permission_required('events.add_event')
def dashboard_event_create(request):
    """إضافة فعالية جديدة"""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة الفعالية بنجاح')
            return redirect('dashboard:dashboard_events')
    else:
        form = EventForm()

    context = {
        'form': form,
        'page_title': 'إضافة فعالية جديدة',
        'current_page': 'إضافة فعالية جديدة'
    }
    return render(request, 'dashboard/events/event_form.html', context)


@login_required
@permission_required('events.change_event')
def dashboard_event_edit(request, pk):
    """تعديل فعالية"""
    event = get_object_or_404(Event, pk=pk)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الفعالية بنجاح')
            return redirect('dashboard:dashboard_events')
    else:
        form = EventForm(instance=event)

    context = {
        'form': form,
        'event': event,
        'page_title': 'تعديل الفعالية',
        'current_page': 'تعديل الفعالية'
    }
    return render(request, 'dashboard/events/event_form.html', context)


@login_required
@permission_required('events.delete_event')
def dashboard_event_delete(request, pk):
    """حذف فعالية"""
    event = get_object_or_404(Event, pk=pk)

    if request.method == 'POST':
        event.delete()
        messages.success(request, 'تم حذف الفعالية بنجاح')
        return redirect('dashboard:dashboard_events')

    context = {
        'event': event,
        'page_title': 'حذف الفعالية',
        'current_page': 'حذف الفعالية'
    }
    return render(request, 'dashboard/events/event_confirm_delete.html', context)


@login_required
@permission_required('events.view_event')
def dashboard_event_detail(request, pk):
    """عرض تفاصيل الفعالية وإدارة الصور"""
    event = get_object_or_404(Event, pk=pk)
    event_images = event.images.all().order_by('order')

    # نموذج إضافة صورة جديدة
    if request.method == 'POST':
        image_form = EventImageForm(request.POST, request.FILES)
        if image_form.is_valid():
            new_image = image_form.save(commit=False)
            new_image.event = event
            new_image.save()
            messages.success(request, 'تم إضافة الصورة بنجاح')
            return redirect('dashboard:dashboard_event_detail', pk=event.id)
    else:
        image_form = EventImageForm(initial={'order': event_images.count()})

    context = {
        'event': event,
        'event_images': event_images,
        'image_form': image_form,
        'page_title': f'تفاصيل الفعالية: {event.title}',
        'current_page': 'تفاصيل الفعالية'
    }
    return render(request, 'dashboard/events/event_detail.html', context)


@login_required
@permission_required('events.change_eventimage')
def dashboard_event_image_edit(request, event_pk, image_pk):
    """تعديل صورة فعالية"""
    event = get_object_or_404(Event, pk=event_pk)
    image = get_object_or_404(EventImage, pk=image_pk, event=event)

    if request.method == 'POST':
        form = EventImageForm(request.POST, request.FILES, instance=image)

        if form.is_valid():
            updated_image = form.save(commit=False)

            # إذا لم يتم تحميل صورة جديدة، احتفظ بالصورة الحالية
            if not updated_image.image and 'image' not in request.FILES:
                updated_image.image = image.image

            updated_image.save()
            messages.success(request, 'تم تحديث الصورة بنجاح')
            return redirect('dashboard:dashboard_event_detail', pk=event.id)
    else:
        form = EventImageForm(instance=image)

    context = {
        'form': form,
        'event': event,
        'image': image,
        'page_title': 'تعديل صورة',
        'current_page': 'تعديل صورة'
    }
    return render(request, 'dashboard/events/event_image_form.html', context)


@login_required
@permission_required('events.delete_eventimage')
def dashboard_event_image_delete(request, event_pk, image_pk):
    """حذف صورة فعالية"""
    event = get_object_or_404(Event, pk=event_pk)
    image = get_object_or_404(EventImage, pk=image_pk, event=event)

    if request.method == 'POST':
        image.delete()
        messages.success(request, 'تم حذف الصورة بنجاح')
        return redirect('dashboard:dashboard_event_detail', pk=event.id)

    context = {
        'event': event,
        'image': image,
        'page_title': 'حذف صورة',
        'current_page': 'حذف صورة'
    }
    return render(request, 'dashboard/events/event_image_confirm_delete.html', context)