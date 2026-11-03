"""Automated test cases for catalog API."""

from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from catalog.models import Category, Product

class CategoryAPITests(APITestCase):
    """Test suite for Category endpoints."""

    def setUp(self):
        """Set up test environment."""
        self.user = User.objects.create_user(username='alice', password='password123')
        self.token = Token.objects.create(user=self.user)
        self.category = Category.objects.create(name='Electronics', slug='electronics')

    def test_given_unauthenticated_request_should_return_category_list(self):
        """Given an unauthenticated GET request, should return categories with status 200."""
        response = self.client.get('/api/v1/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_given_authenticated_request_should_create_category(self):
        """Given an authenticated POST request, should create category with status 201."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        payload = {'name': 'Books', 'slug': 'books'}
        response = self.client.post('/api/v1/categories/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 2)

    def test_given_unauthenticated_request_should_forbid_category_creation(self):
        """Given an unauthenticated POST request, should return status 401."""
        payload = {'name': 'Clothing', 'slug': 'clothing'}
        response = self.client.post('/api/v1/categories/', payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_given_authenticated_request_without_slug_should_auto_generate_slug(self):
        """Given an authenticated POST request without slug, should auto-generate slug with status 201."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        payload = {'name': 'Home Appliances'}
        response = self.client.post('/api/v1/categories/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['slug'], 'home-appliances')

    def test_given_authenticated_delete_request_should_delete_category(self):
        """Given an authenticated DELETE request, should remove category with status 204."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.delete(f'/api/v1/categories/{self.category.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(id=self.category.id).exists())

class ProductAPITests(APITestCase):
    """Test suite for Product endpoints."""

    def setUp(self):
        """Set up test environment."""
        self.alice = User.objects.create_user(username='alice', password='password123')
        self.bob = User.objects.create_user(username='bob', password='password123')
        self.token_alice = Token.objects.create(user=self.alice)
        self.token_bob = Token.objects.create(user=self.bob)

        self.category = Category.objects.create(name='Hardware', slug='hardware')
        self.product = Product.objects.create(
            owner=self.alice,
            category=self.category,
            name='Mechanical Keyboard',
            sku='KB-001',
            price=150.00,
            stock=10,
        )

    def test_given_unauthenticated_request_should_return_product_list(self):
        """Given an unauthenticated GET request, should return product list with status 200."""
        response = self.client.get('/api/v1/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_given_authenticated_request_should_create_product_with_owner(self):
        """Given an authenticated POST request, should associate owner and return status 201."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_alice.key}')
        payload = {
            'category': self.category.id,
            'name': 'Gaming Mouse',
            'sku': 'MS-002',
            'price': '75.00',
            'stock': 20,
        }
        response = self.client.post('/api/v1/products/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_product = Product.objects.get(sku='MS-002')
        self.assertEqual(created_product.owner, self.alice)

    def test_given_invalid_price_should_raise_validation_error(self):
        """Given a non-positive price, should return status 400."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_alice.key}')
        payload = {
            'category': self.category.id,
            'name': 'Broken Item',
            'sku': 'BRK-003',
            'price': '-10.00',
            'stock': 5,
        }
        response = self.client.post('/api/v1/products/', payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)

    def test_given_owner_should_allow_product_update(self):
        """Given the product owner, should allow PUT update with status 200."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_alice.key}')
        payload = {
            'category': self.category.id,
            'name': 'Updated Mechanical Keyboard',
            'sku': 'KB-001',
            'price': '160.00',
            'stock': 12,
        }
        response = self.client.put(f'/api/v1/products/{self.product.id}/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated Mechanical Keyboard')

    def test_given_non_owner_should_forbid_product_update(self):
        """Given a non-owner authenticated user, should reject PUT update with status 403."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_bob.key}')
        payload = {
            'category': self.category.id,
            'name': 'Tampered Keyboard',
            'sku': 'KB-001',
            'price': '10.00',
            'stock': 1,
        }
        response = self.client.put(f'/api/v1/products/{self.product.id}/', payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_given_owner_should_allow_restock_action(self):
        """Given the product owner, should increase inventory stock via custom action."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_alice.key}')
        response = self.client.post(f'/api/v1/products/{self.product.id}/restock/', {'amount': 15})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 25)

class ProductWebPageTests(APITestCase):
    """Test suite for the hybrid catalog frontend web page."""

    def test_given_get_request_should_render_product_list_template(self):
        """Given a GET request to the root URL, should render the catalog template with status 200."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'catalog/product_list.html')

    def test_given_unauthenticated_request_should_render_login_link(self):
        """Given an unauthenticated request, should render Guest label and login link."""
        response = self.client.get('/')
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, 'Guest')
        self.assertContains(response, '/auth/login/')
        self.assertContains(response, 'add-product-modal')
        self.assertContains(response, 'category-modal')
        self.assertContains(response, 'static/catalog/js/product_list.js')

    def test_given_authenticated_session_should_render_user_and_logout_link(self):
        """Given an authenticated session user, should render username and logout link."""
        user = User.objects.create_user(username='diana', password='password123')
        self.client.force_login(user)
        response = self.client.get('/')
        self.assertContains(response, 'Logged in: <strong>diana</strong>')
        self.assertContains(response, '/auth/logout/')


class ProductApproachesComparisonTests(APITestCase):
    """Test suite comparing FBV, CBV, ViewSet, and ModelViewSet implementations."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(username='charlie', password='password123')
        self.token = Token.objects.create(user=self.user)
        self.category = Category.objects.create(name='Gadgets', slug='gadgets')
        self.product = Product.objects.create(
            owner=self.user,
            category=self.category,
            name='USB Hub',
            sku='HUB-001',
            price=25.00,
            stock=5,
        )

    def test_given_fbv_endpoint_should_return_product_list(self):
        """Given a GET request to FBV endpoint, should return 200 with product list."""
        response = self.client.get('/api/v1/fbv/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_given_cbv_endpoint_should_return_product_list(self):
        """Given a GET request to CBV endpoint, should return 200 with paginated product list."""
        response = self.client.get('/api/v1/cbv/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_given_generic_viewset_endpoint_should_return_product_list(self):
        """Given a GET request to ViewSet endpoint, should return 200 with product list."""
        response = self.client.get('/api/v1/viewset/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_given_authenticated_user_should_create_product_via_fbv(self):
        """Given an authenticated POST request to FBV, should create product and assign owner."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        payload = {
            'name': 'Wireless Mouse',
            'sku': 'MOU-002',
            'price': '30.00',
            'stock': 12,
            'category': self.category.id,
        }
        response = self.client.post('/api/v1/fbv/products/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['owner'], 'charlie')


