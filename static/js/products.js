/**
 * Products JavaScript Functions
 * وظائف جافاسكريبت للمنتجات
 */

// Product Quick View
function showQuickView(productId) {
    // Show loading modal
    const modalHtml = `
        <div class="modal fade" id="quickViewModal" tabindex="-1">
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-body text-center p-5">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">جاري التحميل...</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('quickViewModal'));
    modal.show();

    // Fetch product data
    fetch(`/products/api/product/${productId}/quick-view/`)
        .then(response => response.json())
        .then(data => {
            // Update modal content
            const modalContent = `
                <div class="modal-header">
                    <h5 class="modal-title">${data.name}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <div class="col-md-6">
                            <img src="${data.image}" class="img-fluid rounded" alt="${data.name}">
                        </div>
                        <div class="col-md-6">
                            <p class="text-muted mb-2">${data.category.name}</p>
                            <div class="mb-3">
                                ${data.rating > 0 ? `
                                    <div class="rating mb-2">
                                        ${generateStars(data.rating)}
                                        <span class="ms-2">(${data.review_count} تقييم)</span>
                                    </div>
                                ` : ''}
                            </div>
                            <div class="price mb-3">
                                ${data.has_discount ? `
                                    <span class="h4 text-primary">${data.price} د.أ</span>
                                    <span class="text-muted text-decoration-line-through ms-2">${data.base_price}</span>
                                    <span class="badge bg-danger ms-2">${data.discount_percentage}% خصم</span>
                                ` : `
                                    <span class="h4 text-primary">${data.price} د.أ</span>
                                `}
                            </div>
                            <p class="mb-4">${data.short_description || ''}</p>
                            <div class="stock-status mb-4">
                                ${data.in_stock ? 
                                    '<span class="text-success"><i class="fas fa-check-circle"></i> متوفر في المخزن</span>' :
                                    '<span class="text-danger"><i class="fas fa-times-circle"></i> غير متوفر</span>'
                                }
                            </div>
                            <div class="d-flex gap-2">
                                <button class="btn btn-primary flex-fill" onclick="addToCart(${data.id}, 1)" ${!data.in_stock ? 'disabled' : ''}>
                                    <i class="fas fa-shopping-cart me-2"></i>أضف للسلة
                                </button>
                                <a href="${data.url}" class="btn btn-outline-primary">
                                    <i class="fas fa-eye me-2"></i>عرض التفاصيل
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.querySelector('#quickViewModal .modal-content').innerHTML = modalContent;
        })
        .catch(error => {
            console.error('Error:', error);
            modal.hide();
            showNotification('حدث خطأ في تحميل المنتج', 'error');
        });
}

