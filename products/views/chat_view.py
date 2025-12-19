# products/views/chat_view.py
from django.shortcuts import render
from django.views import View


class ProductChatPageView(View):
    """صفحة الدردشة في الموقع"""

    def get(self, request):
        return render(request, 'products/chat.html')