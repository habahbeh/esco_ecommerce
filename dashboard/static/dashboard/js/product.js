// static/dashboard/js/product.js

// تنفيذ الكود عند اكتمال تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    console.log("تم تحميل الصفحة");

    // التحقق من صحة النموذج
    setupFormValidation();

    // تهيئة محرر المواصفات
    initSpecificationsEditor();

    // تهيئة محرر الميزات
    initFeaturesEditor();

    // تهيئة محرر Select2 إذا كان موجوداً
    setupSelect2();

    // تهيئة محرر Summernote إذا كان موجوداً
    setupSummernote();

    // تهيئة أزرار الصور
    setupImageButtons();

    // تهيئة أزرار الحالة
    setupStatusButtons();

    // تهيئة وظائف الخصم
    setupDiscountFunctions();

    // تهيئة وظائف المخزون المتقدمة
    setupAdvancedInventory();

    // تهيئة تبويب التخطي للأخطاء
    setupTabErrorNavigation();
});

// وظيفة للتحقق من صحة النموذج
function setupFormValidation() {
    const form = document.getElementById('product-form');

    if (form) {
        form.addEventListener('submit', function(event) {
            // منع الإرسال التلقائي للنموذج
            event.preventDefault();

            // إزالة رسائل الخطأ السابقة
            document.querySelectorAll('.alert-validation').forEach(el => el.remove());
            document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));

            let hasError = false;

            // التحقق من الحقول المطلوبة
            const requiredFields = [
                { id: 'id_name', message: 'الرجاء إدخال اسم المنتج' },
                { id: 'id_category', message: 'الرجاء اختيار فئة للمنتج' },
                { id: 'id_base_price', message: 'الرجاء إدخال سعر المنتج' },
                { id: 'id_description', message: 'الرجاء إدخال وصف المنتج' },
                { id: 'id_sku', message: 'الرجاء إدخال رقم المنتج (SKU)' }
            ];

            for (const field of requiredFields) {
                const element = document.getElementById(field.id);
                if (!element || !element.value.trim()) {
                    showError(element, field.message);
                    hasError = true;
                }
            }

            // التحقق من قيم الخصم
            const discountPercentage = parseFloat(document.getElementById('id_discount_percentage')?.value || 0);
            const discountAmount = parseFloat(document.getElementById('id_discount_amount')?.value || 0);

            if (discountPercentage > 0 && discountAmount > 0) {
                showError(document.getElementById('id_discount_percentage'), 'لا يمكن استخدام نسبة الخصم ومبلغ الخصم معًا');
                showError(document.getElementById('id_discount_amount'), 'لا يمكن استخدام نسبة الخصم ومبلغ الخصم معًا');
                hasError = true;
            }

            // التحقق من تاريخ الخصم
            const discountStart = document.getElementById('id_discount_start')?.value;
            const discountEnd = document.getElementById('id_discount_end')?.value;

            if (discountStart && discountEnd && new Date(discountStart) >= new Date(discountEnd)) {
                showError(document.getElementById('id_discount_end'), 'تاريخ نهاية الخصم يجب أن يكون بعد تاريخ البداية');
                hasError = true;
            }

            if (hasError) {
                // إضافة رسالة خطأ عامة
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-danger mb-4';
                alertDiv.innerHTML = '<strong>الرجاء تصحيح الأخطاء أدناه قبل حفظ المنتج</strong>';
                form.prepend(alertDiv);

                // الانتقال إلى التبويب الذي يحتوي على أول خطأ
                const firstErrorField = document.querySelector('.is-invalid');
                if (firstErrorField) {
                    const tabPane = firstErrorField.closest('.tab-pane');
                    if (tabPane) {
                        const tabId = tabPane.id;
                        document.querySelector(`#productTabs a[href="#${tabId}"]`).click();

                        // التمرير إلى الحقل الذي يحتوي على الخطأ
                        firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }

                return false;
            }

            // إذا لم تكن هناك أخطاء، أرسل النموذج
            form.submit();
        });
    }
}

