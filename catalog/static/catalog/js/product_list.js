/**
 * BambangShop Catalog Client-Side JavaScript
 * Communicates with Django REST Framework backend using AJAX (Fetch API)
 * with session-based authentication and CSRF token protection.
 */

const BASE_PRODUCTS_ENDPOINT = "/api/v1/products/";
const BASE_CATEGORIES_ENDPOINT = "/api/v1/categories/";

let productsAbortController;
let searchDebounceTimer;

// Helper function to extract CSRF token cookie for mutating requests
function getCookie(name) {
    const prefix = `${name}=`;
    const cookie = document.cookie
        .split(';')
        .map(value => value.trim())
        .find(value => value.startsWith(prefix));
    return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : null;
}

// Sanitize user-generated input against XSS
function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

// Visual feedback toasts
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

// Toggle loading, error, empty, and populated grid states
function displayPageSection({ showLoading = false, showError = false, showEmpty = false, showGrid = false }) {
    const loadingState = document.getElementById('loading');
    const errorState = document.getElementById('error');
    const emptyState = document.getElementById('empty');
    const gridContainer = document.getElementById('grid');

    if (loadingState) loadingState.classList.toggle('hide', !showLoading);
    if (errorState) errorState.classList.toggle('hide', !showError);
    if (emptyState) emptyState.classList.toggle('hide', !showEmpty);
    if (gridContainer) gridContainer.classList.toggle('hide', !showGrid);
}

// Construct product card DOM element
function buildProductCardElement(product) {
    const card = document.createElement('article');
    card.className = 'product-card';

    const formattedPrice = Number(product.price).toFixed(2);
    const stockStatusClass = product.stock > 0 ? 'in-stock' : 'out-of-stock';
    const stockStatusText = product.stock > 0 ? `${product.stock} units available` : 'Out of stock';

    card.innerHTML = `
        <div>
            <div class="product-header">
                <h2 class="product-title">${escapeHtml(product.name)}</h2>
                <span class="badge badge-category">${escapeHtml(product.category_name || 'General')}</span>
            </div>
            <span class="badge badge-sku">SKU: ${escapeHtml(product.sku)}</span>
            <div class="product-details">
                <div class="product-price">$${escapeHtml(formattedPrice)}</div>
                <div class="product-stock ${stockStatusClass}">${escapeHtml(stockStatusText)}</div>
                <div class="product-meta">Owner: ${escapeHtml(product.owner || 'System')}</div>
            </div>
        </div>
        <div class="product-actions">
            <button type="button" class="button button-sm button-restock" data-action="restock" data-id="${escapeHtml(product.id)}">
                + Restock (5)
            </button>
            <button type="button" class="button button-sm button-danger" data-action="delete" data-id="${escapeHtml(product.id)}">
                Delete
            </button>
        </div>
    `;
    return card;
}

// Parse DRF validation or generic error response
function apiErrorMessage(data, status) {
    if (!data || typeof data !== 'object') {
        return `Request failed with HTTP ${status}.`;
    }
    if (data.detail) {
        return data.detail;
    }
    const messages = Object.entries(data)
        .map(([field, err]) => `${field}: ${Array.isArray(err) ? err.join(' ') : err}`);
    return messages.join(' | ') || `Request failed with HTTP ${status}.`;
}

// Reusable mutating request helper sending X-CSRFToken header
async function writeApi(url, method, payload) {
    const csrfToken = getCookie('csrftoken');
    const headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    };
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
    }

    const response = await fetch(url, {
        method: method,
        headers: headers,
        body: payload !== undefined ? JSON.stringify(payload) : undefined,
    });

    if (response.status === 204) {
        return null;
    }

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(apiErrorMessage(data, response.status));
    }
    return data;
}

