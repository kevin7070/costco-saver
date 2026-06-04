"""Item ViewSet — demonstrates the thin-view + service-first pattern."""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Item
from .serializers import ItemSerializer
from .services import archive_item


class ItemViewSet(viewsets.ModelViewSet):
    """CRUD for items owned by the current user.

    List/detail scoped to the current user. Status transitions
    (archive) go through the service layer.
    """

    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Item.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        """Archive an active item.

        POST /api/v1/items/{id}/archive/
        """
        item = self.get_object()
        try:
            archive_item(item)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(ItemSerializer(item).data)
