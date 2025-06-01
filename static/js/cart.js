// static/js/cart.js
/**
 * Cart JavaScript Functions
 * Handles AJAX cart operations and UI updates
 */

(function($) {
    'use strict';

    // Cart object
    var Cart = {

        // Initialize cart functions
        init: function() {
            this.bindEvents();
            this.updateCartDisplay();
        },

        // Bind event handlers
        bindEvents: function() {
            var self = this;

            // Add to cart forms
            $(document).on('submit', '.add-to-cart-form', function(e) {
                e.preventDefault();
                self.addToCart($(this));
            });

            // Quick add buttons
            $(document).on('click', '.add-to-cart-btn', function(e) {
                e.preventDefault();
                var productId = $(this).data('product-id');
                self.quickAddToCart(productId);
            });

            // Update quantity
            $(document).on('change', '.cart-quantity-input', function() {
                var form = $(this).closest('form');
                self.updateQuantity(form);
            });

            // Remove from cart
            $(document).on('click', '.remove-from-cart', function(e) {
                e.preventDefault();
                if (confirm('هل أنت متأكد من حذف هذا المنتج؟')) {
                    var form = $(this).closest('form');
                    form.submit();
                }
            });
        },

        // Add product to cart
        addToCart: function(form) {
            var self = this;
            var submitBtn = form.find('button[type="submit"]');
            var originalText = submitBtn.html();

            // Show loading
            submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i>');

            $.ajax({
                url: form.attr('action'),
                type: 'POST',
                data: form.serialize(),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                success: function(response) {
                    if (response.success) {
                        self.showNotification('success', response.message);
                        self.updateCartCount(response.cart_count);
                        self.updateCartTotal(response.cart_total);

                        // Animate cart icon
                        self.animateCartIcon();
                    } else {
                        self.showNotification('error', response.message || 'حدث خطأ');
                    }
                },
                error: function() {
                    self.showNotification('error', 'حدث خطأ في الاتصال');
                },
                complete: function() {
                    submitBtn.prop('disabled', false).html(originalText);
                }
            });
        },

        // Quick add to cart (quantity = 1)
        quickAddToCart: function(productId) {
            var form = $('<form>', {
                method: 'POST',
                action: '/cart/add/' + productId + '/'
            });

            form.append($('<input>', {
                type: 'hidden',
                name: 'csrfmiddlewaretoken',
                value: this.getCookie('csrftoken')
            }));

            form.append($('<input>', {
                type: 'hidden',
                name: 'quantity',
                value: '1'
            }));

            this.addToCart(form);
        },

        // Update quantity
        updateQuantity: function(form) {
            var self = this;

            $.ajax({
                url: form.attr('action'),
                type: 'POST',
                data: form.serialize(),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                success: function(response) {
                    if (response.success) {
                        self.updateCartCount(response.cart_count);
                        self.updateCartTotal(response.cart_total);

                        // Reload cart page if on cart detail
                        if (window.location.pathname.includes('/cart/')) {
                            location.reload();
                        }
                    }
                }
            });
        },

        // Update cart count in header
        updateCartCount: function(count) {
            $('.cart-count, .cart-badge, #cart-count').text(count);

            if (count > 0) {
                $('.cart-count, .cart-badge').removeClass('d-none');
            } else {
                $('.cart-count, .cart-badge').addClass('d-none');
            }
        },

        // Update cart total
        updateCartTotal: function(total) {
            $('.cart-total').text(total + ' د.أ');
        },

        // Update cart display on page load
        updateCartDisplay: function() {
            // This would typically fetch cart info via AJAX
            // For now, it uses the context processor data
        },

        // Animate cart icon
        animateCartIcon: function() {
            var cartIcon = $('.header-cart-icon, .cart-icon');
            cartIcon.addClass('animate-bounce');

            setTimeout(function() {
                cartIcon.removeClass('animate-bounce');
            }, 1000);
        },

        // Show notification
        showNotification: function(type, message) {
            // If using toastr
            if (typeof toastr !== 'undefined') {
                toastr[type](message);
                return;
            }

            // Fallback notification
            var alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
            var icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';

            var notification = $('<div>', {
                class: 'alert ' + alertClass + ' alert-dismissible fade show cart-notification',
                role: 'alert',
                html: '<i class="fas ' + icon + ' me-2"></i>' + message +
                      '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>'
            });

            // Add to page
            if ($('.cart-notifications').length) {
                $('.cart-notifications').append(notification);
            } else {
                $('body').prepend($('<div class="cart-notifications"></div>').append(notification));
            }

            // Auto hide after 5 seconds
            setTimeout(function() {
                notification.fadeOut(function() {
                    $(this).remove();
                });
            }, 5000);
        },

        // Get CSRF cookie
        getCookie: function(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
    };

    // Initialize when document is ready
    $(document).ready(function() {
        Cart.init();
    });

    // Make Cart available globally
    window.Cart = Cart;

})(jQuery);

// CSS for notifications
var style = document.createElement('style');
style.textContent = `
    .cart-notifications {
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        max-width: 350px;
    }
    
    .cart-notification {
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .animate-bounce {
        animation: bounce 0.5s ease-in-out;
    }
    
    @keyframes bounce {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.2); }
    }
    
    /* RTL Support */
    html[dir="rtl"] .cart-notifications {
        right: auto;
        left: 20px;
    }
`;
document.head.appendChild(style);