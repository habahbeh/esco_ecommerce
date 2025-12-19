# fix_migrations.py
import os
import sys
import django
from django.conf import settings

# تعطيل كل المشاكل
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esco_project.settings')

# Override الإعدادات المشكلة
settings.TEMPLATES[0]['OPTIONS']['context_processors'] = [
    'django.template.context_processors.debug',
    'django.template.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
]

# تعطيل أي middleware مشكلة
settings.MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

django.setup()

# الآن شغل migrations
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'migrate'])