"""Pricing URL routes."""

from rest_framework.routers import DefaultRouter

from .views import PriceAlertViewSet

app_name = "pricing"

router = DefaultRouter()
router.register(r"alerts", PriceAlertViewSet, basename="alert")

urlpatterns = router.urls
