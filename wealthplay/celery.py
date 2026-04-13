import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wealthplay.settings')

app = Celery('wealthplay')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

