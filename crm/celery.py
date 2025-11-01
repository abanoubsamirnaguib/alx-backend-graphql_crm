import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')

app = Celery('crm')

# يأخذ إعدادات CELERY_* من Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# يكتشف المهام تلقائياً من كل apps
app.autodiscover_tasks()