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
from .tasks import catalog_match_receipt


class ReceiptViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Upload, list, view, confirm (review), and delete the current user's receipts."""

    serializer_class = ReceiptSerializer

    def get_queryset(self):
        return (
            Receipt.objects.filter(user=self.request.user)
            .prefetch_related("line_items")
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a receipt (row + file) once it is the user's to remove.

        Blocked while the AI is still in flight (queued/processing) and before
        the data is confirmed (needs_review): only `confirmed`/`failed` receipts
        are deletable. The post_delete signal removes the stored file.
        """
        receipt = self.get_object()  # user-scoped queryset → cross-user 404
        if not receipt.user_can_delete:
            return Response(
                {"detail": "This receipt can't be deleted until processing is "
                           "complete and the data is confirmed."},
                status=status.HTTP_409_CONFLICT,
            )
        receipt.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        upload = ReceiptUploadSerializer(data=request.data)
        upload.is_valid(raise_exception=True)
        receipt = create_receipt(user=request.user, image=upload.validated_data["image"])
        return Response(ReceiptSerializer(receipt).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """User-corrected line items + fields → status confirmed, then catalog matching."""
        receipt = self.get_object()
        serializer = ReceiptReviewSerializer(receipt, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        receipt.refresh_from_db()
        catalog_match_receipt.delay(str(receipt.pk))
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
        # Force a safe content-type from an allowlist — never trust the stored
        # filename's extension (an evil.html upload must not serve as HTML).
        import mimetypes

        guessed, _ = mimetypes.guess_type(receipt.image.name)
        content_type = (
            guessed
            if guessed in ("image/jpeg", "image/png", "application/pdf")
            else "application/octet-stream"
        )
        response = FileResponse(receipt.image.open("rb"), content_type=content_type)
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Disposition"] = "inline"
        return response
