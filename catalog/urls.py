"""URL routing configuration for catalog API."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from catalog.views import (
    CategoryViewSet,
    ProductViewSet,
    product_list_page,
    product_list_fbv,
    product_detail_fbv,
    ProductListAPIView,
    ProductDetailAPIView,
    ProductGenericViewSet,
)

# Automated router for ModelViewSets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'viewset/products', ProductGenericViewSet, basename='product-viewset')

urlpatterns = [
    # Frontend HTML view
    path('', product_list_page, name='product-list-page'),

    # Approach 1: Function-Based Views (FBV with @api_view)
    path('api/v1/fbv/products/', product_list_fbv, name='product-fbv-list'),
    path('api/v1/fbv/products/<int:pk>/', product_detail_fbv, name='product-fbv-detail'),

    # Approach 2: Class-Based Views (Concrete Generics: APIView)
    path('api/v1/cbv/products/', ProductListAPIView.as_view(), name='product-cbv-list'),
    path('api/v1/cbv/products/<int:pk>/', ProductDetailAPIView.as_view(), name='product-cbv-detail'),

    # Approach 3 & 4: Router endpoints (Generic ViewSet & ModelViewSet)
    path('api/v1/', include(router.urls)),
]

