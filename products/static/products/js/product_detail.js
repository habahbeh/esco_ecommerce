/**
 * ملف JavaScript الشامل لصفحة تفاصيل المنتج
 * يتضمن جميع وظائف صفحة المنتج مع نظام التكبير الاحترافي
 * تمت معالجة مشكلة تكرار حقل variant_id وخطأ الاتصال بالخادم
 */

// استدعاء الوظائف عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // التحقق من عدم وجود نماذج متكررة (حل مشكلة تكرار variant_id)
    const addToCartForms = document.querySelectorAll('#addToCartForm');
    if (addToCartForms.length > 1) {
        console.error('تحذير: تم العثور على أكثر من نموذج بنفس المعرف addToCartForm. قد يسبب هذا مشاكل في الإرسال.');
    }

    // تفعيل شجرة الفئات
    initCategoryTree();

    // تفعيل تبويبات المنتج
    initTabs();

    // تفعيل معرض الصور
    initProductGallery();

    // تفعيل وظيفة التكبير
    initProductZoom();

    // تفعيل اختيار متغيرات المنتج
    initVariantSelection();
});

/**
 * ========= وظائف شجرة الفئات =========
 */

// تهيئة شجرة الفئات
function initCategoryTree() {
    // تفعيل الفئات في المسار النشط
    if (typeof currentCategoryPath !== 'undefined' && currentCategoryPath.length > 0) {
        activateCategoryPath();
    }

    // التعامل مع الأزرار للفتح والإغلاق
    const toggleIcons = document.querySelectorAll('.toggle-icon');
    toggleIcons.forEach(icon => {
        icon.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const listItem = this.closest('.category-item');
            const subList = listItem.querySelector('.subcategory-list');

            if (subList) {
                if (subList.style.display === 'none' || !subList.style.display) {
                    subList.style.display = 'block';
                    this.querySelector('.expand-icon').style.display = 'none';
                    this.querySelector('.collapse-icon').style.display = 'inline';
                } else {
                    subList.style.display = 'none';
                    this.querySelector('.expand-icon').style.display = 'inline';
                    this.querySelector('.collapse-icon').style.display = 'none';
                }
            }
        });
    });
}

// تفعيل مسار الفئات
function activateCategoryPath() {
    // الحصول على مسار الفئة الحالي
    const currentPath = window.currentCategoryPath || [];

    if (!currentPath.length) return;

    // تفعيل كل فئة في المسار
    currentPath.forEach(categoryId => {
        // العثور على عنصر الفئة
        const categoryItem = document.querySelector(`.category-item[data-category-id="${categoryId}"]`);
        if (!categoryItem) return;

        // إذا كانت فئة بسيطة، قم بتفعيل الرابط
        const simpleLink = categoryItem.querySelector('.category-link');
        if (simpleLink) {
            simpleLink.classList.add('active');
            simpleLink.style.color = 'var(--bs-primary)';
            simpleLink.style.fontWeight = '600';
            simpleLink.style.backgroundColor = 'rgba(var(--bs-primary-rgb), 0.05)';
            return;
        }

        // إذا كانت فئة لها أطفال، افتح الأكورديون
        const accordionButton = categoryItem.querySelector('.accordion-button');
        const accordionCollapse = categoryItem.querySelector('.accordion-collapse');

        if (accordionButton && accordionCollapse) {
            // إزالة فئة collapsed من الزر
            accordionButton.classList.remove('collapsed');
            // تعيين سمة aria-expanded إلى true
            accordionButton.setAttribute('aria-expanded', 'true');
            // إضافة فئة show إلى العنصر القابل للطي
            accordionCollapse.classList.add('show');
        }

        // افتح جميع الفئات الأب
        let parentAccordion = categoryItem.closest('.accordion-collapse');
        while (parentAccordion) {
            // إضافة فئة show
            parentAccordion.classList.add('show');

            // تحديث حالة الزر
            const parentButton = document.querySelector(`[data-bs-target="#${parentAccordion.id}"]`);
            if (parentButton) {
                parentButton.classList.remove('collapsed');
                parentButton.setAttribute('aria-expanded', 'true');
            }

            // الانتقال إلى المستوى التالي
            const parentItem = parentAccordion.closest('.accordion-item');
            if (parentItem) {
                parentAccordion = parentItem.closest('.accordion-collapse');
            } else {
                break;
            }
        }
    });
}

