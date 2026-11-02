"""Application configuration for catalog app."""

from django.apps import AppConfig

class CatalogConfig(AppConfig):
    """Configuration class for the catalog application."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog'
