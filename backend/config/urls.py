"""URL configuration for costco-saver."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # API v1
    path("api/v1/auth/", include("apps.users.urls", namespace="auth")),
    path("api/v1/items/", include("apps.items.urls", namespace="items")),
    path("api/v1/", include("apps.receipts.urls")),
]

if settings.DEBUG:
    # Static assets only — receipt media is served by an authorized view
    # (ReceiptViewSet.image), never by an unauthenticated static handler.
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