/**
 * ========= وظائف التبويبات =========
 */

// تهيئة تبويبات المنتج
function initTabs() {
    const tabs = document.querySelectorAll('.amazon-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // إزالة الفئة النشطة من جميع التبويبات
            tabs.forEach(t => t.classList.remove('active'));

            // إضافة الفئة النشطة للتبويب المحدد
            this.classList.add('active');

            // إخفاء جميع محتويات التبويبات
            const contents = document.querySelectorAll('.tab-content-wrapper');
            contents.forEach(content => {
                content.style.display = 'none';
            });

            // إظهار المحتوى المحدد
            const tabId = this.getAttribute('data-tab');
            const activeContent = document.getElementById(tabId + '-content');
            if (activeContent) {
                activeContent.style.display = 'block';
            }
        });
    });
}

/**
 * ========= وظائف معرض الصور =========
 */

// تهيئة معرض الصور ووظائف التبديل بين الصور المصغرة
function initProductGallery() {
    // التبديل بين الصور المصغرة
    const thumbnails = document.querySelectorAll('.thumbnail-item');
    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', function() {
            // إزالة الفئة النشطة من جميع الصور المصغرة
            thumbnails.forEach(t => t.classList.remove('active'));

            // إضافة الفئة النشطة للصورة المصغرة المحددة
            this.classList.add('active');

            // تحديث الصورة الرئيسية
            const mainImage = document.querySelector('.main-image-container img');
            const thumbImage = this.querySelector('img');
            if (mainImage && thumbImage) {
                mainImage.src = thumbImage.src;
            }
        });
    });
}

/**
 * ========= وظائف التكبير الاحترافي =========
 */

