"""Serializers for catalog models."""

from rest_framework import serializers
from catalog.models import Category, Product

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for the Category model."""

    slug = serializers.SlugField(required=False)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

    def create(self, validated_data):
        """Create category with auto-generated slug if omitted."""
        if not validated_data.get('slug'):
            from django.utils.text import slugify
            validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update category with auto-generated slug if name changed and slug omitted."""
        if 'name' in validated_data and not validated_data.get('slug'):
            from django.utils.text import slugify
            validated_data['slug'] = slugify(validated_data['name'])
        return super().update(instance, validated_data)

class ProductSerializer(serializers.ModelSerializer):
    """Serializer for the Product model with validation rules."""

    owner = serializers.ReadOnlyField(source='owner.username')
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'sku',
            'price',
            'stock',
            'category',
            'category_name',
            'owner',
            'created_at',
        ]
        read_only_fields = ['id', 'owner', 'created_at']

    def validate_price(self, value):
        """Validate that product price is strictly positive."""
        if value <= 0:
            raise serializers.ValidationError("Product price must be greater than zero.")
        return value

    def validate_stock(self, value):
        """Validate that product stock is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Product stock cannot be negative.")
        return value
