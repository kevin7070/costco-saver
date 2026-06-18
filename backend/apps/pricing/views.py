"""Pricing views — price alert management."""

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import PriceAlert
from .serializers import PriceAlertSerializer


class PriceAlertViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Read and update the current user's price-drop alerts.

    List/detail are scoped to the authenticated user — cross-user IDs 404.
    Status transitions (mark_seen, mark_actioned, dismiss) are idempotent.
    """

    serializer_class = PriceAlertSerializer

    def get_queryset(self):
        qs = (
            PriceAlert.objects.filter(user=self.request.user)
            .select_related("line_item__product", "line_item__receipt")
        )
        # Optional ?status= filter (e.g. ?status=open)
        s = self.request.query_params.get("status")
        if s:
            qs = qs.filter(status=s)
        return qs

    def _set_status(self, new_status: str) -> Response:
        alert = self.get_object()
        alert.status = new_status
        alert.save(update_fields=["status", "updated_at"])
        return Response(PriceAlertSerializer(alert).data)

    @action(detail=True, methods=["post"], url_path="mark-seen")
    def mark_seen(self, request, pk=None):
        """Mark the alert as seen (user noticed it in the UI)."""
        return self._set_status(PriceAlert.Status.SEEN)

    @action(detail=True, methods=["post"], url_path="mark-actioned")
    def mark_actioned(self, request, pk=None):
        """Mark the alert as actioned (user requested the price adjustment)."""
        return self._set_status(PriceAlert.Status.ACTIONED)

    @action(detail=True, methods=["post"], url_path="dismiss")
    def dismiss(self, request, pk=None):
        """Dismiss the alert (user does not intend to act on it)."""
        return self._set_status(PriceAlert.Status.DISMISSED)