// دالة لعرض رسالة خطأ تحت حقل معين
function showError(element, message) {
    if (!element) return;

    element.classList.add('is-invalid');

    // إنشاء عنصر رسالة الخطأ
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger mt-2 alert-validation';
    errorDiv.innerHTML = `<i class="fa fa-exclamation-circle me-1"></i> ${message}`;

    // إضافة رسالة الخطأ بعد الحقل
    const parent = element.closest('.mb-3') || element.parentNode;
    parent.appendChild(errorDiv);
}

// محرر المواصفات
function initSpecificationsEditor() {
    // العناصر
    const outputField = document.getElementById('id_specifications_json');
    const addButton = document.getElementById('add-spec-btn');
    const keyInput = document.getElementById('spec-key');
    const valueInput = document.getElementById('spec-value');
    const tableBody = document.getElementById('specs-table-body');

    if (!outputField || !tableBody) {
        console.log("لم يتم العثور على عناصر المواصفات", {
            outputField: !!outputField,
            tableBody: !!tableBody,
            addButton: !!addButton,
            keyInput: !!keyInput,
            valueInput: !!valueInput
        });
        return;
    }

    console.log("تم العثور على عناصر المواصفات");

    // المواصفات الحالية
    let specifications = {};

    // قراءة القيمة الأولية
    if (outputField.value) {
        try {
            specifications = JSON.parse(outputField.value);
            console.log("تم تحميل المواصفات:", specifications);
        } catch (e) {
            console.error("خطأ في تحليل المواصفات:", e);
            specifications = {};
        }
    }

    // عرض المواصفات الحالية
    function renderSpecifications() {
        tableBody.innerHTML = '';

        // إذا لم تكن هناك مواصفات، نعرض رسالة
        if (Object.keys(specifications).length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td colspan="3" class="text-center text-muted">
                    لا توجد مواصفات حتى الآن. أضف مواصفات للمنتج.
                </td>
            `;
            tableBody.appendChild(row);
            return;
        }

        // عرض المواصفات في الجدول
        for (const key in specifications) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${key}</td>
                <td>${specifications[key]}</td>
                <td>
                    <button type="button" class="btn btn-sm btn-danger" data-key="${key}">
                        حذف
                    </button>
                </td>
            `;
            tableBody.appendChild(row);

            // إضافة حدث للزر حذف
            row.querySelector('button').addEventListener('click', function() {
                const key = this.getAttribute('data-key');
                delete specifications[key];
                updateOutput();
                renderSpecifications();
            });
        }
    }

    // تحديث حقل الإخراج
    function updateOutput() {
        outputField.value = JSON.stringify(specifications);
    }

    // إضافة مواصفة جديدة
    function addSpecification() {
        const key = keyInput.value.trim();
        const value = valueInput.value.trim();

        if (!key) {
            alert('الرجاء إدخال اسم الخاصية');
            keyInput.focus();
            return;
        }

        specifications[key] = value;
        keyInput.value = '';
        valueInput.value = '';
        keyInput.focus();

        updateOutput();
        renderSpecifications();
        console.log("تمت إضافة المواصفة:", key, value);
    }

    // تسجيل الأحداث
    if (addButton) {
        addButton.addEventListener('click', addSpecification);
        console.log("تم إضافة حدث النقر على زر إضافة المواصفات");
    }

    if (keyInput && valueInput) {
        keyInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                valueInput.focus();
            }
        });

        valueInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addSpecification();
            }
        });
    }

    // تهيئة العرض الأولي
    renderSpecifications();
}