// تهيئة نظام تكبير صور المنتج
function initProductZoom() {
    console.log("تهيئة وظيفة التكبير..."); // للتأكد من تنفيذ الدالة

    // العناصر الرئيسية - تحديد دقيق للصورة والحاوية
    const container = document.querySelector('.main-image-container');
    const mainImage = document.querySelector('.main-image-container img'); // تحديد أي صورة داخل الحاوية

    // التحقق من وجود العناصر
    if (!container || !mainImage) {
        console.error("لم يتم العثور على عناصر التكبير:", { container, mainImage });
        return;
    }

    console.log("تم العثور على العناصر:", { container, mainImage });

    // إضافة الفئة للصورة إذا لم تكن موجودة
    mainImage.classList.add('main-product-image');

    // إنشاء عناصر التكبير
    const zoomLens = document.createElement('div');
    zoomLens.classList.add('zoom-lens');

    const zoomResult = document.createElement('div');
    zoomResult.classList.add('zoom-result');

    // إضافة العناصر إلى الحاوية
    container.appendChild(zoomLens);
    container.appendChild(zoomResult);

    // إضافة عنصر إرشادات التكبير
    const instructions = document.createElement('div');
    instructions.classList.add('zoom-instructions');
    instructions.innerHTML = '<i class="fas fa-search-plus"></i> حرك المؤشر لتكبير الصورة';
    container.appendChild(instructions);

    // نسبة التكبير
    const zoomLevel = 4;

    // متغيرات للتتبع
    let isZooming = false;
    let imgRect;

    // إعداد صورة النتيجة
    const resultImage = new Image();
    resultImage.src = mainImage.src;
    resultImage.style.position = 'absolute';
    resultImage.style.maxWidth = 'none';
    zoomResult.appendChild(resultImage);

    // بدء عملية التكبير
    function startZoom() {
        console.log("بدء التكبير");
        imgRect = mainImage.getBoundingClientRect();
        isZooming = true;
        container.classList.add('zooming');
        zoomLens.style.display = 'block';
        zoomResult.style.display = 'block';
    }

    // إيقاف عملية التكبير
    function stopZoom() {
        console.log("إيقاف التكبير");
        isZooming = false;
        container.classList.remove('zooming');
        zoomLens.style.display = 'none';
        zoomResult.style.display = 'none';
    }

    // تحريك العدسة وتحديث الصورة المكبرة
    function moveZoom(e) {
        if (!isZooming) return;

        // منع السلوك الافتراضي
        e.preventDefault();

        // الحصول على موضع المؤشر بالنسبة للصفحة
        const mouseX = e.clientX;
        const mouseY = e.clientY;

        // الحصول على أبعاد وموضع الصورة
        const {left, top, width, height} = imgRect;

        // حساب موضع المؤشر بالنسبة للصورة
        let posX = mouseX - left;
        let posY = mouseY - top;

        // التأكد من أن المؤشر داخل الصورة
        if (posX < 0) posX = 0;
        if (posY < 0) posY = 0;
        if (posX > width) posX = width;
        if (posY > height) posY = height;

        // حساب النسب المئوية لموضع المؤشر في الصورة
        const mouseXPercent = posX / width;
        const mouseYPercent = posY / height;

        // حجم العدسة
        const lensWidth = zoomLens.offsetWidth;
        const lensHeight = zoomLens.offsetHeight;

        // موضع العدسة (تمركز حول المؤشر)
        let lensX = posX - lensWidth / 2;
        let lensY = posY - lensHeight / 2;

        // حدود العدسة
        if (lensX < 0) lensX = 0;
        if (lensY < 0) lensY = 0;
        if (lensX > width - lensWidth) lensX = width - lensWidth;
        if (lensY > height - lensHeight) lensY = height - lensHeight;

        // تحديث موضع العدسة
        zoomLens.style.left = `${lensX}px`;
        zoomLens.style.top = `${lensY}px`;

        // أبعاد الصورة المكبرة
        const zoomedWidth = width * zoomLevel;
        const zoomedHeight = height * zoomLevel;

        // حساب موضع الصورة المكبرة بناءً على موضع المؤشر مباشرة
        const resultX = mouseXPercent * (zoomedWidth - zoomResult.offsetWidth);
        const resultY = mouseYPercent * (zoomedHeight - zoomResult.offsetHeight);

        // تحديث حجم وموضع الصورة المكبرة
        resultImage.style.width = `${zoomedWidth}px`;
        resultImage.style.height = `${zoomedHeight}px`;
        resultImage.style.left = `${-resultX}px`;
        resultImage.style.top = `${-resultY}px`;
    }

    // ربط الأحداث
    container.addEventListener('mouseenter', startZoom);
    container.addEventListener('mouseleave', stopZoom);
    container.addEventListener('mousemove', moveZoom);

    // تحديث صورة التكبير عند تغيير الصورة الرئيسية
    function updateZoomImage(newSrc) {
        resultImage.src = newSrc;
    }

    // الاستماع لتغييرات الصورة المصغرة
    const thumbnails = document.querySelectorAll('.thumbnail-item');
    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', function() {
            const thumbImage = this.querySelector('img');
            if (thumbImage && mainImage) {
                mainImage.src = thumbImage.src;
                updateZoomImage(thumbImage.src);
            }
        });
    });
}

/**
 * ========= وظائف متغيرات المنتج =========
 */

