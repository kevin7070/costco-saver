"""Shared fixtures for all tests."""

from django.conf import settings

# Disable django-axes during tests — it needs middleware/request plumbing
# that DRF APIClient doesn't provide. Real-world brute-force protection
# should be tested with a live runserver or dedicated integration tests.
if "axes.backends.AxesBackend" in settings.AUTHENTICATION_BACKENDS:
    settings.AUTHENTICATION_BACKENDS = [
        b for b in settings.AUTHENTICATION_BACKENDS
        if b != "axes.backends.AxesBackend"
    ]

import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient

from .factories import ItemFactory, UserFactory

register(UserFactory)
register(ItemFactory)


@pytest.fixture
def api_client():
    """Unauthenticated API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Plain user (user_type='user')."""
    return UserFactory()


@pytest.fixture
def admin_user(db):
    """Admin user (user_type='admin')."""
    return UserFactory(user_type="admin")


@pytest.fixture
def user_client(user):
    """API client authenticated as plain user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_client(admin_user):
    """API client authenticated as admin."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
