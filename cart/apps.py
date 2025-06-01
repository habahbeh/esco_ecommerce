# cart/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CartConfig(AppConfig):
    """
    Cart application configuration
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cart'
    verbose_name = _('سلة التسوق')

    def ready(self):
        import cart.signals