// تهيئة اختيار متغيرات المنتج وتحديث حقل variant_id
function initVariantSelection() {
    // الحصول على جميع أزرار اختيار المتغيرات
    const variantOptions = document.querySelectorAll('.variant-option');

    // الحصول على حقل variant_id الخفي
    const selectedVariantIdField = document.getElementById('selectedVariantId');

    if (!variantOptions.length || !selectedVariantIdField) return;

    // إضافة مستمع حدث لكل خيار متغير
    variantOptions.forEach(option => {
        option.addEventListener('click', function() {
            // تجاهل العناصر غير المتوفرة
            if (this.classList.contains('out-of-stock')) return;

            // إزالة الفئة النشطة من جميع الخيارات في نفس المجموعة
            const group = this.closest('.variant-group');
            if (group) {
                group.querySelectorAll('.variant-option').forEach(opt => {
                    opt.classList.remove('active');
                });
            }

            // إضافة الفئة النشطة للخيار المحدد
            this.classList.add('active');

            // الحصول على معرف المتغير المحدد
            const variantId = this.getAttribute('data-variant-id');

            // تحديث الحقل الخفي
            if (variantId && selectedVariantIdField) {
                console.log("تم تحديد المتغير:", variantId);
                selectedVariantIdField.value = variantId;
            }

            // تحديث السعر إذا كان متاحاً
            updatePriceForVariant(variantId);
        });
    });

    // صفوف الجدول للمتغيرات (إذا كانت موجودة)
    const variantRows = document.querySelectorAll('.variant-row');
    if (variantRows.length) {
        variantRows.forEach(row => {
            row.addEventListener('click', function() {
                // تجاهل الصفوف غير المتوفرة
                if (this.classList.contains('out-of-stock')) return;

                // إزالة الفئة المحددة من جميع الصفوف
                variantRows.forEach(r => r.classList.remove('selected'));

                // إضافة الفئة المحددة للصف المحدد
                this.classList.add('selected');

                // الحصول على معرف المتغير المحدد
                const variantId = this.getAttribute('data-variant-id');

                // تحديث الحقل الخفي
                if (variantId && selectedVariantIdField) {
                    console.log("تم تحديد المتغير من الجدول:", variantId);
                    selectedVariantIdField.value = variantId;
                }

                // تحديث السعر إذا كان متاحاً
                updatePriceForVariant(variantId);
            });
        });
    }
}

// تحديث السعر بناءً على المتغير المحدد
function updatePriceForVariant(variantId) {
    if (!variantId) return;

    // البحث عن معلومات المتغير (يعتمد على هيكل الصفحة)
    const variantElement = document.querySelector(`.variant-option[data-variant-id="${variantId}"], .variant-row[data-variant-id="${variantId}"]`);

    if (variantElement) {
        const price = variantElement.getAttribute('data-price');
        if (price) {
            // تحديث عرض السعر
            const priceDisplay = document.querySelector('.current-price');
            if (priceDisplay) {
                priceDisplay.textContent = price + ' د.أ';
            }
        }
    }
}

/**
 * ========= وظائف إضافية =========
 */

// التحكم بالكمية مع مراعاة المتغير المحدد
function changeQuantity(change) {
    const input = document.getElementById('quantity');
    if (!input) return;

    const currentValue = parseInt(input.value) || 1;
    const newValue = currentValue + change;

    // الحصول على الحد الأقصى من المخزون المتوفر
    let max = parseInt(input.getAttribute('max')) || 999;

    // إذا كان هناك متغير محدد، استخدم كمية المخزون الخاصة به
    const selectedVariantId = document.getElementById('selectedVariantId');
    if (selectedVariantId && selectedVariantId.value) {
        const variantRow = document.querySelector(`.variant-row[data-variant-id="${selectedVariantId.value}"]`);
        if (variantRow) {
            const variantStock = parseInt(variantRow.dataset.stock) || 0;
            if (variantStock > 0) {
                max = variantStock;
            }
        }
    }

    // التحقق من الحدود
    if (newValue >= 1 && newValue <= max) {
        input.value = newValue;
    }

    // إذا وصلنا للحد الأقصى، أظهر تنبيه
    if (newValue >= max) {
        showNotification('warning', 'لقد وصلت إلى الحد الأقصى المتوفر من هذا المنتج');
    }
}

