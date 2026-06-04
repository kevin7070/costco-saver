"""Item URL routes."""

from rest_framework.routers import DefaultRouter

from .views import ItemViewSet

app_name = "items"

router = DefaultRouter()
router.register(r"", ItemViewSet, basename="item")

urlpatterns = router.urls
