/**
 * BambangShop Modal UI Management
 * Encapsulates modal display, closing, and backdrop dismissal.
 */
document.addEventListener('DOMContentLoaded', () => {
    const addProductModal = document.getElementById('add-product-modal');
    const openModalBtn = document.getElementById('open-modal-btn');
    const closeModalBtn = document.getElementById('close-modal-btn');

    const categoryModal = document.getElementById('category-modal');
    const openCategoryModalBtn = document.getElementById('open-category-modal-btn');
    const closeCategoryModalBtn = document.getElementById('close-category-modal-btn');
    const quickAddCategoryBtn = document.getElementById('quick-add-category-btn');

    function openProductModal() {
        if (typeof window.loadCategories === 'function') {
            window.loadCategories();
        }
        if (addProductModal) addProductModal.classList.remove('hide');
    }

    function closeProductModal() {
        if (addProductModal) addProductModal.classList.add('hide');
    }

    function openCategoryModal() {
        if (typeof window.loadCategories === 'function') {
            window.loadCategories();
        }
        if (categoryModal) categoryModal.classList.remove('hide');
    }

    function closeCategoryModal() {
        if (categoryModal) categoryModal.classList.add('hide');
    }

    // Attach listeners
    if (openModalBtn) openModalBtn.addEventListener('click', openProductModal);
    if (closeModalBtn) closeModalBtn.addEventListener('click', closeProductModal);
    if (addProductModal) {
        addProductModal.addEventListener('click', (e) => {
            if (e.target === addProductModal) closeProductModal();
        });
    }

    if (openCategoryModalBtn) openCategoryModalBtn.addEventListener('click', openCategoryModal);
    if (closeCategoryModalBtn) closeCategoryModalBtn.addEventListener('click', closeCategoryModal);
    if (quickAddCategoryBtn) quickAddCategoryBtn.addEventListener('click', openCategoryModal);
    if (categoryModal) {
        categoryModal.addEventListener('click', (e) => {
            if (e.target === categoryModal) closeCategoryModal();
        });
    }

    // Expose helpers globally for other scripts
    window.openProductModal = openProductModal;
    window.closeProductModal = closeProductModal;
    window.openCategoryModal = openCategoryModal;
    window.closeCategoryModal = closeCategoryModal;
});
