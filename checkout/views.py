from django.shortcuts import render
from django.views.generic import TemplateView

class ComingSoonView(TemplateView):
    """
    صفحة مؤقتة تظهر أثناء تطوير نظام الدفع
    """
    template_name = 'checkout/coming_soon.html'
