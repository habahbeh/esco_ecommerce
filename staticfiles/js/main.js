// ESCO Enhanced JavaScript
(function() {
    'use strict';

    // Utility Functions
    const utils = {
        // Debounce function for performance
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Throttle function for performance
        throttle: function(func, limit) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        // Smooth scroll to element
        smoothScroll: function(target, duration = 800) {
            const targetElement = document.querySelector(target);
            if (!targetElement) return;

            const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset;
            const startPosition = window.pageYOffset;
            const distance = targetPosition - startPosition;
            let startTime = null;

            function animation(currentTime) {
                if (startTime === null) startTime = currentTime;
                const timeElapsed = currentTime - startTime;
                const run = ease(timeElapsed, startPosition, distance, duration);
                window.scrollTo(0, run);
                if (timeElapsed < duration) requestAnimationFrame(animation);
            }

            function ease(t, b, c, d) {
                t /= d / 2;
                if (t < 1) return c / 2 * t * t + b;
                t--;
                return -c / 2 * (t * (t - 2) - 1) + b;
            }

            requestAnimationFrame(animation);
        },

        // Format numbers with Arabic/English numerals
        formatNumber: function(num, lang = 'ar') {
            if (lang === 'ar') {
                return num.toString().replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
            }
            return num.toString();
        },

        // Get current language
        getCurrentLang: function() {
            return document.documentElement.getAttribute('lang') || 'ar';
        }
    };

    // Initialize all modules when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize modules
        NavigationModule.init();
        SearchModule.init();
        CartModule.init();
        ProductModule.init();
        FormModule.init();
        LazyLoadModule.init();
        AnimationModule.init();
        AccessibilityModule.init();
    });

    // Navigation Module
    const NavigationModule = {
        init: function() {
            this.initSmoothScrolling();
            this.initActiveNavLinks();
            this.initMobileMenuSwipe();
        },

        initSmoothScrolling: function() {
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function(e) {
                    const href = this.getAttribute('href');
                    if (href === '#' || href === '#!') return;

                    e.preventDefault();
                    utils.smoothScroll(href);
                });
            });
        },

        initActiveNavLinks: function() {
            const sections = document.querySelectorAll('section[id]');
            const navLinks = document.querySelectorAll('.nav-menu a[href^="#"]');

            window.addEventListener('scroll', utils.throttle(() => {
                let current = '';

                sections.forEach(section => {
                    const sectionTop = section.offsetTop - 100;
                    const sectionBottom = sectionTop + section.offsetHeight;

                    if (window.pageYOffset >= sectionTop && window.pageYOffset < sectionBottom) {
                        current = section.getAttribute('id');
                    }
                });

                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${current}`) {
                        link.classList.add('active');
                    }
                });
            }, 100));
        },

        initMobileMenuSwipe: function() {
            const mobileMenu = document.getElementById('mobileMenu');
            if (!mobileMenu) return;

            let touchStartX = 0;
            let touchEndX = 0;

            mobileMenu.addEventListener('touchstart', e => {
                touchStartX = e.changedTouches[0].screenX;
            });

            mobileMenu.addEventListener('touchend', e => {
                touchEndX = e.changedTouches[0].screenX;
                this.handleSwipe();
            });

            const handleSwipe = () => {
                const swipeThreshold = 50;
                const isRTL = document.documentElement.getAttribute('dir') === 'rtl';

                if (isRTL) {
                    if (touchStartX - touchEndX > swipeThreshold) {
                        // Swipe left in RTL (close)
                        document.getElementById('mobileMenuClose').click();
                    }
                } else {
                    if (touchEndX - touchStartX > swipeThreshold) {
                        // Swipe right in LTR (close)
                        document.getElementById('mobileMenuClose').click();
                    }
                }
            };

            this.handleSwipe = handleSwipe;
        }
    };

    // Search Module
    const SearchModule = {
        init: function() {
            this.initSearchSuggestions();
            this.initSearchHistory();
            this.initVoiceSearch();
        },

        initSearchSuggestions: function() {
            const searchInputs = document.querySelectorAll('.search-input');

            searchInputs.forEach(input => {
                const suggestionsContainer = document.createElement('div');
                suggestionsContainer.className = 'search-suggestions';
                input.parentElement.appendChild(suggestionsContainer);

                input.addEventListener('input', utils.debounce((e) => {
                    const query = e.target.value.trim();
                    if (query.length < 2) {
                        suggestionsContainer.style.display = 'none';
                        return;
                    }

                    // Here you would normally make an API call
                    // For demo, showing mock suggestions
                    this.showSuggestions(query, suggestionsContainer);
                }, 300));

                // Hide suggestions when clicking outside
                document.addEventListener('click', (e) => {
                    if (!e.target.closest('.search-form')) {
                        suggestionsContainer.style.display = 'none';
                    }
                });
            });
        },

        showSuggestions: function(query, container) {
            // Mock suggestions - replace with actual API call
            const suggestions = [
                'مولدات كهربائية',
                'معدات صناعية',
                'أدوات يدوية',
                'معدات السلامة'
            ].filter(s => s.includes(query));

            if (suggestions.length === 0) {
                container.style.display = 'none';
                return;
            }

            container.innerHTML = suggestions.map(s =>
                `<div class="suggestion-item">${s}</div>`
            ).join('');

            container.style.display = 'block';

            // Add click handlers
            container.querySelectorAll('.suggestion-item').forEach(item => {
                item.addEventListener('click', function() {
                    const input = container.previousElementSibling;
                    input.value = this.textContent;
                    container.style.display = 'none';
                    input.form.submit();
                });
            });
        },

        initSearchHistory: function() {
            const searchForms = document.querySelectorAll('.search-form');

            searchForms.forEach(form => {
                form.addEventListener('submit', function(e) {
                    const query = this.querySelector('input[name="q"]').value.trim();
                    if (query) {
                        SearchModule.saveToHistory(query);
                    }
                });
            });
        },

        saveToHistory: function(query) {
            let history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
            history = history.filter(item => item !== query); // Remove duplicates
            history.unshift(query); // Add to beginning
            history = history.slice(0, 5); // Keep only last 5
            localStorage.setItem('searchHistory', JSON.stringify(history));
        },

        initVoiceSearch: function() {
            if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) return;

            const searchInputs = document.querySelectorAll('.search-input');

            searchInputs.forEach(input => {
                const voiceBtn = document.createElement('button');
                voiceBtn.className = 'voice-search-btn';
                voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
                voiceBtn.type = 'button';
                voiceBtn.setAttribute('aria-label', 'البحث الصوتي');

                input.parentElement.insertBefore(voiceBtn, input.nextSibling);

                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                recognition.lang = utils.getCurrentLang() === 'ar' ? 'ar-SA' : 'en-US';
                recognition.continuous = false;
                recognition.interimResults = false;

                voiceBtn.addEventListener('click', function() {
                    recognition.start();
                    this.classList.add('listening');
                });

                recognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    input.value = transcript;
                    voiceBtn.classList.remove('listening');
                };

                recognition.onerror = function() {
                    voiceBtn.classList.remove('listening');
                };
            });
        }
    };

    // Cart Module
    const CartModule = {
        init: function() {
            this.initAddToCart();
            this.initCartPreview();
            this.initQuantityControls();
        },

        initAddToCart: function() {
            document.addEventListener('submit', function(e) {
                if (e.target.matches('.add-to-cart-form')) {
                    e.preventDefault();
                    CartModule.handleAddToCart(e.target);
                }
            });
        },

        initCartPreview: function () {
            // البحث عن عنصر معاينة السلة في الصفحة إذا كان موجوداً
            const cartIcon = document.querySelector('.cart-btn, .header-cart-icon, .action-btn.cart-btn');
            if (!cartIcon) return;

            // إنشاء عنصر معاينة السلة إذا لم يكن موجوداً
            let cartPreview = document.querySelector('.cart-preview-container');
            if (!cartPreview) {
                cartPreview = document.createElement('div');
                cartPreview.className = 'cart-preview-container';
                cartPreview.style.cssText = `
            position: absolute;
            top: 100%;
            right: 0;
            width: 300px;
            background: var(--bs-body-bg);
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            z-index: 1040;
            display: none;
            overflow: hidden;
        `;

                // إضافة لمستند الصفحة في المكان المناسب
                const headerActions = document.querySelector('.header-actions');
                if (headerActions) {
                    const cartBtnParent = cartIcon.parentElement;
                    cartBtnParent.style.position = 'relative';
                    cartBtnParent.appendChild(cartPreview);
                } else {
                    document.body.appendChild(cartPreview);
                    cartPreview.style.position = 'fixed';
                    cartPreview.style.top = '80px';
                    cartPreview.style.right = '20px';
                }

                // التصحيح للغة العربية
                if (document.documentElement.dir === 'rtl') {
                    cartPreview.style.right = 'auto';
                    cartPreview.style.left = '0';
                }
            }

            // إضافة معالج أحداث لإظهار معاينة السلة عند تحريك الماوس فوق أيقونة السلة
            cartIcon.addEventListener('mouseenter', () => {
                this.fetchCartPreview();
            });

            // إخفاء المعاينة عند مغادرة منطقة المعاينة
            cartPreview.addEventListener('mouseleave', () => {
                cartPreview.style.display = 'none';
            });
        },

        fetchCartPreview: function () {
            const cartPreview = document.querySelector('.cart-preview-container');
            if (!cartPreview) return;

            // إظهار حالة التحميل
            cartPreview.innerHTML = '<div class="p-3 text-center"><i class="fas fa-spinner fa-spin"></i></div>';
            cartPreview.style.display = 'block';

            // في بيئة حقيقية، نقوم بطلب AJAX لجلب محتوى السلة
            // لكن هنا نقوم بمحاكاة الاستجابة
            setTimeout(() => {
                if (cartPreview.style.display === 'none') return;

                // التحقق من وجود منتجات في السلة
                const cartBadge = document.querySelector('.cart-badge');
                const hasItems = cartBadge && cartBadge.style.display !== 'none';

                if (hasItems) {
                    cartPreview.innerHTML = `
                <div class="p-3">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h6 class="mb-0">سلة التسوق</h6>
                        <a href="/cart/" class="text-primary">عرض الكل</a>
                    </div>
                    <div class="cart-items">
                        <div class="cart-item d-flex py-2 border-bottom">
                            <div class="placeholder-image bg-light rounded" style="width:50px;height:50px;flex-shrink:0"></div>
                            <div class="ms-2 flex-grow-1">
                                <p class="mb-0 small">منتج في السلة</p>
                                <span class="text-primary fw-bold">السعر</span>
                            </div>
                        </div>
                    </div>
                    <div class="text-center mt-3">
                        <a href="/cart/checkout/" class="btn btn-primary btn-sm w-100">إتمام الطلب</a>
                    </div>
                </div>
            `;
                } else {
                    cartPreview.innerHTML = `
                <div class="p-3 text-center">
                    <i class="fas fa-shopping-cart text-muted mb-2" style="font-size:2rem"></i>
                    <p class="mb-2">سلة التسوق فارغة</p>
                    <a href="/products/" class="btn btn-outline-primary btn-sm">تسوق الآن</a>
                </div>
            `;
                }
            }, 500);
        },

        handleAddToCart: async function(form) {
            const button = form.querySelector('button[type="submit"]');
            const originalText = button.innerHTML;
            const lang = utils.getCurrentLang();

            // Show loading state
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

            try {
                const formData = new FormData(form);
                const response = await fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    // Update cart badge
                    this.updateCartBadge(data.cart_items_count);

                    // Show success animation
                    button.innerHTML = '<i class="fas fa-check"></i>';
                    button.classList.add('btn-success');

                    // Show cart preview
                    this.showCartPreview(data.product);

                    // Reset button after delay
                    setTimeout(() => {
                        button.innerHTML = originalText;
                        button.classList.remove('btn-success');
                        button.disabled = false;
                    }, 2000);
                } else {
                    throw new Error(data.message || 'Error adding to cart');
                }
            } catch (error) {
                button.innerHTML = '<i class="fas fa-exclamation-circle"></i>';
                button.classList.add('btn-danger');

                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.classList.remove('btn-danger');
                    button.disabled = false;
                }, 2000);

                console.error('Error:', error);
            }
        },

        updateCartBadge: function(count) {
            const badges = document.querySelectorAll('.cart-badge');
            badges.forEach(badge => {
                if (count > 0) {
                    badge.textContent = utils.formatNumber(count, utils.getCurrentLang());
                    badge.style.display = 'block';
                } else {
                    badge.style.display = 'none';
                }
            });
        },

        showCartPreview: function(product) {
            // Create cart preview element
            const preview = document.createElement('div');
            preview.className = 'cart-preview animate-slide-up';
            preview.innerHTML = `
                <div class="cart-preview-content">
                    <div class="cart-preview-header">
                        <i class="fas fa-check-circle text-success"></i>
                        <span>${utils.getCurrentLang() === 'ar' ? 'تمت الإضافة إلى السلة' : 'Added to cart'}</span>
                    </div>
                    <div class="cart-preview-product">
                        <img src="${product.image}" alt="${product.name}">
                        <div class="product-info">
                            <h6>${product.name}</h6>
                            <p class="text-primary fw-bold">${product.price}</p>
                        </div>
                    </div>
                    <div class="cart-preview-actions">
                        <a href="/cart/" class="btn btn-primary btn-sm">
                            ${utils.getCurrentLang() === 'ar' ? 'عرض السلة' : 'View Cart'}
                        </a>
                        <button class="btn btn-outline-secondary btn-sm" onclick="this.closest('.cart-preview').remove()">
                            ${utils.getCurrentLang() === 'ar' ? 'متابعة التسوق' : 'Continue Shopping'}
                        </button>
                    </div>
                </div>
            `;

            document.body.appendChild(preview);

            // Auto remove after 5 seconds
            setTimeout(() => {
                preview.classList.add('fade-out');
                setTimeout(() => preview.remove(), 300);
            }, 5000);
        },

        initQuantityControls: function() {
            document.addEventListener('click', function(e) {
                if (e.target.matches('.quantity-btn')) {
                    const input = e.target.parentElement.querySelector('.quantity-input');
                    const currentValue = parseInt(input.value) || 1;
                    const min = parseInt(input.min) || 1;
                    const max = parseInt(input.max) || 999;

                    if (e.target.classList.contains('quantity-increase')) {
                        if (currentValue < max) {
                            input.value = currentValue + 1;
                            input.dispatchEvent(new Event('change'));
                        }
                    } else if (e.target.classList.contains('quantity-decrease')) {
                        if (currentValue > min) {
                            input.value = currentValue - 1;
                            input.dispatchEvent(new Event('change'));
                        }
                    }
                }
            });
        }
    };

    // Product Module
    const ProductModule = {
        init: function() {
            this.initProductGallery();
            this.initProductFilters();
            this.initQuickView();
            this.initWishlist();
            this.initComparison();
        },

        initProductGallery: function() {
            const galleries = document.querySelectorAll('.product-gallery');

            galleries.forEach(gallery => {
                const mainImage = gallery.querySelector('.main-image img');
                const thumbnails = gallery.querySelectorAll('.thumbnail-image');

                thumbnails.forEach(thumb => {
                    thumb.addEventListener('click', function() {
                        // Update main image
                        mainImage.src = this.dataset.fullImage;
                        mainImage.alt = this.alt;

                        // Update active thumbnail
                        thumbnails.forEach(t => t.classList.remove('active'));
                        this.classList.add('active');
                    });
                });

                // Zoom functionality
                if (mainImage) {
                    this.initImageZoom(mainImage);
                }
            });
        },

        initImageZoom: function(image) {
            const zoomContainer = document.createElement('div');
            zoomContainer.className = 'zoom-container';
            image.parentElement.appendChild(zoomContainer);

            image.addEventListener('mousemove', function(e) {
                const rect = this.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / rect.width) * 100;
                const y = ((e.clientY - rect.top) / rect.height) * 100;

                zoomContainer.style.backgroundImage = `url(${this.src})`;
                zoomContainer.style.backgroundPosition = `${x}% ${y}%`;
                zoomContainer.style.display = 'block';
            });

            image.addEventListener('mouseleave', function() {
                zoomContainer.style.display = 'none';
            });
        },

        initProductFilters: function() {
            const filterForm = document.querySelector('.product-filters');
            if (!filterForm) return;

            // Price range slider
            const priceSlider = filterForm.querySelector('.price-range-slider');
            if (priceSlider) {
                this.initPriceRangeSlider(priceSlider);
            }

            // Filter changes
            filterForm.addEventListener('change', utils.debounce(function() {
                ProductModule.applyFilters();
            }, 500));

            // Clear filters
            const clearBtn = filterForm.querySelector('.clear-filters');
            if (clearBtn) {
                clearBtn.addEventListener('click', function() {
                    filterForm.reset();
                    ProductModule.applyFilters();
                });
            }
        },

        initPriceRangeSlider: function(container) {
            const minInput = container.querySelector('.price-min');
            const maxInput = container.querySelector('.price-max');
            const slider = container.querySelector('.price-slider');

            if (!slider) return;

            // Initialize slider UI
            // This would be replaced with actual slider library implementation
        },

        applyFilters: function() {
            const form = document.querySelector('.product-filters');
            const formData = new FormData(form);
            const params = new URLSearchParams(formData);

            // Show loading state
            const productsContainer = document.querySelector('.products-container');
            productsContainer.classList.add('loading');

            // Update URL without page reload
            const newUrl = `${window.location.pathname}?${params.toString()}`;
            window.history.pushState({}, '', newUrl);

            // Fetch filtered products
            fetch(newUrl, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newProducts = doc.querySelector('.products-container').innerHTML;

                productsContainer.innerHTML = newProducts;
                productsContainer.classList.remove('loading');

                // Reinitialize product modules
                LazyLoadModule.init();
                AnimationModule.init();
            })
            .catch(error => {
                console.error('Error applying filters:', error);
                productsContainer.classList.remove('loading');
            });
        },

        initQuickView: function() {
            document.addEventListener('click', function(e) {
                if (e.target.matches('.quick-view-btn')) {
                    e.preventDefault();
                    const productId = e.target.dataset.productId;
                    ProductModule.showQuickView(productId);
                }
            });
        },

        showQuickView: async function(productId) {
            // Create modal
            const modal = document.createElement('div');
            modal.className = 'quick-view-modal';
            modal.innerHTML = `
                <div class="modal-overlay"></div>
                <div class="modal-content">
                    <button class="modal-close"><i class="fas fa-times"></i></button>
                    <div class="modal-body">
                        <div class="text-center p-5">
                            <i class="fas fa-spinner fa-spin fa-3x"></i>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);
            document.body.style.overflow = 'hidden';

            // Close modal handlers
            modal.querySelector('.modal-close').addEventListener('click', () => {
                modal.remove();
                document.body.style.overflow = '';
            });

            modal.querySelector('.modal-overlay').addEventListener('click', () => {
                modal.remove();
                document.body.style.overflow = '';
            });

            try {
                // Fetch product details
                const response = await fetch(`/api/products/${productId}/quick-view/`);
                const data = await response.json();

                // Update modal content
                modal.querySelector('.modal-body').innerHTML = `
                    <div class="row">
                        <div class="col-md-6">
                            <img src="${data.image}" alt="${data.name}" class="img-fluid">
                        </div>
                        <div class="col-md-6">
                            <h3>${data.name}</h3>
                            <p class="text-primary fs-4 fw-bold">${data.price}</p>
                            <p>${data.description}</p>
                            <form class="add-to-cart-form" action="/cart/add/${productId}/" method="post">
                                <input type="hidden" name="csrfmiddlewaretoken" value="${data.csrf_token}">
                                <div class="d-flex gap-3 mb-3">
                                    <input type="number" name="quantity" value="1" min="1" class="form-control" style="width: 100px;">
                                    <button type="submit" class="btn btn-primary flex-grow-1">
                                        <i class="fas fa-shopping-cart me-2"></i>
                                        ${utils.getCurrentLang() === 'ar' ? 'أضف إلى السلة' : 'Add to Cart'}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                `;

                // Reinitialize cart module for the new form
                CartModule.init();
            } catch (error) {
                modal.querySelector('.modal-body').innerHTML = `
                    <div class="alert alert-danger">
                        ${utils.getCurrentLang() === 'ar' ? 'حدث خطأ في تحميل المنتج' : 'Error loading product'}
                    </div>
                `;
            }
        },

        initWishlist: function() {
            document.addEventListener('click', function(e) {
                if (e.target.matches('.wishlist-btn')) {
                    e.preventDefault();
                    const productId = e.target.dataset.productId;
                    const isActive = e.target.classList.contains('active');

                    if (isActive) {
                        ProductModule.removeFromWishlist(productId, e.target);
                    } else {
                        ProductModule.addToWishlist(productId, e.target);
                    }
                }
            });
        },

        addToWishlist: async function(productId, button) {
            try {
                const response = await fetch('/api/wishlist/add/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: JSON.stringify({ product_id: productId })
                });

                const data = await response.json();

                if (data.success) {
                    button.classList.add('active');
                    this.showNotification('تمت الإضافة إلى قائمة الأمنيات', 'success');
                }
            } catch (error) {
                this.showNotification('حدث خطأ', 'error');
            }
        },

        removeFromWishlist: async function(productId, button) {
            try {
                const response = await fetch('/api/wishlist/remove/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: JSON.stringify({ product_id: productId })
                });

                const data = await response.json();

                if (data.success) {
                    button.classList.remove('active');
                    this.showNotification('تمت الإزالة من قائمة الأمنيات', 'info');
                }
            } catch (error) {
                this.showNotification('حدث خطأ', 'error');
            }
        },

        initComparison: function() {
            const compareButtons = document.querySelectorAll('.compare-btn');
            const compareList = [];

            compareButtons.forEach(btn => {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    const productId = this.dataset.productId;

                    if (this.classList.contains('active')) {
                        // Remove from comparison
                        const index = compareList.indexOf(productId);
                        if (index > -1) {
                            compareList.splice(index, 1);
                        }
                        this.classList.remove('active');
                    } else {
                        // Add to comparison
                        if (compareList.length >= 4) {
                            ProductModule.showNotification('يمكن مقارنة 4 منتجات كحد أقصى', 'warning');
                            return;
                        }
                        compareList.push(productId);
                        this.classList.add('active');
                    }

                    ProductModule.updateComparisonBar(compareList);
                });
            });
        },

        updateComparisonBar: function(compareList) {
            let bar = document.querySelector('.comparison-bar');

            if (compareList.length === 0) {
                if (bar) bar.remove();
                return;
            }

            if (!bar) {
                bar = document.createElement('div');
                bar.className = 'comparison-bar';
                document.body.appendChild(bar);
            }

            bar.innerHTML = `
                <div class="container">
                    <div class="d-flex justify-content-between align-items-center">
                        <span>${compareList.length} منتجات للمقارنة</span>
                        <div>
                            <button class="btn btn-primary btn-sm" onclick="ProductModule.showComparison()">
                                عرض المقارنة
                            </button>
                            <button class="btn btn-outline-secondary btn-sm" onclick="ProductModule.clearComparison()">
                                مسح الكل
                            </button>
                        </div>
                    </div>
                </div>
            `;
        },

        showComparison: function() {
            // Implementation for showing comparison table
            window.location.href = '/products/compare/?' + compareList.map(id => `id=${id}`).join('&');
        },

        clearComparison: function() {
            document.querySelectorAll('.compare-btn.active').forEach(btn => {
                btn.classList.remove('active');
            });
            compareList.length = 0;
            this.updateComparisonBar([]);
        },

        getCSRFToken: function() {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        },

        showNotification: function(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification notification-${type} animate-slide-up`;
            notification.innerHTML = `
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            `;

            document.body.appendChild(notification);

            setTimeout(() => {
                notification.classList.add('fade-out');
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }
    };

    // Form Module
    const FormModule = {
        init: function() {
            this.initFormValidation();
            this.initPasswordToggle();
            this.initFileUpload();
        },

        initFormValidation: function() {
            const forms = document.querySelectorAll('.needs-validation');

            forms.forEach(form => {
                form.addEventListener('submit', function(event) {
                    if (!form.checkValidity()) {
                        event.preventDefault();
                        event.stopPropagation();
                    }

                    form.classList.add('was-validated');
                });

                // Real-time validation
                const inputs = form.querySelectorAll('input, textarea, select');
                inputs.forEach(input => {
                    input.addEventListener('blur', function() {
                        if (this.value) {
                            this.classList.add('touched');
                        }
                    });

                    input.addEventListener('input', function() {
                        if (this.classList.contains('touched')) {
                            this.checkValidity();
                        }
                    });
                });
            });
        },

        initPasswordToggle: function() {
            const passwordToggles = document.querySelectorAll('.password-toggle');

            passwordToggles.forEach(toggle => {
                toggle.addEventListener('click', function() {
                    const input = this.parentElement.querySelector('input');
                    const icon = this.querySelector('i');

                    if (input.type === 'password') {
                        input.type = 'text';
                        icon.classList.remove('fa-eye');
                        icon.classList.add('fa-eye-slash');
                    } else {
                        input.type = 'password';
                        icon.classList.remove('fa-eye-slash');
                        icon.classList.add('fa-eye');
                    }
                });
            });
        },

        initFileUpload: function() {
            const fileInputs = document.querySelectorAll('.custom-file-input');

            fileInputs.forEach(input => {
                input.addEventListener('change', function() {
                    const fileName = this.files[0]?.name || 'اختر ملف';
                    const label = this.nextElementSibling;
                    if (label) {
                        label.textContent = fileName;
                    }

                    // Preview for images
                    if (this.files[0] && this.files[0].type.startsWith('image/')) {
                        this.showImagePreview(this.files[0]);
                    }
                });
            });
        },

        showImagePreview: function(file) {
            const reader = new FileReader();
            const preview = document.createElement('img');
            preview.className = 'file-preview';

            reader.onload = function(e) {
                preview.src = e.target.result;
            };

            reader.readAsDataURL(file);

            // Add preview to DOM
            const container = file.parentElement;
            const existingPreview = container.querySelector('.file-preview');
            if (existingPreview) {
                existingPreview.remove();
            }
            container.appendChild(preview);
        }
    };

    // Lazy Load Module
    const LazyLoadModule = {
        init: function() {
            if ('IntersectionObserver' in window) {
                const imageObserver = new IntersectionObserver((entries, observer) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            img.src = img.dataset.src;
                            img.classList.remove('lazy');
                            observer.unobserve(img);
                        }
                    });
                });

                const lazyImages = document.querySelectorAll('img.lazy');
                lazyImages.forEach(img => imageObserver.observe(img));
            }
        }
    };

    // Animation Module
    const AnimationModule = {
        init: function() {
            this.initScrollAnimations();
            this.initCounterAnimations();
            this.initParallax();
        },

        initScrollAnimations: function() {
            const animatedElements = document.querySelectorAll('[data-animate]');

            if ('IntersectionObserver' in window) {
                const animationObserver = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const element = entry.target;
                            const animation = element.dataset.animate;
                            element.classList.add('animate-' + animation);
                            animationObserver.unobserve(element);
                        }
                    });
                }, {
                    threshold: 0.1
                });

                animatedElements.forEach(el => animationObserver.observe(el));
            }
        },

        initCounterAnimations: function() {
            const counters = document.querySelectorAll('.counter');

            counters.forEach(counter => {
                const updateCount = () => {
                    const target = +counter.getAttribute('data-target');
                    const count = +counter.innerText;
                    const increment = target / 200;

                    if (count < target) {
                        counter.innerText = Math.ceil(count + increment);
                        setTimeout(updateCount, 10);
                    } else {
                        counter.innerText = utils.formatNumber(target, utils.getCurrentLang());
                    }
                };

                // Start animation when visible
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            updateCount();
                            observer.unobserve(entry.target);
                        }
                    });
                });

                observer.observe(counter);
            });
        },

        initParallax: function() {
            const parallaxElements = document.querySelectorAll('.parallax');

            if (parallaxElements.length === 0) return;

            window.addEventListener('scroll', utils.throttle(() => {
                const scrolled = window.pageYOffset;

                parallaxElements.forEach(element => {
                    const speed = element.dataset.speed || 0.5;
                    const yPos = -(scrolled * speed);
                    element.style.transform = `translateY(${yPos}px)`;
                });
            }, 10));
        }
    };

    // Accessibility Module
    const AccessibilityModule = {
        init: function() {
            this.initKeyboardNavigation();
            this.initAriaLiveRegions();
            this.initFocusTrap();
        },

        initKeyboardNavigation: function() {
            // Escape key to close modals/menus
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    // Close mobile menu
                    const mobileMenu = document.querySelector('.mobile-menu.active');
                    if (mobileMenu) {
                        document.getElementById('mobileMenuClose').click();
                    }

                    // Close any open modals
                    const modals = document.querySelectorAll('.modal.show');
                    modals.forEach(modal => {
                        const closeBtn = modal.querySelector('.btn-close');
                        if (closeBtn) closeBtn.click();
                    });
                }
            });

            // Tab navigation improvements
            const interactiveElements = document.querySelectorAll('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
            interactiveElements.forEach(element => {
                element.addEventListener('focus', function() {
                    this.classList.add('keyboard-focused');
                });

                element.addEventListener('blur', function() {
                    this.classList.remove('keyboard-focused');
                });
            });
        },

        initAriaLiveRegions: function() {
            // Create aria-live region for announcements
            const liveRegion = document.createElement('div');
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.className = 'sr-only';
            liveRegion.id = 'aria-live-region';
            document.body.appendChild(liveRegion);
        },

        initFocusTrap: function() {
            // Trap focus in modals
            document.addEventListener('shown.bs.modal', function(e) {
                const modal = e.target;
                const focusableElements = modal.querySelectorAll('a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])');
                const firstFocusable = focusableElements[0];
                const lastFocusable = focusableElements[focusableElements.length - 1];

                modal.addEventListener('keydown', function(e) {
                    if (e.key === 'Tab') {
                        if (e.shiftKey) {
                            if (document.activeElement === firstFocusable) {
                                e.preventDefault();
                                lastFocusable.focus();
                            }
                        } else {
                            if (document.activeElement === lastFocusable) {
                                e.preventDefault();
                                firstFocusable.focus();
                            }
                        }
                    }
                });

                firstFocusable.focus();
            });
        },

        announce: function(message) {
            const liveRegion = document.getElementById('aria-live-region');
            if (liveRegion) {
                liveRegion.textContent = message;
                setTimeout(() => {
                    liveRegion.textContent = '';
                }, 1000);
            }
        }
    };

    // Expose modules to global scope for external use
    window.ESCOModules = {
        utils,
        NavigationModule,
        SearchModule,
        CartModule,
        ProductModule,
        FormModule,
        LazyLoadModule,
        AnimationModule,
        AccessibilityModule
    };

})();