# في checkout/urls.py
from django.urls import path
from django.views.generic import TemplateView

app_name = 'checkout'

urlpatterns = [
    path('', TemplateView.as_view(template_name='checkout/coming_soon.html'), name='checkout'),
]