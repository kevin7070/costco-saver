"""Reusable user-field validators."""

from __future__ import annotations

from rest_framework import serializers


def validate_not_disposable(email: str) -> None:
    """Reject disposable / throwaway email domains (anti-abuse)."""
    from disposable_email_domains import blocklist

    domain = email.rsplit("@", 1)[-1].lower().strip().rstrip(".")
    # Check the domain and every parent (sub.mailinator.com -> mailinator.com).
    labels = domain.split(".")
    if any(
        ".".join(labels[i:]) in blocklist for i in range(max(len(labels) - 1, 1))
    ):
        raise serializers.ValidationError(
            "Disposable email addresses are not allowed."
        )
