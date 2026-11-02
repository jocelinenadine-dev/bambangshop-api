"""Admin site registrations for catalog application."""

from django.contrib import admin
from catalog.models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category model."""

    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for Product model."""

    list_display = (
        'id',
        'name',
        'sku',
        'category',
        'price',
        'stock',
        'owner',
        'created_at',
    )
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'sku')
    raw_id_fields = ('owner',)
    date_hierarchy = 'created_at'
