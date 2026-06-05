"""Celery application for costco-saver.

Background tasks and scheduling. Receipt parsing runs on an on-demand,
single-concurrency, retryable queue; other jobs run on their own schedules.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("costco_saver")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
