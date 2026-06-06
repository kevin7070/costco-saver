"""Celery tasks for transactional auth emails (async, off the request path)."""

from __future__ import annotations

from celery import shared_task
from django.contrib.auth import get_user_model

from . import emails


@shared_task(name="apps.users.tasks.send_verification_email")
def send_verification_email(user_id: str) -> None:
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return
    emails.send_verification_email(user)


@shared_task(name="apps.users.tasks.send_already_registered_email")
def send_already_registered_email(email: str) -> None:
    emails.send_already_registered_email(email)


@shared_task(name="apps.users.tasks.send_password_reset_email")
def send_password_reset_email(user_id: str, token: str) -> None:
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return
    emails.send_password_reset_email(user, token)
