import pymysql
pymysql.version_info = (1, 4, 12, "final", 0)
pymysql.install_as_MySQLdb()

# أضف هذا السطر - خدعة Django
# from django.db.backends.mysql import base
# base.require_version = lambda self: None