// Add to Cart
function addToCart(productId, quantity = 1, variantId = null) {
    const formData = new FormData();
    formData.append('quantity', quantity);
    if (variantId) {
        formData.append('variant_id', variantId);
    }
    formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

    fetch(`/cart/add/${productId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message || 'تمت إضافة المنتج إلى السلة', 'success');
            updateCartCount(data.cart_count);

            // Animate cart icon
            animateCartIcon();
        } else {
            showNotification(data.message || 'حدث خطأ', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('حدث خطأ في إضافة المنتج', 'error');
    });
}

// Add to Wishlist
function toggleWishlist(productId, button) {
    if (!window.userAuthenticated) {
        window.location.href = '/accounts/login/?next=' + window.location.pathname;
        return;
    }

    const isInWishlist = button.classList.contains('active');
    const url = isInWishlist ?
        `/products/api/wishlist/remove/${productId}/` :
        `/products/api/wishlist/add/${productId}/`;

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            button.classList.toggle('active');
            const icon = button.querySelector('i');
            icon.classList.toggle('far');
            icon.classList.toggle('fas');

            showNotification(data.message, 'success');
            updateWishlistCount(data.wishlist_count);
        } else {
            showNotification(data.message || 'حدث خطأ', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('حدث خطأ', 'error');
    });
}

// Add to Comparison
function addToComparison(productId) {
    const formData = new FormData();
    formData.append('product_id', productId);
    formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

    fetch('/products/api/compare/add/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            updateComparisonCount(data.comparison_count);
        } else {
            showNotification(data.message || 'حدث خطأ', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('حدث خطأ', 'error');
    });
}

// Update Cart Count
function updateCartCount(count) {
    const cartBadge = document.querySelector('.cart-badge');
    if (cartBadge) {
        if (count > 0) {
            cartBadge.textContent = count;
            cartBadge.style.display = 'block';
        } else {
            cartBadge.style.display = 'none';
        }
    }
}

// Update Wishlist Count
function updateWishlistCount(count) {
    const wishlistBadge = document.querySelector('.wishlist-badge');
    if (wishlistBadge) {
        if (count > 0) {
            wishlistBadge.textContent = count;
            wishlistBadge.style.display = 'block';
        } else {
            wishlistBadge.style.display = 'none';
        }
    }
}

// Update Comparison Count
function updateComparisonCount(count) {
    const comparisonBadge = document.querySelector('.comparison-badge');
    if (comparisonBadge) {
        if (count > 0) {
            comparisonBadge.textContent = count;
            comparisonBadge.style.display = 'block';
        } else {
            comparisonBadge.style.display = 'none';
        }
    }
}

// Show Notification
function showNotification(message, type = 'info') {
    // Remove existing notifications
    document.querySelectorAll('.product-notification').forEach(n => n.remove());

    const notification = document.createElement('div');
    notification.className = `product-notification alert alert-${type} position-fixed`;
    notification.style.cssText = `
        top: 100px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        animation: slideIn 0.3s ease;
    `;

    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };

    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${icons[type] || icons.info} me-2"></i>
            <span>${message}</span>
        </div>
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;

    document.body.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Animate Cart Icon
function animateCartIcon() {
    const cartIcon = document.querySelector('.cart-btn');
    if (cartIcon) {
        cartIcon.classList.add('animate-bounce');
        setTimeout(() => cartIcon.classList.remove('animate-bounce'), 1000);
    }
}

// Generate Star Rating
function generateStars(rating) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;
    const emptyStars = 5 - Math.ceil(rating);

    let stars = '';

    for (let i = 0; i < fullStars; i++) {
        stars += '<i class="fas fa-star text-warning"></i>';
    }

    if (hasHalfStar) {
        stars += '<i class="fas fa-star-half-alt text-warning"></i>';
    }

    for (let i = 0; i < emptyStars; i++) {
        stars += '<i class="far fa-star text-warning"></i>';
    }

    return stars;
}

// Get CSRF Cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Product Image Gallery
class ProductGallery {
    constructor(container) {
        this.container = container;
        this.mainImage = container.querySelector('.main-image');
        this.thumbnails = container.querySelectorAll('.thumbnail');
        this.currentIndex = 0;

        this.init();
    }

    init() {
        // Thumbnail clicks
        this.thumbnails.forEach((thumb, index) => {
            thumb.addEventListener('click', () => {
                this.showImage(index);
            });
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                this.showPrevious();
            } else if (e.key === 'ArrowRight') {
                this.showNext();
            }
        });

        // Touch gestures
        let touchStartX = 0;
        let touchEndX = 0;

        this.mainImage.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });

        this.mainImage.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            this.handleSwipe();
        });
    }

    showImage(index) {
        this.currentIndex = index;
        const thumb = this.thumbnails[index];

        // Update main image
        this.mainImage.src = thumb.dataset.large || thumb.src;
        this.mainImage.alt = thumb.alt;

        // Update active thumbnail
        this.thumbnails.forEach(t => t.classList.remove('active'));
        thumb.classList.add('active');
    }

    showNext() {
        const nextIndex = (this.currentIndex + 1) % this.thumbnails.length;
        this.showImage(nextIndex);
    }

    showPrevious() {
        const prevIndex = (this.currentIndex - 1 + this.thumbnails.length) % this.thumbnails.length;
        this.showImage(prevIndex);
    }

    handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchStartX - touchEndX;

        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                this.showNext();
            } else {
                this.showPrevious();
            }
        }
    }
}

// Product Filters
class ProductFilters {
    constructor(form) {
        this.form = form;
        this.inputs = form.querySelectorAll('input, select');
        this.submitButton = form.querySelector('button[type="submit"]');
        this.resetButton = form.querySelector('button[type="reset"]');

        this.init();
    }

    init() {
        // Auto-submit on change
        this.inputs.forEach(input => {
            if (input.type === 'checkbox' || input.type === 'radio') {
                input.addEventListener('change', () => this.applyFilters());
            }
        });

        // Price range slider
        const priceMin = this.form.querySelector('.price-min');
        const priceMax = this.form.querySelector('.price-max');

        if (priceMin && priceMax) {
            priceMin.addEventListener('change', () => this.updatePriceRange());
            priceMax.addEventListener('change', () => this.updatePriceRange());
        }

        // Reset button
        if (this.resetButton) {
            this.resetButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.resetFilters();
            });
        }
    }

    applyFilters() {
        // Show loading state
        this.submitButton.disabled = true;
        this.submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري التطبيق...';

        // Submit form
        this.form.submit();
    }

    updatePriceRange() {
        const min = this.form.querySelector('.price-min').value;
        const max = this.form.querySelector('.price-max').value;

        // Update visual indicator if exists
        const indicator = this.form.querySelector('.price-range-indicator');
        if (indicator) {
            indicator.textContent = `${min} - ${max} د.أ`;
        }
    }

    resetFilters() {
        // Reset form
        this.form.reset();

        // Clear URL parameters
        const url = new URL(window.location.href);
        url.search = '';
        window.location.href = url.href;
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize product galleries
    document.querySelectorAll('.product-gallery').forEach(gallery => {
        new ProductGallery(gallery);
    });

    // Initialize filters
    const filterForm = document.querySelector('.product-filters');
    if (filterForm) {
        new ProductFilters(filterForm);
    }

    // Wishlist buttons
    document.querySelectorAll('.wishlist-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            toggleWishlist(productId, this);
        });
    });

    // Quick view buttons
    document.querySelectorAll('.quick-view-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            showQuickView(productId);
        });
    });

    // Compare buttons
    document.querySelectorAll('.compare-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            addToComparison(productId);
        });
    });
});

// CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {
            transform: translateY(0);
        }
        40% {
            transform: translateY(-10px);
        }
        60% {
            transform: translateY(-5px);
        }
    }
    
    .animate-bounce {
        animation: bounce 1s ease;
    }
`;
document.head.appendChild(style);