// إضافة للمفضلة
function addToWishlist(productId) {
    // التنفيذ
    showNotification('success', 'تمت إضافة المنتج إلى قائمة الأمنيات');
}

// إضافة للمقارنة
function addToCompare(productId) {
    // التنفيذ
    showNotification('info', 'تمت إضافة المنتج إلى المقارنة');
}

// مشاركة المنتج
function shareProduct() {
    const modal = new bootstrap.Modal(document.getElementById('shareModal'));
    modal.show();
}

// نسخ الرابط
function copyLink() {
    const input = document.getElementById('productLink');
    input.select();
    document.execCommand('copy');

    showNotification('success', 'تم نسخ الرابط بنجاح');
}

// دالة الإشعارات
function showNotification(type, message) {
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;

    const icons = {
        success: 'check-circle',
        error: 'times-circle',
        info: 'info-circle',
        warning: 'exclamation-triangle'
    };

    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${icons[type]} me-2"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(toast);

    // إظهار الإشعار
    setTimeout(() => toast.classList.add('show'), 100);

    // إزالة بعد 3 ثواني
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// تحديث عدد العناصر في السلة
<<<<<<< HEAD
// function updateCartCount() {
//     // تحديث عدد العناصر في السلة في الهيدر
//     const cartBadge = document.querySelector('.cart-count');
//     if (cartBadge) {
//         const currentCount = parseInt(cartBadge.textContent) || 0;
//         cartBadge.textContent = currentCount + 1;
//     }
// }

function updateCartCount(count) {
    // 1. تحديث جميع علامات السلة في الصفحة
    const cartBadges = document.querySelectorAll('.cart-badge');
    cartBadges.forEach(badge => {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'block' : 'none';
    });

    // 2. تحديث أي عناصر أخرى تعرض عدد العناصر
    const cartCountElements = document.querySelectorAll('.cart-count');
    cartCountElements.forEach(element => {
        element.textContent = count;
=======
function updateCartCount(count) {
    // تحديث عدد العناصر في السلة في الهيدر
    const cartBadges = document.querySelectorAll('.cart-badge');
    cartBadges.forEach(badge => {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
>>>>>>> main
    });
}

// نموذج إضافة المنتج للسلة (يتم تنفيذه بعد تحميل الصفحة)
document.addEventListener('DOMContentLoaded', function() {
    const addToCartForm = document.getElementById('addToCartForm');

    if (addToCartForm) {


        addToCartForm.addEventListener('submit', function(e) {
            // منع السلوك الافتراضي للنموذج
            e.preventDefault();

            // الحصول على معرف المنتج من الصفحة
            let productId;

            // محاولة الحصول على معرف المنتج من عنوان الصفحة
            const urlParts = window.location.pathname.split('/');
            const slugIndex = urlParts.indexOf('products') + 1;
            if (slugIndex > 0 && slugIndex < urlParts.length) {
                // الحصول على معرف المنتج من data-attribute
                const productElement = document.querySelector('[data-product-id]');
                if (productElement) {
                    productId = productElement.getAttribute('data-product-id');
                    console.log("تم العثور على معرف المنتج من العنصر:", productId);
                }
            }

            // إذا لم نجد معرف المنتج، نستخدم قيمة افتراضية
            if (!productId) {
                productId = "11"; // معرف المنتج الافتراضي - قم بتغييره حسب منتجك
                console.log("استخدام معرف المنتج الافتراضي:", productId);
            }

            // بناء المسار الصحيح يدوياً
            const correctUrl = `/cart/add/${productId}/`;
            console.log("المسار الصحيح للإرسال:", correctUrl);

            // باقي الكود كما هو...
            const btn = e.submitter || this.querySelector('button[type="submit"]');
            if (!btn) return;

            const originalContent = btn.innerHTML;

            // التحقق من اختيار متغير المنتج إذا كان مطلوباً
            const variantsContainer = document.querySelector('.variants-section');
            const selectedVariantId = document.getElementById('selectedVariantId');

            if (variantsContainer && !selectedVariantId.value) {
                showNotification('error', 'الرجاء اختيار متغير المنتج أولاً');
                return false;
            }

            // إظهار حالة التحميل
            btn.disabled = true;
            if (btn.querySelector('.btn-text') && btn.querySelector('.btn-loading')) {
                btn.querySelector('.btn-text').style.display = 'none';
                btn.querySelector('.btn-loading').style.display = 'inline';
            } else {
                btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري الإضافة...';
            }

            // جمع بيانات النموذج
            const formData = new FormData(this);

            // طباعة البيانات للتشخيص
            console.log("بيانات النموذج:");
            for (let pair of formData.entries()) {
                console.log(pair[0] + ': ' + pair[1]);
            }

            // إرسال الطلب للمسار الصحيح
            fetch(correctUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => {
                console.log("استجابة الخادم:", response.status, response.statusText);

                if (!response.ok) {
                    console.error("خطأ في الاستجابة:", response.status);
                    return response.text().then(text => {
                        console.error("محتوى الخطأ:", text);
                        throw new Error(`فشل في الاتصال بالخادم (${response.status})`);
                    });
                }

                return response.json();
            })
            .then(data => {
                console.log("بيانات الاستجابة:", data);

                if (data.success) {
<<<<<<< HEAD
                    btn.innerHTML = '<i class="fas fa-check me-2"></i>تمت الإضافة بنجاح';

                    // تحديث عدد العناصر في السلة
                    const cartBadge = document.querySelector('.cart-count');
                    if (cartBadge) {
                        cartBadge.textContent = data.cart_count;
                    }

                    updateCartCount(data.cart_count);

                    // إظهار إشعار النجاح
                    let productName = document.querySelector('.product-title').textContent;
                    let variantInfo = '';

                    // إضافة معلومات المتغير إذا كان محدداً
                    if (selectedVariantId.value) {
                        const selectedVariant = document.querySelector(`.variant-row[data-variant-id="${selectedVariantId.value}"]`);
                        if (selectedVariant) {
                            const color = selectedVariant.querySelector('td:nth-child(2)')?.textContent.trim();
                            const size = selectedVariant.querySelector('td:nth-child(3)')?.textContent.trim();
                            if (color || size) {
                                variantInfo = ` (${color}${size ? ' - ' + size : ''})`;
                            }
                        }
                    }

                    showNotification('success', `تمت إضافة "${productName}${variantInfo}" إلى السلة بنجاح`);

                    // إعادة تعيين الزر بعد ثانيتين
                    setTimeout(() => {
                        btn.disabled = false;
                        btn.innerHTML = originalText;
                    }, 2000);
=======
                    showNotification('success', data.message || 'تمت إضافة المنتج إلى السلة');
                    updateCartCount(data.cart_count);
>>>>>>> main
                } else {
                    showNotification('error', data.message || 'حدث خطأ أثناء إضافة المنتج للسلة');
                }
            })
            .catch(error => {
                console.error("خطأ:", error);
                showNotification('error', 'حدث خطأ أثناء إضافة المنتج للسلة. يرجى المحاولة مرة أخرى.');
            })
            .finally(() => {
                // إعادة الزر إلى حالته الأصلية
                btn.disabled = false;
                if (btn.querySelector('.btn-text') && btn.querySelector('.btn-loading')) {
                    btn.querySelector('.btn-text').style.display = 'inline';
                    btn.querySelector('.btn-loading').style.display = 'none';
                } else {
                    btn.innerHTML = originalContent;
                }
            });
        });
    }
});