// Advanced Filters JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // تهيئة شريط تمرير نطاق السعر (noUiSlider)
    initPriceRangeSlider();

    // تهيئة البحث في الفلاتر
    initFilterSearch();

    // تهيئة الفلاتر النشطة
    initActiveFilters();

    // تهيئة حدث مسح جميع الفلاتر
    initClearFilters();

    // تهيئة التبديل التلقائي للفلاتر
    initAutoApplyFilters();

    // تهيئة فتح/إغلاق الفلاتر في الشاشات الصغيرة
    initMobileFiltersToggle();

    // تهيئة أزرار نطاق السعر السريعة
    initPricePresetButtons();
});

/**
 * تهيئة شريط تمرير نطاق السعر باستخدام noUiSlider
 */
function initPriceRangeSlider() {
    const priceSlider = document.getElementById('priceRangeSlider');

    if (!priceSlider || typeof noUiSlider === 'undefined') return;

    s
    const minPriceInput = document.getElementById('minPrice');
    const maxPriceInput = document.getElementById('maxPrice');

    // الحصول على القيم الحالية من الفورم
    const minPrice = parseInt(minPriceInput.value) || 0;
    const maxPrice = parseInt(maxPriceInput.value) || 1000;

    // تهيئة شريط التمرير
    noUiSlider.create(priceSlider, {
        start: [minPrice, maxPrice],
        connect: true,
        step: 5,
        range: {
            'min': 0,
            'max': 1000
        },
        format: {
            to: value => Math.round(value),
            from: value => Math.round(value)
        }
    });

    // تحديث حقول الإدخال عند تحريك شريط التمرير
    priceSlider.noUiSlider.on('update', function(values, handle) {
        if (handle === 0) {
            minPriceInput.value = values[0];
        } else {
            maxPriceInput.value = values[1];
        }
    });

    // تحديث شريط التمرير عند تغيير قيم حقول الإدخال
    minPriceInput.addEventListener('change', function() {
        priceSlider.noUiSlider.set([this.value, null]);
    });

    maxPriceInput.addEventListener('change', function() {
        priceSlider.noUiSlider.set([null, this.value]);
    });
}

/**
 * تهيئة وظيفة البحث في قوائم الفلاتر (العلامات التجارية والفئات)
 */
function initFilterSearch() {
    // البحث في العلامات التجارية
    const brandSearch = document.querySelector('.brand-search');
    if (brandSearch) {
        brandSearch.addEventListener('input', function() {
            filterListItems(this.value, '.brand-item');
        });
    }

    // البحث في الفئات
    const categorySearch = document.querySelector('.category-search');
    if (categorySearch) {
        categorySearch.addEventListener('input', function() {
            filterListItems(this.value, '.category-item');
        });
    }
}

/**
 * فلترة عناصر القائمة بناءً على نص البحث
 */
function filterListItems(searchText, itemSelector) {
    const items = document.querySelectorAll(itemSelector);
    const searchLower = searchText.toLowerCase();

    items.forEach(item => {
        const text = item.querySelector('label').textContent.toLowerCase();
        if (text.includes(searchLower)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

/**
 * تهيئة أزرار إزالة الفلاتر النشطة
 */
function initActiveFilters() {
    document.querySelectorAll('.remove-filter').forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.dataset.filter;
            const value = this.dataset.value;

            removeFilter(filter, value);
        });
    });
}

/**
 * إزالة فلتر معين وإعادة تحميل الصفحة
 */
function removeFilter(filter, value) {
    const form = document.getElementById('advancedFilterForm');

    if (filter === 'price') {
        // إزالة فلتر السعر
        const minPrice = form.querySelector('[name="min_price"]');
        const maxPrice = form.querySelector('[name="max_price"]');

        if (minPrice) minPrice.value = '';
        if (maxPrice) maxPrice.value = '';
    } else if (value) {
        // إزالة فلتر بقيمة محددة (مثل علامة تجارية معينة)
        const inputs = form.querySelectorAll(`[name="${filter}"][value="${value}"]`);
        inputs.forEach(input => {
            input.checked = false;
        });
    } else {
        // إزالة فلتر بسيط (مثل الفلترات الثنائية)
        const input = form.querySelector(`[name="${filter}"]`);
        if (input) {
            if (input.type === 'checkbox') {
                input.checked = false;
            } else if (input.type === 'radio') {
                input.checked = false;
            } else {
                input.value = '';
            }
        }
    }

    // تقديم النموذج لتحديث النتائج
    form.submit();
}