// محرر الميزات
function initFeaturesEditor() {
    // العناصر
    const outputField = document.getElementById('id_features_json');
    const addButton = document.getElementById('add-feature-btn');
    const featureInput = document.getElementById('feature-input');
    const featuresList = document.getElementById('features-list');

    if (!outputField || !featuresList || !addButton || !featureInput) {
        console.log("لم يتم العثور على عناصر الميزات", {
            outputField: !!outputField,
            featuresList: !!featuresList,
            addButton: !!addButton,
            featureInput: !!featureInput
        });
        return;
    }

    console.log("تم العثور على عناصر الميزات");

    // الميزات الحالية
    let features = [];

    // قراءة القيمة الأولية
    if (outputField.value) {
        try {
            features = JSON.parse(outputField.value);
            if (!Array.isArray(features)) {
                features = [];
            }
            console.log("تم تحميل الميزات:", features);
        } catch (e) {
            console.error("خطأ في تحليل الميزات:", e);
            features = [];
        }
    }

    // عرض الميزات الحالية
    function renderFeatures() {
        featuresList.innerHTML = '';

        // إذا لم تكن هناك ميزات، نعرض رسالة
        if (features.length === 0) {
            const item = document.createElement('li');
            item.className = 'list-group-item text-center text-muted';
            item.textContent = 'لا توجد ميزات حتى الآن. أضف ميزات للمنتج.';
            featuresList.appendChild(item);
            return;
        }

        // عرض الميزات في القائمة
        features.forEach((feature, index) => {
            const item = document.createElement('li');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            item.innerHTML = `
                <span>${feature}</span>
                <div class="btn-group">
                    <button type="button" class="btn btn-sm btn-secondary" data-index="${index}" data-action="up" ${index === 0 ? 'disabled' : ''}>
                        <i class="fa fa-arrow-up"></i>
                    </button>
                    <button type="button" class="btn btn-sm btn-secondary" data-index="${index}" data-action="down" ${index === features.length - 1 ? 'disabled' : ''}>
                        <i class="fa fa-arrow-down"></i>
                    </button>
                    <button type="button" class="btn btn-sm btn-danger" data-index="${index}" data-action="delete">
                        <i class="fa fa-times"></i>
                    </button>
                </div>
            `;
            featuresList.appendChild(item);

            // إضافة أحداث للأزرار
            const buttons = item.querySelectorAll('button');
            buttons.forEach(button => {
                button.addEventListener('click', function() {
                    const index = parseInt(this.getAttribute('data-index'));
                    const action = this.getAttribute('data-action');

                    if (action === 'delete') {
                        features.splice(index, 1);
                    } else if (action === 'up' && index > 0) {
                        [features[index - 1], features[index]] = [features[index], features[index - 1]];
                    } else if (action === 'down' && index < features.length - 1) {
                        [features[index], features[index + 1]] = [features[index + 1], features[index]];
                    }

                    updateOutput();
                    renderFeatures();
                });
            });
        });
    }

    // تحديث حقل الإخراج
    function updateOutput() {
        outputField.value = JSON.stringify(features);
    }

    // إضافة ميزة جديدة
    function addFeature() {
        const feature = featureInput.value.trim();

        if (!feature) {
            alert('الرجاء إدخال ميزة');
            featureInput.focus();
            return;
        }

        features.push(feature);
        featureInput.value = '';
        featureInput.focus();

        updateOutput();
        renderFeatures();
        console.log("تمت إضافة الميزة:", feature);
    }

    // تسجيل الأحداث
    addButton.addEventListener('click', addFeature);
    console.log("تم إضافة حدث النقر على زر إضافة الميزات");

    featureInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addFeature();
        }
    });

    // تهيئة العرض الأولي
    renderFeatures();
}

// تهيئة Select2
function setupSelect2() {
    if (window.jQuery && jQuery.fn.select2) {
        jQuery('.select2').select2({
            dir: document.documentElement.getAttribute('dir'),
            placeholder: "اختر...",
            allowClear: true,
            width: '100%'
        });

        // البحث عن المنتجات ذات الصلة
        jQuery('#id_related_products, #id_cross_sell_products, #id_upsell_products').select2({
            dir: document.documentElement.getAttribute('dir'),
            placeholder: "اختر المنتجات...",
            allowClear: true,
            width: '100%',
            ajax: {
                url: "/dashboard/products/autocomplete/",
                dataType: 'json',
                delay: 250,
                data: function(params) {
                    return {
                        q: params.term,
                        page: params.page
                    };
                },
                processResults: function(data, params) {
                    params.page = params.page || 1;
                    return {
                        results: data.results,
                        pagination: {
                            more: data.more
                        }
                    };
                },
                cache: true
            },
            minimumInputLength: 2
        });
    }
}

