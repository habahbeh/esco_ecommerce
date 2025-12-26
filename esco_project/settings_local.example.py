"""
Example local settings - Copy this file to settings_local.py and fill in your values
مثال على الإعدادات المحلية - انسخ هذا الملف إلى settings_local.py واملأ القيم

INSTRUCTIONS:
1. Copy this file to settings_local.py
2. Fill in your actual credentials
3. Never commit settings_local.py to git!

التعليمات:
1. انسخ هذا الملف إلى settings_local.py
2. املأ بياناتك الفعلية
3. لا ترفع settings_local.py إلى git أبداً!
"""

# SECURITY WARNING: keep the secret key used in production secret!
# Generate a new one for production: https://djecrety.ir/
# مفتاح الأمان - يجب أن يبقى سرياً
# أنشئ مفتاحاً جديداً للإنتاج
SECRET_KEY = 'your-secret-key-here-generate-a-new-one'

# Debug mode - set to False in production
# وضع التطوير - اضبطه على False في الإنتاج
DEBUG = True

# Database configuration
# إعدادات قاعدة البيانات
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'your_database_name',
        'USER': 'your_database_user',
        'PASSWORD': 'your_database_password',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'autocommit': True,
        }
    }
}

# Email configuration
# إعدادات البريد الإلكتروني
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'Your Name <your-email@example.com>'

# Allowed hosts - add your domain in production
# المضيفين المسموح بهم - أضف نطاقك في الإنتاج
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'your-domain.com']
