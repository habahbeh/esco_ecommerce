from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # الصفحة الرئيسية - Home page
    path('', views.HomeView.as_view(), name='home'),

    # صفحات ثابتة - Static pages
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),

    # تغيير اللغة - Language switching
    # path('set-language/<str:lang_code>/', views.set_language, name='set_language'),

    path('settings/', views.site_settings_view, name='site_settings'),
    path('preview-color/', views.preview_color, name='preview_color'),

    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),

]