// تهيئة Summernote
function setupSummernote() {
    if (window.jQuery && jQuery.fn.summernote) {
        jQuery('.rich-text-editor').summernote({
            height: 300,
            toolbar: [
                ['style', ['style']],
                ['font', ['bold', 'underline', 'clear']],
                ['color', ['color']],
                ['para', ['ul', 'ol', 'paragraph']],
                ['table', ['table']],
                ['insert', ['link', 'picture']],
                ['view', ['fullscreen', 'codeview', 'help']]
            ],
            lang: 'ar-AR',
            placeholder: "أدخل وصفاً تفصيلياً للمنتج هنا..."
        });
    }
}

// تهيئة أزرار الصور
function setupImageButtons() {
    // إضافة صور جديدة
    const addImageBtn = document.getElementById('add-image-btn');
    const productImagesInput = document.getElementById('product_images');

    if (addImageBtn && productImagesInput) {
        addImageBtn.addEventListener('click', function() {
            productImagesInput.click();
        });

        productImagesInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                for (let i = 0; i < this.files.length; i++) {
                    let file = this.files[i];
                    let reader = new FileReader();

                    reader.onload = function(e) {
                        const imagePreview = document.createElement('div');
                        imagePreview.className = 'image-preview-item temp-image';
                        imagePreview.innerHTML = `
                            <img src="${e.target.result}" alt="معاينة الصورة">
                            <div class="image-preview-actions">
                                <button type="button" class="btn-remove-temp-image" title="حذف">
                                    <i class="fa fa-trash text-danger"></i>
                                </button>
                            </div>
                        `;

                        // إضافة الصورة قبل زر الإضافة
                        addImageBtn.parentNode.insertBefore(imagePreview, addImageBtn);

                        // إضافة حدث لحذف الصورة المؤقتة
                        imagePreview.querySelector('.btn-remove-temp-image').addEventListener('click', function() {
                            imagePreview.remove();
                        });
                    };

                    reader.readAsDataURL(file);
                }
            }
        });
    }

    // حذف الصور الحالية
    document.querySelectorAll('.btn-remove-image').forEach(button => {
        button.addEventListener('click', function() {
            if (confirm("هل أنت متأكد من حذف هذه الصورة؟")) {
                const imageId = this.getAttribute('data-image-id');
                // هنا يمكن إضافة طلب AJAX لحذف الصورة
                this.closest('.image-preview-item').remove();
            }
        });
    });

    // جعل الصورة رئيسية
    document.querySelectorAll('.btn-make-primary').forEach(button => {
        button.addEventListener('click', function() {
            const imageId = this.getAttribute('data-image-id');
            document.getElementById('primary_image').value = imageId;

            // تحديث واجهة المستخدم
            document.querySelectorAll('.image-preview-item').forEach(item => {
                item.classList.remove('is-primary');
                const badge = item.querySelector('.image-preview-badge');
                if (badge) badge.remove();
            });

            this.closest('.image-preview-item').classList.add('is-primary');
            const badge = document.createElement('div');
            badge.className = 'image-preview-badge';
            badge.textContent = 'الصورة الرئيسية';
            this.closest('.image-preview-item').appendChild(badge);

            // تحديث أيقونة النجمة
            document.querySelectorAll('.btn-make-primary i').forEach(icon => {
                icon.classList.remove('text-warning');
                icon.classList.add('text-muted');
            });

            this.querySelector('i').classList.remove('text-muted');
            this.querySelector('i').classList.add('text-warning');
        });
    });
}

