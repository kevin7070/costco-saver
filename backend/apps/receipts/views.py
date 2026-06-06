from django.http import FileResponse, Http404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Receipt
from .serializers import (
    ReceiptReviewSerializer,
    ReceiptSerializer,
    ReceiptUploadSerializer,
)
from .services import create_receipt


class ReceiptViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Upload, list, view, and confirm (review) the current user's receipts."""

    serializer_class = ReceiptSerializer

    def get_queryset(self):
        return (
            Receipt.objects.filter(user=self.request.user)
            .prefetch_related("line_items")
        )

    def create(self, request, *args, **kwargs):
        upload = ReceiptUploadSerializer(data=request.data)
        upload.is_valid(raise_exception=True)
        receipt = create_receipt(user=request.user, image=upload.validated_data["image"])
        return Response(ReceiptSerializer(receipt).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """User-corrected line items + fields → status confirmed."""
        receipt = self.get_object()
        serializer = ReceiptReviewSerializer(receipt, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        receipt.refresh_from_db()
        return Response(ReceiptSerializer(receipt).data)

    @action(detail=True, methods=["get"])
    def image(self, request, pk=None):
        """Serve the receipt image to its owner only.

        get_object() runs against the user-scoped queryset, so a cross-user id
        404s — this is the only authorized path to a receipt file (replaces the
        unauthenticated static media handler).
        """
        receipt = self.get_object()
        if not receipt.image:
            raise Http404
        response = FileResponse(receipt.image.open("rb"))
        response["X-Content-Type-Options"] = "nosniff"
        return response
