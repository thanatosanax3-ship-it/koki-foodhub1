
from django.contrib import admin
from .models import Product, InventoryItem, Sale

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_active")
    search_fields = ("name", "category")

@admin.register(InventoryItem)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "quantity", "reorder_point", "updated_at")
    search_fields = ("sku", "product__name")

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("product", "date", "units_sold", "revenue")
    list_filter = ("date", "product")