// تهيئة أزرار الحالة
function setupStatusButtons() {
    const statusSwitch = document.getElementById('status_switch');
    const statusField = document.getElementById('id_status');
    const statusLabel = document.getElementById('status_label');

    if (statusSwitch && statusField) {
        statusSwitch.addEventListener('change', function() {
            if (this.checked) {
                statusField.value = 'published';
                statusLabel.innerHTML = '<i class="fa fa-eye text-success me-1"></i> منشور';
            } else {
                statusField.value = 'draft';
                statusLabel.innerHTML = '<i class="fa fa-eye-slash text-secondary me-1"></i> مسودة';
            }
        });
    }

    const visibilitySwitch = document.getElementById('visibility_switch');
    const isActiveField = document.getElementById('id_is_active');
    const visibilityLabel = document.getElementById('visibility_label');

    if (visibilitySwitch && isActiveField) {
        visibilitySwitch.addEventListener('change', function() {
            if (this.checked) {
                isActiveField.checked = true;
                visibilityLabel.innerHTML = '<i class="fa fa-check-circle text-success me-1"></i> نشط';
            } else {
                isActiveField.checked = false;
                visibilityLabel.innerHTML = '<i class="fa fa-ban text-danger me-1"></i> غير نشط';
            }
        });
    }
}

// تهيئة وظائف الخصم
function setupDiscountFunctions() {
    // العناصر
    const discountPercentage = document.getElementById('id_discount_percentage');
    const discountAmount = document.getElementById('id_discount_amount');
    const discountStart = document.getElementById('id_discount_start');
    const discountEnd = document.getElementById('id_discount_end');
    const basePrice = document.getElementById('id_base_price');
    const previewContent = document.querySelector('.discount-preview-content');

    if (!discountPercentage || !discountAmount || !basePrice || !previewContent) {
        return;
    }

    // منع استخدام نسبة الخصم ومبلغ الخصم معًا
    discountPercentage.addEventListener('input', function() {
        if (parseFloat(this.value) > 0) {
            discountAmount.value = 0;
        }
        updateDiscountPreview();
    });

    discountAmount.addEventListener('input', function() {
        if (parseFloat(this.value) > 0) {
            discountPercentage.value = 0;
        }
        updateDiscountPreview();
    });

    // تحديث المعاينة عند تغيير أي من حقول الخصم
    basePrice.addEventListener('input', updateDiscountPreview);
    discountStart.addEventListener('change', updateDiscountPreview);
    discountEnd.addEventListener('change', updateDiscountPreview);

    // دالة تحديث معاينة الخصم
    function updateDiscountPreview() {
        const base = parseFloat(basePrice.value) || 0;
        const percentage = parseFloat(discountPercentage.value) || 0;
        const amount = parseFloat(discountAmount.value) || 0;

        let currentPrice = base;
        let hasDiscount = false;
        let savingsPercentage = 0;

        // حساب السعر الحالي والخصم
        if (percentage > 0) {
            currentPrice = base - (base * percentage / 100);
            hasDiscount = true;
            savingsPercentage = percentage;
        } else if (amount > 0) {
            currentPrice = base - amount;
            hasDiscount = true;
            savingsPercentage = Math.round((amount / base) * 100);
        }

        // التحقق من فترة الخصم
        const now = new Date();
        const start = discountStart.value ? new Date(discountStart.value) : null;
        const end = discountEnd.value ? new Date(discountEnd.value) : null;

        // التحقق من أن الخصم نشط الآن
        if (hasDiscount) {
            if (start && start > now) {
                hasDiscount = false; // الخصم لم يبدأ بعد
            } else if (end && end < now) {
                hasDiscount = false; // الخصم منتهي
            }
        }

        // تحديث معاينة الخصم
        if (hasDiscount && currentPrice < base) {
            previewContent.innerHTML = `
                <div class="d-flex align-items-center">
                    <div class="h5 mb-0 me-2 product-price">${currentPrice.toFixed(2)} د.ا</div>
                    <div class="text-decoration-line-through text-muted">${base.toFixed(2)} د.ا</div>
                    <div class="badge bg-danger ms-2">${savingsPercentage}% خصم</div>
                </div>
            `;
        } else {
            previewContent.innerHTML = `
                <div class="d-flex align-items-center">
                    <div class="h5 mb-0 me-2 product-price">${base.toFixed(2)} د.ا</div>
                </div>
            `;
        }
    }

    // تهيئة المعاينة عند تحميل الصفحة
    updateDiscountPreview();
}

