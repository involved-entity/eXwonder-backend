import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery(
    "eXwonder", include=["users.tasks"], broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND
)

app.conf.task_queues = {
    "normal_priority": {
        "exchange": "normal_priority",
        "routing_key": "normal_priority",
    },
    "high_priority": {
        "exchange": "high_priority",
        "routing_key": "high_priority",
    },
}

app.conf.task_routes = {
    "users.tasks.make_center_crop": {"queue": "high_priority"},
    "users.tasks.send_reset_password_mail": {"queue": "normal_priority"},
    "users.tasks.send_2fa_code_mail_message": {"queue": "normal_priority"},
}

app.autodiscover_tasks()
