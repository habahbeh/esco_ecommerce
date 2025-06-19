# checkout/urls.py
from django.urls import path
from .views import CheckoutView, PaymentMethodView, PaymentConfirmationView, OrderSuccessView


app_name = 'checkout'

urlpatterns = [
    path('', CheckoutView.as_view(), name='checkout'),
    path('payment/', PaymentMethodView.as_view(), name='payment_method'),
    path('payment/confirm/', PaymentConfirmationView.as_view(), name='payment_confirmation'),
    path('success/<uuid:order_id>/', OrderSuccessView.as_view(), name='order_success'),

]