import os

from celery import Celery
from celery.beat import crontab
from celery.schedules import crontab

print(">>> users.tasks imported")

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

# Explicitly include users.tasks so Celery will import that module and
# register the tasks. autodiscover_tasks() is still used to pick up tasks from
# all apps, but adding include makes registration robust in some environments.
app = Celery('main', include=['users.tasks'])

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "send_daily_report": {
        "task": "users.tasks.send_daily_report",
        "schedule": crontab(minute="*")
    }
}
