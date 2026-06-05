from django.contrib import admin

from .models import PriceAlert, PriceObservation, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("item_number", "name", "current_price", "on_sale", "last_checked")
    search_fields = ("item_number", "name")


@admin.register(PriceObservation)
class PriceObservationAdmin(admin.ModelAdmin):
    list_display = ("product", "price", "on_sale", "observed_at")
    list_filter = ("on_sale",)


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ("line_item", "user", "delta", "within_adjustment_window", "status", "created_at")
    list_filter = ("status", "within_adjustment_window")