// تهيئة وظائف المخزون المتقدمة
function setupAdvancedInventory() {
    const trackInventory = document.getElementById('id_track_inventory');
    const stockQuantity = document.getElementById('id_stock_quantity');
    const reservedQuantity = document.getElementById('id_reserved_quantity');
    const isDigital = document.getElementById('id_is_digital');

    if (!trackInventory || !stockQuantity || !reservedQuantity || !isDigital) {
        return;
    }

    // إلغاء تعطيل حقل الكمية المتوفرة للمنتجات الجديدة
    stockQuantity.disabled = false;

    // عند تغيير المنتج الرقمي، تعطيل تتبع المخزون
    isDigital.addEventListener('change', function() {
        if (this.checked) {
            trackInventory.checked = false;
            trackInventory.disabled = true;
            stockQuantity.disabled = true;
            reservedQuantity.disabled = true;
        } else {
            trackInventory.disabled = false;
            stockQuantity.disabled = !trackInventory.checked;
            reservedQuantity.disabled = !trackInventory.checked;
        }
    });

    // عند تغيير تتبع المخزون
    trackInventory.addEventListener('change', function() {
        //stockQuantity.disabled = !this.checked;
        reservedQuantity.disabled = !this.checked;
    });

    // تهيئة الحالة الأولية
    if (isDigital.checked) {
        trackInventory.checked = false;
        trackInventory.disabled = true;
        //stockQuantity.disabled = true;
        reservedQuantity.disabled = true;
    } else {
        //stockQuantity.disabled = !trackInventory.checked;
        reservedQuantity.disabled = !trackInventory.checked;
    }
}

// تهيئة تبويب التخطي للأخطاء
function setupTabErrorNavigation() {
    // الانتقال بين التبويبات عند الضغط على التبويب
    const tabLinks = document.querySelectorAll('#productTabs a[data-bs-toggle="tab"]');
    tabLinks.forEach(link => {
        link.addEventListener('click', function() {
            // حفظ التبويب المحدد في التخزين المحلي
            localStorage.setItem('activeProductTab', this.getAttribute('href'));
        });
    });

    // استعادة التبويب المحفوظ عند تحميل الصفحة
    const savedTab = localStorage.getItem('activeProductTab');
    if (savedTab) {
        const tabElement = document.querySelector(`#productTabs a[href="${savedTab}"]`);
        if (tabElement) {
            tabElement.click();
        }
    }

    // إضافة أيقونات الخطأ إلى علامات التبويب
    const form = document.getElementById('product-form');
    if (form) {
        form.addEventListener('submit', function(event) {
            // إزالة جميع أيقونات الخطأ
            document.querySelectorAll('.tab-error-icon').forEach(el => el.remove());

            // التحقق من كل تبويب للأخطاء
            document.querySelectorAll('.tab-pane').forEach(tabPane => {
                const hasErrors = tabPane.querySelectorAll('.is-invalid, .alert-validation').length > 0;
                if (hasErrors) {
                    const tabId = tabPane.id;
                    const tabLink = document.querySelector(`#productTabs a[href="#${tabId}"]`);

                    // إضافة أيقونة خطأ إلى علامة التبويب
                    const errorIcon = document.createElement('span');
                    errorIcon.className = 'tab-error-icon ms-1 text-danger';
                    errorIcon.innerHTML = '<i class="fa fa-exclamation-circle"></i>';
                    tabLink.appendChild(errorIcon);
                }
            });
        });
    }
}