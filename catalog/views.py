"""API views and viewsets for catalog application."""

from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, generics, permissions, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from catalog.models import Category, Product
from catalog.serializers import CategorySerializer, ProductSerializer
from catalog.permissions import IsOwnerOrReadOnly


def product_list_page(request):
    """Render the BambangShop product catalog web page."""
    return render(request, 'catalog/product_list.html')


# =============================================================================
# Approach 1: Function-Based Views (FBV with @api_view)
# =============================================================================

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def product_list_fbv(request):
    """Handle collection operations for products using function-based view."""
    if request.method == 'GET':
        products = Product.objects.all().order_by('-created_at')
        category_id = request.query_params.get('category')
        if category_id:
            products = products.filter(category_id=category_id)
        search_query = request.query_params.get('search')
        if search_query:
            products = products.filter(name__icontains=search_query)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def product_detail_fbv(request, pk):
    """Handle item operations for a single product using function-based view."""
    product = get_object_or_404(Product, pk=pk)

    if request.method in ['PUT', 'PATCH', 'DELETE']:
        permission = IsOwnerOrReadOnly()
        if not permission.has_object_permission(request, None, product):
            return Response(
                {'detail': 'You do not have permission to perform this action.'},
                status=status.HTTP_403_FORBIDDEN
            )

    if request.method == 'GET':
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = (request.method == 'PATCH')
        serializer = ProductSerializer(product, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================================================
# Approach 2: Class-Based Views (Concrete Generics: ListCreate & RetrieveUpdateDestroy)
# =============================================================================

class ProductListAPIView(generics.ListCreateAPIView):
    """Collection endpoint implemented via Concrete Generic Views."""

    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'sku']
    ordering_fields = ['price', 'created_at']

    def perform_create(self, serializer):
        """Associate newly created product with the authenticated user."""
        serializer.save(owner=self.request.user)


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Item endpoint implemented via Concrete Generic Views."""

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]


# =============================================================================
# Approach 3: Generic ViewSet (Semantic action methods without ModelViewSet derivation)
# =============================================================================

class ProductGenericViewSet(viewsets.ViewSet):
    """Resource lifecycle controller using explicit action handlers."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def list(self, request):
        """List products with optional category filtering."""
        queryset = Product.objects.all().order_by('-created_at')
        category_id = request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        serializer = ProductSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Create new product associating requesting user as owner."""
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """Retrieve single product by primary key."""
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def update(self, request, pk=None):
        """Update product instance verifying owner permissions."""
        product = get_object_or_404(Product, pk=pk)
        self.check_object_permissions(request, product)
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Delete product instance verifying owner permissions."""
        product = get_object_or_404(Product, pk=pk)
        self.check_object_permissions(request, product)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================================================
# Approach 4: ModelViewSet (Full automatic CRUD lifecycle abstraction)
# =============================================================================

class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing product categories."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    """ModelViewSet for managing catalog products with search, filtering, and ordering."""

    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'sku']
    ordering_fields = ['price', 'created_at']

    def perform_create(self, serializer):
        """Associate newly created product with the authenticated user."""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrReadOnly])
    def restock(self, request, pk=None):
        """Increase inventory stock for a product."""
        product = self.get_object()
        amount = int(request.data.get('amount', 0))
        if amount <= 0:
            return Response(
                {'error': 'Restock amount must be greater than zero.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        product.stock += amount
        product.save()
        return Response(
            {'status': 'stock updated', 'current_stock': product.stock},
            status=status.HTTP_200_OK
        )

