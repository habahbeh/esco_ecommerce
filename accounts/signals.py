# accounts/signals.py
"""
إشارات تطبيق الحسابات
تستخدم لتنفيذ الإجراءات عند أحداث معينة مثل إنشاء المستخدم
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import UserProfile, User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    إنشاء ملف شخصي للمستخدم عند إنشاء مستخدم جديد
    Create user profile when user is created
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    حفظ الملف الشخصي للمستخدم عند حفظ المستخدم
    Save user profile when user is saved
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()