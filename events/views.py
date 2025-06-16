from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from .models import Event, EventImage

def event_list(request):
    """عرض قائمة الفعاليات النشطة والقادمة"""
    now = timezone.now()

    # الفعاليات الجارية
    ongoing_events = Event.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).order_by('order', 'start_date')

    # الفعاليات القادمة
    upcoming_events = Event.objects.filter(
        is_active=True,
        start_date__gt=now
    ).order_by('order', 'start_date')

    # الفعاليات المنتهية (تعرض أحدث 5 فعاليات)
    past_events = Event.objects.filter(
        is_active=True,
        end_date__lt=now
    ).order_by('-end_date')[:5]

    context = {
        'ongoing_events': ongoing_events,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
    }

    return render(request, 'events/event_list.html', context)

def event_detail(request, slug):
    """عرض تفاصيل فعالية محددة"""
    event = get_object_or_404(Event, slug=slug, is_active=True)

    # صور الفعالية
    images = event.images.all().order_by('order')

    # الفعاليات الأخرى القادمة (للعرض كاقتراحات)
    now = timezone.now()
    other_events = Event.objects.filter(
        is_active=True
    ).exclude(id=event.id).order_by('start_date')[:3]

    context = {
        'event': event,
        'images': images,
        'other_events': other_events,
    }

    return render(request, 'events/event_detail.html', context)

def get_active_banner(request):
    """واجهة برمجية تطبيقات للحصول على الشريط الإعلاني النشط"""
    now = timezone.now()

    # محاولة العثور على فعالية نشطة لعرضها في الشريط العلوي
    banner_event = Event.objects.filter(
        is_active=True,
        display_in__in=['banner', 'both'],
        start_date__lte=now,
        end_date__gte=now
    ).order_by('order', '-start_date').first()

    # إذا لم تكن هناك فعالية نشطة، ابحث عن فعالية قادمة
    if not banner_event:
        banner_event = Event.objects.filter(
            is_active=True,
            display_in__in=['banner', 'both'],
            start_date__gt=now
        ).order_by('order', 'start_date').first()

    if banner_event:
        response = {
            'success': True,
            'event': {
                'id': banner_event.id,
                'title': banner_event.title,
                'short_description': banner_event.short_description,
                'banner_image': banner_event.banner_image.url if banner_event.banner_image else None,
                'url': banner_event.get_absolute_url(),
                'registration_url': banner_event.registration_url,
                'button_text': banner_event.button_text,
                'status': banner_event.status_text
            }
        }
    else:
        response = {
            'success': False,
            'message': 'لا توجد فعاليات نشطة للعرض'
        }

    return JsonResponse(response)