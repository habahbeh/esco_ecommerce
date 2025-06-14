# checkout/urls.py
from django.urls import path
from .views import ComingSoonView

app_name = 'checkout'

urlpatterns = [
    path('', ComingSoonView.as_view(), name='checkout'),
]