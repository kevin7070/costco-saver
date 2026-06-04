from django.contrib import admin

from .models import LineItem, Receipt


class LineItemInline(admin.TabularInline):
    model = LineItem
    extra = 0


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "store_location", "purchase_date",
        "receipt_number", "parse_status", "created_at",
    )
    list_filter = ("parse_status", "purchase_date")
    search_fields = ("receipt_number", "invoice_number", "store_location", "user__email")
    readonly_fields = ("raw_parse", "created_at", "updated_at")
    inlines = [LineItemInline]


@admin.register(LineItem)
class LineItemAdmin(admin.ModelAdmin):
    list_display = (
        "raw_name", "item_number", "item_type",
        "unit_price", "amount", "taxable", "tracking_status",
    )
    list_filter = ("item_type", "tracking_status", "taxable")
    search_fields = ("raw_name", "item_number")