// Retrieve catalog products with debounced search and category filtering
async function fetchProducts(searchQuery = '', categoryId = '') {
    if (productsAbortController) {
        productsAbortController.abort();
    }
    productsAbortController = new AbortController();

    const gridContainer = document.getElementById('grid');
    try {
        displayPageSection({ showLoading: true });
        const url = new URL(BASE_PRODUCTS_ENDPOINT, window.location.origin);
        if (searchQuery) url.searchParams.set('search', searchQuery);
        if (categoryId) url.searchParams.set('category', categoryId);

        const response = await fetch(url, {
            headers: { 'Accept': 'application/json' },
            signal: productsAbortController.signal,
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const payload = await response.json();
        const products = Array.isArray(payload) ? payload : (payload.results || []);

        if (gridContainer) {
            gridContainer.replaceChildren(...products.map(buildProductCardElement));
        }
        displayPageSection({
            showGrid: products.length > 0,
            showEmpty: products.length === 0,
        });
    } catch (error) {
        if (error.name === 'AbortError') return;
        console.error(error);
        displayPageSection({ showError: true });
    }
}

// Populate category management list
function renderCategoryList(categories) {
    const categoryListContainer = document.getElementById('category-list');
    if (!categoryListContainer) return;
    categoryListContainer.innerHTML = '';
    if (categories.length === 0) {
        categoryListContainer.innerHTML = '<div style="color: var(--text-muted); font-size: 0.85rem; padding: 8px 0;">No categories registered yet.</div>';
        return;
    }
    categories.forEach(cat => {
        const item = document.createElement('div');
        item.style.cssText = 'display: flex; justify-content: space-between; align-items: center; padding: 8px 10px; background-color: var(--background); border-radius: 6px; border: 1px solid var(--border);';
        item.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-weight: 600; font-size: 0.9rem;">${escapeHtml(cat.name)}</span>
                <span class="badge badge-sku">${escapeHtml(cat.slug)}</span>
            </div>
            <button type="button" class="button button-sm button-danger" data-category-action="delete" data-id="${escapeHtml(cat.id)}" style="padding: 2px 8px; font-size: 0.75rem;">
                Delete
            </button>
        `;
        categoryListContainer.appendChild(item);
    });
}

// Load categories to populate form dropdown and filter selector
async function loadCategories(selectedId = null) {
    const categorySelect = document.getElementById('product-category');
    const categoryFilter = document.getElementById('category-filter');
    try {
        const response = await fetch(BASE_CATEGORIES_ENDPOINT, {
            headers: { 'Accept': 'application/json' }
        });
        if (!response.ok) return;
        const data = await response.json();
        const categories = Array.isArray(data) ? data : (data.results || []);

        if (categorySelect) {
            const currentSelected = selectedId || categorySelect.value;
            categorySelect.innerHTML = '<option value="">Select a category...</option>';
            categories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.id;
                option.textContent = cat.name;
                if (String(cat.id) === String(currentSelected)) {
                    option.selected = true;
                }
                categorySelect.appendChild(option);
            });
        }

        if (categoryFilter) {
            const currentFilter = categoryFilter.value;
            categoryFilter.innerHTML = '<option value="">All Categories</option>';
            categories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.id;
                option.textContent = cat.name;
                if (String(cat.id) === String(currentFilter)) {
                    option.selected = true;
                }
                categoryFilter.appendChild(option);
            });
        }

        renderCategoryList(categories);
    } catch (err) {
        console.error('Failed to load categories', err);
    }
}
window.loadCategories = loadCategories;

// Handle Product creation form submission
async function addProduct(event) {
    event.preventDefault();
    const productForm = document.getElementById('product-form');
    const addProductModal = document.getElementById('add-product-modal');
    const searchInput = document.getElementById('search-input');
    const categoryFilter = document.getElementById('category-filter');
    const submitBtn = productForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;

    try {
        const formData = new FormData(productForm);
        const payload = {
            name: formData.get('name'),
            sku: formData.get('sku'),
            category: parseInt(formData.get('category'), 10),
            price: formData.get('price'),
            stock: parseInt(formData.get('stock'), 10) || 0,
        };

        await writeApi(BASE_PRODUCTS_ENDPOINT, 'POST', payload);
        productForm.reset();
        if (addProductModal) addProductModal.classList.add('hide');
        showToast('Product created successfully.', 'success');
        await fetchProducts(searchInput?.value.trim() || '', categoryFilter?.value || '');
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.disabled = false;
    }
}

// Handle Category creation form submission
async function addCategory(event) {
    event.preventDefault();
    const categoryForm = document.getElementById('category-form');
    const categoryModal = document.getElementById('category-modal');
    const addProductModal = document.getElementById('add-product-modal');
    const submitBtn = document.getElementById('save-category-btn');
    if (submitBtn) submitBtn.disabled = true;

    try {
        const formData = new FormData(categoryForm);
        const name = formData.get('name').trim();
        const slug = formData.get('slug').trim();
        const payload = { name };
        if (slug) payload.slug = slug;

        const newCategory = await writeApi(BASE_CATEGORIES_ENDPOINT, 'POST', payload);
        categoryForm.reset();
        showToast(`Category "${newCategory.name}" created successfully.`, 'success');
        await loadCategories(newCategory.id);
        if (addProductModal && !addProductModal.classList.contains('hide') && categoryModal) {
            categoryModal.classList.add('hide');
        }
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        if (submitBtn) submitBtn.disabled = false;
    }
}

// Initialize listeners on DOM load
document.addEventListener('DOMContentLoaded', () => {
    const productForm = document.getElementById('product-form');
    const categoryForm = document.getElementById('category-form');
    const categoryListContainer = document.getElementById('category-list');
    const gridContainer = document.getElementById('grid');
    const categoryFilter = document.getElementById('category-filter');
    const searchInput = document.getElementById('search-input');

    if (productForm) productForm.addEventListener('submit', addProduct);
    if (categoryForm) categoryForm.addEventListener('submit', addCategory);

    // Event delegation on category list for delete buttons
    if (categoryListContainer) {
        categoryListContainer.addEventListener('click', async (event) => {
            const button = event.target.closest('button[data-category-action="delete"]');
            if (!button || button.disabled) return;

            const catId = button.dataset.id;
            if (!window.confirm('Are you sure you want to delete this category? Associated products may be affected.')) {
                return;
            }

            button.disabled = true;
            try {
                await writeApi(`${BASE_CATEGORIES_ENDPOINT}${catId}/`, 'DELETE');
                showToast('Category deleted successfully.', 'success');
                await loadCategories();
                await fetchProducts(searchInput?.value.trim() || '', categoryFilter?.value || '');
            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                button.disabled = false;
            }
        });
    }

    // Event delegation on grid container for restock and delete actions
    if (gridContainer) {
        gridContainer.addEventListener('click', async (event) => {
            const button = event.target.closest('button[data-action]');
            if (!button || button.disabled) return;

            const action = button.dataset.action;
            const productId = button.dataset.id;

            if (action === 'delete') {
                if (!window.confirm('Are you sure you want to delete this merchandise?')) {
                    return;
                }
            }

            button.disabled = true;
            try {
                if (action === 'restock') {
                    await writeApi(`${BASE_PRODUCTS_ENDPOINT}${productId}/restock/`, 'POST', { amount: 5 });
                    showToast('Product inventory restocked by 5 units.', 'success');
                } else if (action === 'delete') {
                    await writeApi(`${BASE_PRODUCTS_ENDPOINT}${productId}/`, 'DELETE');
                    showToast('Product successfully removed from catalog.', 'success');
                }
                await fetchProducts(searchInput?.value.trim() || '', categoryFilter?.value || '');
            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                button.disabled = false;
            }
        });
    }

    // Category filter selector
    if (categoryFilter) {
        categoryFilter.addEventListener('change', () => {
            fetchProducts(searchInput?.value.trim() || '', categoryFilter.value);
        });
    }

    // Search input with debounce
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(searchDebounceTimer);
            searchDebounceTimer = setTimeout(() => {
                fetchProducts(searchInput.value.trim(), categoryFilter?.value || '');
            }, 300);
        });
    }

    // Initial load
    fetchProducts();
    loadCategories();
});