/**
 * تهيئة زر مسح جميع الفلاتر
 */
function initClearFilters() {
    const clearButton = document.querySelector('.clear-filters-btn');
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            clearAllFilters();
        });
    }
}

/**
 * مسح جميع الفلاتر والعودة إلى الصفحة الأساسية
 */
function clearAllFilters() {
    // الحصول على الرابط الأساسي بدون معلمات
    const baseUrl = window.location.pathname;

    // الحفاظ على معلمات معينة مثل البحث والترتيب
    const urlParams = new URLSearchParams(window.location.search);
    const newParams = new URLSearchParams();

    // الاحتفاظ بمعلمات البحث والترتيب فقط
    if (urlParams.has('q')) {
        newParams.set('q', urlParams.get('q'));
    }

    if (urlParams.has('sort')) {
        newParams.set('sort', urlParams.get('sort'));
    }

    // إعادة تحميل الصفحة مع المعلمات المحفوظة فقط
    const newUrl = baseUrl + (newParams.toString() ? '?' + newParams.toString() : '');
    window.location.href = newUrl;
}

/**
 * تطبيق الفلاتر تلقائيًا عند تغيير أي فلتر
 */
function initAutoApplyFilters() {
    const autoSubmitElements = document.querySelectorAll(
        '#advancedFilterForm input[type="checkbox"], ' +
        '#advancedFilterForm input[type="radio"]'
    );

    autoSubmitElements.forEach(element => {
        element.addEventListener('change', function() {
            // يمكن تفعيل التقديم التلقائي إذا أردت
            // document.getElementById('advancedFilterForm').submit();

            // أو إظهار زر التطبيق بتأثير لفت الانتباه
            const applyButton = document.querySelector('#advancedFilterForm button[type="submit"]');
            if (applyButton) {
                applyButton.classList.add('btn-pulse');
                setTimeout(() => {
                    applyButton.classList.remove('btn-pulse');
                }, 1500);
            }
        });
    });
}

/**
 * تهيئة أزرار فتح/إغلاق الفلاتر في الشاشات الصغيرة
 */
function initMobileFiltersToggle() {
    // زر فتح الفلاتر
    const openFilterBtn = document.querySelector('.open-filter-sidebar');
    if (openFilterBtn) {
        openFilterBtn.addEventListener('click', function() {
            document.querySelector('.filters-sidebar-container').classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    }

    // زر إغلاق الفلاتر
    const closeFilterBtn = document.querySelector('.toggle-filter-sidebar');
    if (closeFilterBtn) {
        closeFilterBtn.addEventListener('click', function() {
            document.querySelector('.filters-sidebar-container').classList.remove('active');
            document.body.style.overflow = '';
        });
    }

    // إغلاق عند النقر خارج منطقة الفلاتر
    const filterContainer = document.querySelector('.filters-sidebar-container');
    if (filterContainer) {
        filterContainer.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }
}

/**
 * تهيئة أزرار نطاق السعر السريعة
 */
function initPricePresetButtons() {
    document.querySelectorAll('.price-preset').forEach(button => {
        button.addEventListener('click', function() {
            const minPrice = this.dataset.min;
            const maxPrice = this.dataset.max;

            const minInput = document.getElementById('minPrice');
            const maxInput = document.getElementById('maxPrice');

            if (minInput) minInput.value = minPrice;
            if (maxInput) maxInput.value = maxPrice;

            // تحديث شريط التمرير إذا كان موجودًا
            const priceSlider = document.getElementById('priceRangeSlider');
            if (priceSlider && priceSlider.noUiSlider) {
                priceSlider.noUiSlider.set([minPrice, maxPrice || 1000]);
            }
        });
    });
}

/**
 * إضافة تأثير نبض للزر
 */
document.addEventListener('DOMContentLoaded', function() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes btn-pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(var(--bs-primary-rgb), 0.7);
            }
            70% {
                box-shadow: 0 0 0 10px rgba(var(--bs-primary-rgb), 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(var(--bs-primary-rgb), 0);
            }
        }
        
        .btn-pulse {
            animation: btn-pulse 1.5s cubic-bezier(0.66, 0, 0, 1);
        }
    `;
    document.head.appendChild(style);
});