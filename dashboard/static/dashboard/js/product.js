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

    // إضافة استدعاء لمحرر المتغيرات
    initProductVariantsEditor();

    // تهيئة محرر الخصائص الإضافية
    initAttributesEditor();

    // الحصول على حقول الخصم
    var discountPercentage = document.getElementById('id_discount_percentage');
    var discountAmount = document.getElementById('id_discount_amount');

    // التأكد من أن القيم الأولية صحيحة
    if (!discountPercentage.value || discountPercentage.value === '') {
        discountPercentage.value = '0';
    }

    if (!discountAmount.value || discountAmount.value === '') {
        discountAmount.value = '0';
    }

    // إضافة مستمعين للأحداث
    [discountPercentage, discountAmount].forEach(function(field) {
        // عند تغيير القيمة
        field.addEventListener('change', function() {
            if (this.value === '' || isNaN(parseFloat(this.value))) {
                this.value = '0';
            } else if (parseFloat(this.value) < 0) {
                this.value = '0';
            }
        });

        // عند فقدان التركيز
        field.addEventListener('blur', function() {
            if (this.value === '' || isNaN(parseFloat(this.value))) {
                this.value = '0';
            }
        });
    });


    setupAttributeDeleteButtons();

    // إعادة تهيئة أزرار الحذف بعد إضافة خاصية جديدة
    const addAttrBtn = document.getElementById('add-attr-btn');
    if (addAttrBtn) {
        addAttrBtn.addEventListener('click', function() {
            setTimeout(setupAttributeDeleteButtons, 100);
        });
    }

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
// تهيئة Select2
function setupSelect2() {
    if (window.jQuery && jQuery.fn.select2) {
        // التهيئة العامة
        jQuery('.select2').select2({
            dir: document.documentElement.getAttribute('dir'),
            placeholder: "اختر...",
            allowClear: true,
            width: '100%'
        });

        // تهيئة خاصة لحقل الفئة
        jQuery('#id_category').select2({
            dir: document.documentElement.getAttribute('dir'),
            placeholder: "اختر الفئة...",
            allowClear: true,
            width: '100%',
            templateResult: formatCategoryOption,
            templateSelection: formatCategorySelection,
            language: {
                noResults: function() {
                    return "لا توجد نتائج";
                },
                searching: function() {
                    return "جاري البحث...";
                }
            }
        });

        // تهيئة خاصة لحقل العلامة التجارية
        jQuery('#id_brand').select2({
            dir: document.documentElement.getAttribute('dir'),
            placeholder: "اختر العلامة التجارية...",
            allowClear: true,
            width: '100%',
            language: {
                noResults: function() {
                    return "لا توجد نتائج";
                },
                searching: function() {
                    return "جاري البحث...";
                }
            }
        });

        jQuery('#id_status').select2({
            dir: document.documentElement.getAttribute('dir'),
            width: '100%',
            minimumResultsForSearch: Infinity, // إخفاء البحث لأن الخيارات قليلة
            templateResult: formatStatusOption,
            templateSelection: formatStatusSelection
        });

        jQuery('.select2-stock-status').select2({
    dir: document.documentElement.getAttribute('dir'),
    width: '100%',
    minimumResultsForSearch: Infinity, // إخفاء البحث لأن الخيارات قليلة
    templateResult: formatStockStatusOption,
    templateSelection: formatStockStatusSelection
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

    function formatStatusOption(status) {
        if (!status.id) {
            return status.text;
        }

        var statusIcon = '';
        var statusClass = '';

        switch(status.id) {
            case 'published':
                statusIcon = '<i class="fa fa-check-circle text-success me-1"></i>';
                statusClass = 'text-success';
                break;
            case 'draft':
                statusIcon = '<i class="fa fa-edit text-secondary me-1"></i>';
                statusClass = 'text-secondary';
                break;
            case 'pending_review':
                statusIcon = '<i class="fa fa-clock text-warning me-1"></i>';
                statusClass = 'text-warning';
                break;
            case 'archived':
                statusIcon = '<i class="fa fa-archive text-danger me-1"></i>';
                statusClass = 'text-danger';
                break;
        }

        return $(
            '<span>' + statusIcon + '<span class="' + statusClass + '">' + status.text + '</span></span>'
        );
    }

    // دالة تنسيق الحالة المختارة
    function formatStatusSelection(status) {
        if (!status.id) {
            return status.text;
        }

        var statusIcon = '';

        switch(status.id) {
            case 'published':
                statusIcon = '<i class="fa fa-check-circle text-success me-1"></i>';
                break;
            case 'draft':
                statusIcon = '<i class="fa fa-edit text-secondary me-1"></i>';
                break;
            case 'pending_review':
                statusIcon = '<i class="fa fa-clock text-warning me-1"></i>';
                break;
            case 'archived':
                statusIcon = '<i class="fa fa-archive text-danger me-1"></i>';
                break;
        }

        return $(
            '<span>' + statusIcon + status.text + '</span>'
        );
    }




    // دالة تنسيق خيارات حالة المخزون
function formatStockStatusOption(state) {
    if (!state.id) {
        return state.text;
    }

    var icon = jQuery(state.element).data('icon');
    var statusClass = '';

    switch(state.id) {
        case 'in_stock':
            statusClass = 'text-success';
            break;
        case 'out_of_stock':
            statusClass = 'text-danger';
            break;
        case 'pre_order':
            statusClass = 'text-warning';
            break;
        default:
            statusClass = 'text-secondary';
    }

    return jQuery(
        '<span><i class="fas ' + icon + ' ' + statusClass + ' me-2"></i><span>' + state.text + '</span></span>'
    );
}

// دالة تنسيق حالة المخزون المختارة
function formatStockStatusSelection(state) {
    if (!state.id) {
        return state.text;
    }

    var icon = jQuery(state.element).data('icon');
    var statusClass = '';

    switch(state.id) {
        case 'in_stock':
            statusClass = 'text-success';
            break;
        case 'out_of_stock':
            statusClass = 'text-danger';
            break;
        case 'pre_order':
            statusClass = 'text-warning';
            break;
        default:
            statusClass = 'text-secondary';
    }

    return jQuery(
        '<span><i class="fas ' + icon + ' ' + statusClass + ' me-2"></i><span>' + state.text + '</span></span>'
    );
}

    // تنسيق خيارات الفئات للعرض بالتسلسل الهرمي
    function formatCategoryOption(category) {
        if (!category.id) {
            return category.text;
        }

        // التعامل مع المسافات البادئة للفئات الفرعية
        var $option = $(category.element);
        var level = ($option.text().match(/^\s+/) || [''])[0].length / 4;

        var $container = $('<span>');

        // إضافة مسافات للفئات الفرعية
        if (level > 0) {
            var $indent = $('<span>').html('&nbsp;'.repeat(level * 4));
            $container.append($indent);

            // إضافة أيقونة للفئات الفرعية
            var $icon = $('<i class="fa fa-level-up-alt fa-rotate-90 me-1 text-muted"></i>');
            $container.append($icon);
        }

        // إضافة نص الفئة
        var $text = $('<span>').text(category.text.trim());
        $container.append($text);

        return $container;
    }

    // تنسيق الفئة المختارة
    function formatCategorySelection(category) {
        if (!category.id) {
            return category.text;
        }
        return category.text.trim();
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
    const imagePreviews = document.getElementById('image-previews');
    const imagesDropzone = document.querySelector('.images-dropzone');

    if (addImageBtn && productImagesInput) {
        addImageBtn.addEventListener('click', function() {
            productImagesInput.click();
        });

        // تفعيل السحب والإفلات
        if (imagesDropzone) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                imagesDropzone.addEventListener(eventName, preventDefaults, false);
            });

            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }

            ['dragenter', 'dragover'].forEach(eventName => {
                imagesDropzone.addEventListener(eventName, highlight, false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                imagesDropzone.addEventListener(eventName, unhighlight, false);
            });

            function highlight() {
                imagesDropzone.classList.add('dragover');
            }

            function unhighlight() {
                imagesDropzone.classList.remove('dragover');
            }

            imagesDropzone.addEventListener('drop', handleDrop, false);

            function handleDrop(e) {
                const dt = e.dataTransfer;
                const files = dt.files;

                handleFiles(files);
            }
        }

        productImagesInput.addEventListener('change', function() {
            handleFiles(this.files);
        });

        function handleFiles(files) {
            if (files.length > 0) {
                // إخفاء رسالة السحب والإفلات بعد إضافة صور
                const dropzoneMessage = document.querySelector('.dropzone-message');
                if (dropzoneMessage) {
                    dropzoneMessage.style.display = 'none';
                }

                for (let i = 0; i < files.length; i++) {
                    let file = files[i];
                    let reader = new FileReader();

                    reader.onload = function(e) {
                        const uniqueId = 'temp-' + Date.now() + '-' + i;
                        const imagePreview = document.createElement('div');
                        imagePreview.className = 'image-preview-item temp-image';
                        imagePreview.dataset.tempId = uniqueId;

                        imagePreview.innerHTML = `
                            <div class="image-preview-inner">
                                <img src="${e.target.result}" alt="معاينة الصورة">
                                <div class="image-preview-overlay">
                                    <div class="image-preview-actions">
                                        <button type="button" class="btn btn-light btn-sm rounded-circle btn-remove-temp-image" title="حذف">
                                            <i class="fa fa-trash text-danger"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <div class="image-meta mt-1 small">
                                <span class="text-muted">${file.name.length > 20 ? file.name.substring(0, 17) + '...' : file.name}</span>
                            </div>
                        `;

                        // إضافة الصورة
                        imagePreviews.appendChild(imagePreview);

                        // إضافة حدث لحذف الصورة المؤقتة
                        imagePreview.querySelector('.btn-remove-temp-image').addEventListener('click', function() {
                            imagePreview.remove();

                            // إظهار رسالة السحب والإفلات إذا لم تعد هناك صور
                            if (document.querySelectorAll('.image-preview-item').length === 0) {
                                if (dropzoneMessage) {
                                    dropzoneMessage.style.display = 'block';
                                }
                            }
                        });
                    };

                    reader.readAsDataURL(file);
                }
            }
        }
    }

    // حذف الصور الحالية وجعل الصورة رئيسية
    // (نفس الكود السابق مع تحديثات بسيطة)
    document.querySelectorAll('.btn-remove-image').forEach(button => {
        button.addEventListener('click', function() {
            if (confirm("هل أنت متأكد من حذف هذه الصورة؟")) {
                const imageId = this.getAttribute('data-image-id');
                const imageItem = this.closest('.image-preview-item');

                // إضافة حقل مخفي لتتبع الصور المحذوفة
                const deletedImageInput = document.createElement('input');
                deletedImageInput.type = 'hidden';
                deletedImageInput.name = 'deleted_images[]';
                deletedImageInput.value = imageId;
                document.getElementById('product-form').appendChild(deletedImageInput);

                // إزالة الصورة من العرض
                imageItem.remove();

                // إظهار رسالة السحب والإفلات إذا لم تعد هناك صور
                if (document.querySelectorAll('.image-preview-item').length === 0) {
                    const dropzoneMessage = document.querySelector('.dropzone-message');
                    if (dropzoneMessage) {
                        dropzoneMessage.style.display = 'block';
                    }
                }
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

            const imageItem = this.closest('.image-preview-item');
            imageItem.classList.add('is-primary');

            // إضافة شارة الصورة الرئيسية
            if (!imageItem.querySelector('.image-preview-badge')) {
                const badge = document.createElement('div');
                badge.className = 'image-preview-badge';
                badge.innerHTML = '<i class="fa fa-check-circle me-1"></i>رئيسية';
                imageItem.querySelector('.image-preview-inner').appendChild(badge);
            }

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

document.querySelectorAll('.feature-switch').forEach(function(switchElem) {
    // جعل النقر على الحاوية بأكملها يبدل حالة الاختيار
    switchElem.addEventListener('click', function(e) {
        // منع التكرار إذا تم النقر على المفتاح نفسه
        if (e.target.tagName !== 'INPUT') {
            const checkbox = this.querySelector('input[type="checkbox"]');
            checkbox.checked = !checkbox.checked;

            // إطلاق حدث تغيير لتنفيذ أي منطق مرتبط
            const event = new Event('change', { bubbles: true });
            checkbox.dispatchEvent(event);
        }
    });

    // تحديث مظهر المفتاح عند تغيير حالة الاختيار
    const checkbox = switchElem.querySelector('input[type="checkbox"]');
    checkbox.addEventListener('change', function() {
        if (this.checked) {
            switchElem.classList.add('active');
        } else {
            switchElem.classList.remove('active');
        }
    });

    // تهيئة الحالة الأولية
    if (checkbox.checked) {
        switchElem.classList.add('active');
    }
});

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

// إدارة متغيرات المنتج (Variants)
function initProductVariantsEditor() {
    console.log("تهيئة محرر متغيرات المنتج");

    // العناصر
    const variantsContainer = document.getElementById('variants-container');
    const variantsTableBody = document.getElementById('variants-table-body');
    const addVariantBtn = document.getElementById('add-variant-btn');
    const variantsJsonInput = document.getElementById('product_variants_json');
    const deletedVariantsInput = document.getElementById('deleted_variants_json');

    if (!variantsContainer || !variantsTableBody || !addVariantBtn || !variantsJsonInput || !deletedVariantsInput) {
        console.log("لم يتم العثور على عناصر متغيرات المنتج", {
            variantsContainer: !!variantsContainer,
            variantsTableBody: !!variantsTableBody,
            addVariantBtn: !!addVariantBtn,
            variantsJsonInput: !!variantsJsonInput,
            deletedVariantsInput: !!deletedVariantsInput
        });
        return;
    }

    console.log("تم العثور على عناصر متغيرات المنتج");

    // قائمة المتغيرات
    let variants = [];
    let deletedVariants = [];

    // قراءة المتغيرات الحالية
    try {
        const variantsJson = variantsJsonInput.value;
        if (variantsJson) {
            variants = JSON.parse(variantsJson);
            console.log("تم تحميل المتغيرات:", variants);
        }
    } catch (e) {
        console.error("خطأ في تحليل متغيرات المنتج:", e);
        variants = [];
    }

    // رقم سالب للمتغيرات الجديدة (المؤقتة)
    let tempVariantId = -1;

    // دالة إنشاء نافذة حذف المتغيرات
    function setupVariantDeleteModal() {
        // التحقق من وجود النافذة المنبثقة
        if (!document.getElementById('deleteVariantModal')) {
            // إنشاء عناصر Modal
            const deleteModal = document.createElement('div');
            deleteModal.className = 'modal fade';
            deleteModal.id = 'deleteVariantModal';
            deleteModal.tabIndex = '-1';
            deleteModal.setAttribute('aria-labelledby', 'deleteVariantModalLabel');
            deleteModal.setAttribute('aria-hidden', 'true');

            deleteModal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header text-secondary">
                            <h5 class="modal-title" id="deleteVariantModalLabel">حذف متغير المنتج</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="إغلاق"></button>
                        </div>
                        <div class="modal-body">
                            <input type="hidden" id="delete-variant-index" value="">
                            <p>سيتم حذف المتغير <strong id="variant-name-to-delete"></strong>.</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إلغاء</button>
                            <button type="button" class="btn btn-danger" id="confirm-delete-variant">حذف</button>
                        </div>
                    </div>
                </div>
            `;

            // إضافة Modal إلى الصفحة
            document.body.appendChild(deleteModal);
        }

        // تهيئة معالج حدث تأكيد الحذف
        document.getElementById('confirm-delete-variant').addEventListener('click', function() {
            const indexToDelete = parseInt(document.getElementById('delete-variant-index').value);

            if (!isNaN(indexToDelete) && indexToDelete >= 0 && indexToDelete < variants.length) {
                const variant = variants[indexToDelete];

                // إذا كان المتغير مخزناً في قاعدة البيانات، أضفه إلى قائمة المحذوفات
                if (variant.id > 0) {
                    deletedVariants.push(variant.id);
                    deletedVariantsInput.value = JSON.stringify(deletedVariants);
                }

                // إزالة المتغير من القائمة
                variants.splice(indexToDelete, 1);
                updateVariantsJson();

                // إعادة عرض المتغيرات مع تأثير بصري
                const variantsTableRows = document.querySelectorAll('#variants-table-body tr');
                if (indexToDelete < variantsTableRows.length) {
                    const rowToDelete = variantsTableRows[indexToDelete];
                    rowToDelete.style.transition = 'all 0.3s';
                    rowToDelete.style.opacity = '0';
                    rowToDelete.style.transform = 'translateX(20px)';

                    setTimeout(() => {
                        renderVariants();
                    }, 300);
                } else {
                    renderVariants();
                }

                // إغلاق النافذة المنبثقة
                const modalInstance = bootstrap.Modal.getInstance(document.getElementById('deleteVariantModal'));
                modalInstance.hide();
            }
        });
    }

    // عرض المتغيرات
    function renderVariants() {
        variantsTableBody.innerHTML = '';

        // إذا لم تكن هناك متغيرات، نعرض رسالة
        if (variants.length === 0) {
            const row = document.createElement('tr');
            row.id = 'no-variants-row';
            row.innerHTML = `
                <td colspan="6" class="text-center text-muted py-3">
                    <i class="fa fa-info-circle me-1"></i> لا توجد متغيرات للمنتج. أضف متغيرات باستخدام الزر أعلاه.
                </td>
            `;
            variantsTableBody.appendChild(row);
            return;
        }

        // عرض المتغيرات في الجدول
        variants.forEach((variant, index) => {
            const row = document.createElement('tr');
            row.setAttribute('data-variant-id', variant.id || tempVariantId);

            // محتوى الصف
            row.innerHTML = `
                <td>${variant.name}</td>
                <td>${variant.sku || '-'}</td>
                <td>
                    ${renderAttributes(variant.attributes)}
                </td>
                <td>
                    <div class="input-group input-group-sm">
                        <input type="number" class="form-control variant-price" 
                            value="${variant.base_price !== null ? variant.base_price : ''}" 
                            placeholder="السعر الأساسي">
                        <span class="input-group-text">د.ا</span>
                    </div>
                </td>
                <td>
                    <input type="number" class="form-control form-control-sm variant-stock" 
                        value="${variant.stock_quantity !== null ? variant.stock_quantity : 0}" min="0">
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-primary edit-variant-btn" title="تعديل">
                            <i class="fa fa-edit"></i>
                        </button>
                        <button type="button" class="btn btn-danger delete-variant-btn" title="حذف">
                            <i class="fa fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            variantsTableBody.appendChild(row);

            // أحداث التعديل والحذف
            const editBtn = row.querySelector('.edit-variant-btn');
            const deleteBtn = row.querySelector('.delete-variant-btn');
            const priceInput = row.querySelector('.variant-price');
            const stockInput = row.querySelector('.variant-stock');

            // حدث زر التعديل
            editBtn.addEventListener('click', () => {
                editVariant(variant, index);
            });

            // حدث زر الحذف
            deleteBtn.addEventListener('click', () => {
                deleteVariant(variant, index);
            });

            // تحديث السعر
            priceInput.addEventListener('change', () => {
                const newPrice = parseFloat(priceInput.value) || null;
                variants[index].base_price = newPrice;
                updateVariantsJson();
            });

            // تحديث المخزون
            stockInput.addEventListener('change', () => {
                const newStock = parseInt(stockInput.value) || 0;
                variants[index].stock_quantity = newStock;
                updateVariantsJson();
            });
        });
    }

    // عرض خصائص المتغير
    function renderAttributes(attributes) {
        if (!attributes || Object.keys(attributes).length === 0) {
            return '<span class="text-muted">-</span>';
        }

        const attributeItems = [];
        for (const [key, value] of Object.entries(attributes)) {
            attributeItems.push(`<span class="badge bg-light text-dark">${key}: ${value}</span>`);
        }

        return attributeItems.join(' ');
    }

    // حذف متغير - يجب تعريفها قبل استخدامها
    function deleteVariant(variant, index) {
        // تهيئة نافذة حذف المتغير إذا لم تكن موجودة
        if (!document.getElementById('deleteVariantModal')) {
            setupVariantDeleteModal();
        }

        // تعيين المؤشر واسم المتغير في النافذة المنبثقة
        document.getElementById('delete-variant-index').value = index;
        document.getElementById('variant-name-to-delete').textContent = variant.name;

        // عرض النافذة المنبثقة
        const deleteModal = document.getElementById('deleteVariantModal');
        const modalInstance = bootstrap.Modal.getInstance(deleteModal) || new bootstrap.Modal(deleteModal);
        modalInstance.show();
    }

    // إضافة متغير جديد
    function addVariant() {
        // فتح مربع حوار إضافة متغير
        openVariantModal({
            id: tempVariantId--,
            name: '',
            sku: '',
            attributes: {},
            base_price: null,
            stock_quantity: 0,
            is_active: true,
            is_default: variants.length === 0, // جعل المتغير الأول افتراضياً
            sort_order: variants.length
        }, -1);
    }

    // تعديل متغير
    function editVariant(variant, index) {
        openVariantModal(variant, index);
    }


    // فتح مربع حوار المتغير
    function openVariantModal(variant, index) {
        // إنشاء مربع الحوار
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'variantModal';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('aria-labelledby', 'variantModalLabel');
        modal.setAttribute('aria-hidden', 'true');

        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="variantModalLabel">
                            ${index === -1 ? 'إضافة متغير جديد' : 'تعديل المتغير'}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="إغلاق"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <label for="variant-name" class="form-label">اسم المتغير <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="variant-name" 
                                    value="${variant.name}" placeholder="مثال: أحمر، كبير، 128GB" required>
                            </div>
                            <div class="col-md-6">
                                <label for="variant-sku" class="form-label">رقم المتغير (SKU)</label>
                                <input type="text" class="form-control" id="variant-sku" 
                                    value="${variant.sku}" placeholder="سيتم إنشاؤه تلقائياً إذا تُرك فارغاً">
                            </div>
                        </div>

                        <div class="row mb-3">
                            <div class="col-md-6">
                                <label for="variant-price" class="form-label">السعر</label>
                                <div class="input-group">
                                    <input type="number" class="form-control" id="variant-price" 
                                        value="${variant.base_price !== null ? variant.base_price : ''}" 
                                        placeholder="سعر المتغير (اختياري)">
                                    <span class="input-group-text">د.ا</span>
                                </div>
                                <div class="form-text">اترك فارغاً لاستخدام سعر المنتج الأساسي</div>
                            </div>
                            <div class="col-md-6">
                                <label for="variant-stock" class="form-label">المخزون</label>
                                <input type="number" class="form-control" id="variant-stock" 
                                    value="${variant.stock_quantity}" min="0">
                            </div>
                        </div>

                        <div class="row mb-3">
                            <div class="col-md-6">
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="variant-active" 
                                        ${variant.is_active ? 'checked' : ''}>
                                    <label class="form-check-label" for="variant-active">متغير نشط</label>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="variant-default" 
                                        ${variant.is_default ? 'checked' : ''}>
                                    <label class="form-check-label" for="variant-default">متغير افتراضي</label>
                                </div>
                            </div>
                        </div>

                        <hr>

                        <h6>خصائص المتغير</h6>
                        <p class="text-muted small">أضف خصائص مثل اللون، الحجم، السعة، إلخ.</p>

                        <div id="variant-attributes">
                            <!-- ستتم إضافة الخصائص هنا -->
                        </div>

                        <div class="d-flex mt-2 mb-3">
                            <div class="flex-grow-1 me-2">
                                <input type="text" class="form-control" id="attribute-key" placeholder="اسم الخاصية (مثل: اللون)">
                            </div>
                            <div class="flex-grow-1 me-2">
                                <input type="text" class="form-control" id="attribute-value" placeholder="قيمة الخاصية (مثل: أحمر)">
                            </div>
                            <div>
                                <button type="button" id="add-attribute-btn" class="btn btn-secondary">إضافة</button>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إلغاء</button>
                        <button type="button" class="btn btn-primary" id="save-variant-btn">حفظ المتغير</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // عرض الخصائص الحالية
        const variantAttributes = document.getElementById('variant-attributes');
        function renderVariantAttributes() {
            variantAttributes.innerHTML = '';

            if (Object.keys(variant.attributes).length === 0) {
                variantAttributes.innerHTML = '<div class="text-muted">لا توجد خصائص محددة</div>';
                return;
            }

            const attrTable = document.createElement('table');
            attrTable.className = 'table table-sm table-bordered';
            attrTable.innerHTML = `
                <thead class="table-light">
                    <tr>
                        <th>الخاصية</th>
                        <th>القيمة</th>
                        <th width="60"></th>
                    </tr>
                </thead>
                <tbody id="attr-table-body"></tbody>
            `;
            variantAttributes.appendChild(attrTable);

            const attrTableBody = document.getElementById('attr-table-body');
            for (const [key, value] of Object.entries(variant.attributes)) {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${key}</td>
                    <td>${value}</td>
                    <td class="text-center">
                        <button type="button" class="btn btn-sm btn-danger delete-attr-btn" data-key="${key}">
                            <i class="fa fa-times"></i>
                        </button>
                    </td>
                `;
                attrTableBody.appendChild(row);

                // حدث حذف الخاصية
                row.querySelector('.delete-attr-btn').addEventListener('click', function() {
                    const key = this.getAttribute('data-key');
                    delete variant.attributes[key];
                    renderVariantAttributes();
                });
            }
        }

        renderVariantAttributes();

        // إضافة خاصية جديدة
        const addAttributeBtn = document.getElementById('add-attribute-btn');
        const attributeKey = document.getElementById('attribute-key');
        const attributeValue = document.getElementById('attribute-value');

        addAttributeBtn.addEventListener('click', function() {
            const key = attributeKey.value.trim();
            const value = attributeValue.value.trim();

            if (!key) {
                alert('الرجاء إدخال اسم الخاصية');
                attributeKey.focus();
                return;
            }

            variant.attributes[key] = value;
            attributeKey.value = '';
            attributeValue.value = '';
            attributeKey.focus();
            renderVariantAttributes();
        });

        // إضافة الأحداث للحقول
        attributeKey.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                attributeValue.focus();
            }
        });

        attributeValue.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addAttributeBtn.click();
            }
        });

        // زر حفظ المتغير
        const saveVariantBtn = document.getElementById('save-variant-btn');
        saveVariantBtn.addEventListener('click', function() {
            const variantName = document.getElementById('variant-name').value.trim();
            const variantSku = document.getElementById('variant-sku').value.trim();
            const variantPrice = document.getElementById('variant-price').value.trim();
            const variantStock = document.getElementById('variant-stock').value.trim();
            const variantActive = document.getElementById('variant-active').checked;
            const variantDefault = document.getElementById('variant-default').checked;

            if (!variantName) {
                alert('الرجاء إدخال اسم المتغير');
                document.getElementById('variant-name').focus();
                return;
            }

            // تحديث بيانات المتغير
            variant.name = variantName;
            variant.sku = variantSku;
            variant.base_price = variantPrice ? parseFloat(variantPrice) : null;
            variant.stock_quantity = variantStock ? parseInt(variantStock) : 0;
            variant.is_active = variantActive;
            variant.is_default = variantDefault;

            // إضافة/تحديث المتغير في القائمة
            if (index === -1) {
                variants.push(variant);
            } else {
                variants[index] = variant;
            }

            // إذا تم تعيين هذا المتغير كافتراضي، إلغاء تعيين المتغيرات الأخرى
            if (variant.is_default) {
                variants.forEach((v, i) => {
                    if (i !== index) {
                        v.is_default = false;
                    }
                });
            }

            // تحديث JSON وإعادة عرض المتغيرات
            updateVariantsJson();
            renderVariants();

            // إغلاق مربع الحوار
            const modalElement = document.getElementById('variantModal');
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            modalInstance.hide();


        });

        // عرض مربع الحوار
        const modalElement = document.getElementById('variantModal');
        const modalInstance = new bootstrap.Modal(modalElement);
        modalInstance.show();

        // تنظيف عند إغلاق مربع الحوار
        modalElement.addEventListener('hidden.bs.modal', function() {
            document.body.removeChild(modalElement);
        });
    }

    // تحديث حقل JSON المخفي
    function updateVariantsJson() {
        variantsJsonInput.value = JSON.stringify(variants);
    }

    // إضافة الأحداث
    addVariantBtn.addEventListener('click', addVariant);

    // تهيئة العرض الأولي
    renderVariants();
}

// تهيئة محرر الخصائص الإضافية
function initAttributesEditor() {
    const addAttrBtn = document.getElementById('add-attr-btn');
    const attrName = document.getElementById('attr-name');
    const attrType = document.getElementById('attr-type');
    const attrOptionsContainer = document.getElementById('attr-options-container');
    const attrOptions = document.getElementById('attr-options');
    const attributesTableBody = document.getElementById('attributes-table-body');
    const deletedAttributes = document.getElementById('deleted-attributes');

    // قائمة للخصائص المحذوفة
    let deletedAttributeIds = [];

    // تغيير عرض حقل الخيارات بناءً على نوع الخاصية
    if (attrType) {
        attrType.addEventListener('change', function() {
            if (this.value === 'select' || this.value === 'multiselect') {
                attrOptionsContainer.style.display = 'block';
            } else {
                attrOptionsContainer.style.display = 'none';
            }
        });
    }

    // إضافة خاصية جديدة
    if (addAttrBtn && attrName && attrType) {
        addAttrBtn.addEventListener('click', function() {
            const name = attrName.value.trim();
            const type = attrType.value;

            if (!name) {
                alert('الرجاء إدخال اسم الخاصية');
                attrName.focus();
                return;
            }

            // إنشاء معرف مؤقت للخاصية الجديدة
            const tempId = 'new_' + new Date().getTime();

            // إنشاء صف جديد
            const row = document.createElement('tr');
            row.setAttribute('data-attr-id', tempId);

            // إنشاء محتوى الصف
            row.innerHTML = `
                <td>${name}</td>
                <td><span class="badge bg-secondary">${type}</span></td>
                <td>
                    <input type="text" name="attribute_${tempId}" class="form-control form-control-sm">
                    <input type="hidden" name="new_attribute_name_${tempId}" value="${name}">
                    <input type="hidden" name="new_attribute_type_${tempId}" value="${type}">
                    ${type === 'select' || type === 'multiselect' ? 
                      `<input type="hidden" name="new_attribute_options_${tempId}" value="${attrOptions.value}">` : ''}
                </td>
                <td>
                    <button type="button" class="btn btn-sm btn-danger delete-attr-btn" data-attr-id="${tempId}">
                        <i class="fa fa-trash"></i>
                    </button>
                </td>
            `;

            // إضافة الصف للجدول
            const noAttributesRow = document.getElementById('no-attributes-row');
            if (noAttributesRow) {
                noAttributesRow.remove();
            }

            attributesTableBody.appendChild(row);

            // إضافة حدث للزر حذف
            row.querySelector('.delete-attr-btn').addEventListener('click', function() {
                const attrId = this.getAttribute('data-attr-id');
                if (attrId.startsWith('new_')) {
                    // إذا كانت خاصية جديدة، نحذفها فقط من DOM
                    row.remove();
                } else {
                    // إذا كانت خاصية موجودة، نضيفها لقائمة المحذوفة
                    deletedAttributeIds.push(attrId);
                    deletedAttributes.value = JSON.stringify(deletedAttributeIds);
                    row.remove();
                }

                // إعادة عرض رسالة "لا توجد خصائص" إذا لم تعد هناك خصائص
                if (attributesTableBody.children.length === 0) {
                    const emptyRow = document.createElement('tr');
                    emptyRow.id = 'no-attributes-row';
                    emptyRow.innerHTML = `
                        <td colspan="4" class="text-center text-muted py-3">
                            <i class="fa fa-info-circle me-1"></i> لا توجد خصائص إضافية للمنتج. أضف خصائص باستخدام النموذج أعلاه.
                        </td>
                    `;
                    attributesTableBody.appendChild(emptyRow);
                }
            });

            // إعادة تعيين النموذج
            attrName.value = '';
            attrType.value = 'text';
            attrOptions.value = '';
            attrOptionsContainer.style.display = 'none';
            attrName.focus();
        });
    }

    // // إضافة أحداث للأزرار الموجودة مسبقًا
    // document.querySelectorAll('.delete-attr-btn').forEach(button => {
    //     button.addEventListener('click', function() {
    //         const attrId = this.getAttribute('data-attr-id');
    //         const row = this.closest('tr');
    //
    //         if (confirm('هل أنت متأكد من حذف هذه الخاصية؟')) {
    //             // إضافة معرف الخاصية لقائمة المحذوفة
    //             deletedAttributeIds.push(attrId);
    //             deletedAttributes.value = JSON.stringify(deletedAttributeIds);
    //
    //             // حذف الصف من الجدول
    //             row.remove();
    //
    //             // إعادة عرض رسالة "لا توجد خصائص" إذا لم تعد هناك خصائص
    //             if (attributesTableBody.children.length === 0) {
    //                 const emptyRow = document.createElement('tr');
    //                 emptyRow.id = 'no-attributes-row';
    //                 emptyRow.innerHTML = `
    //                     <td colspan="4" class="text-center text-muted py-3">
    //                         <i class="fa fa-info-circle me-1"></i> لا توجد خصائص إضافية للمنتج. أضف خصائص باستخدام النموذج أعلاه.
    //                     </td>
    //                 `;
    //                 attributesTableBody.appendChild(emptyRow);
    //             }
    //         }
    //     });
    // });
}

function ensureMinimumZero(input) {
    // إذا كانت القيمة فارغة أو أقل من صفر، نعيدها إلى صفر
    if (input.value === '' || parseFloat(input.value) < 0) {
        input.value = '0';
    }
}


// إضافة أحداث للأزرار الموجودة مسبقًا
function setupAttributeDeleteButtons() {
    // متغيرات عامة
    const attributesTableBody = document.getElementById('attributes-table-body');
    const deletedAttributes = document.getElementById('deleted-attributes');
    let deletedAttributeIds = [];

    // تهيئة قائمة الخصائص المحذوفة
    if (deletedAttributes && deletedAttributes.value) {
        try {
            deletedAttributeIds = JSON.parse(deletedAttributes.value);
        } catch(e) {
            deletedAttributeIds = [];
        }
    }

    // إنشاء Modal ديناميكياً إذا لم يكن موجوداً
    let deleteModal = document.getElementById('deleteAttributeModal');

    if (!deleteModal) {
        // إنشاء عناصر Modal
        deleteModal = document.createElement('div');
        deleteModal.className = 'modal fade';
        deleteModal.id = 'deleteAttributeModal';
        deleteModal.tabIndex = '-1';
        deleteModal.setAttribute('aria-labelledby', 'deleteAttributeModalLabel');
        deleteModal.setAttribute('aria-hidden', 'true');

        deleteModal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header  text-secondary">
                        <h5 class="modal-title" id="deleteAttributeModalLabel">حذف الخاصية</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="إغلاق"></button>
                    </div>
                    <div class="modal-body">
                        <input type="hidden" id="delete-attr-id" value="">
                        <p>سيتم حذف الخاصية.</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إلغاء</button>
                        <button type="button" class="btn btn-danger" id="confirm-delete-attr">حذف</button>
                    </div>
                </div>
            </div>
        `;

        // إضافة Modal إلى الصفحة
        document.body.appendChild(deleteModal);

        // تهيئة كائن Modal من Bootstrap
        const modalInstance = new bootstrap.Modal(deleteModal);

        // إضافة حدث لزر التأكيد
        document.getElementById('confirm-delete-attr').addEventListener('click', function() {
            const attrId = document.getElementById('delete-attr-id').value;
            const row = document.querySelector(`tr[data-attr-id="${attrId}"]`);

            // إضافة معرف الخاصية لقائمة المحذوفة إذا لم تكن خاصية جديدة
            if (!attrId.startsWith('new_')) {
                deletedAttributeIds.push(attrId);
                deletedAttributes.value = JSON.stringify(deletedAttributeIds);
            }

            // تطبيق تأثير بصري ثم حذف الصف
            row.style.transition = 'all 0.3s';
            row.style.opacity = '0';
            row.style.transform = 'translateX(20px)';

            setTimeout(() => {
                row.remove();

                // إعادة عرض رسالة "لا توجد خصائص" إذا لم تعد هناك خصائص
                if (attributesTableBody.children.length === 0) {
                    const emptyRow = document.createElement('tr');
                    emptyRow.id = 'no-attributes-row';
                    emptyRow.innerHTML = `
                        <td colspan="4" class="text-center text-muted py-3">
                            <i class="fa fa-info-circle me-1"></i> لا توجد خصائص إضافية للمنتج. أضف خصائص باستخدام النموذج أعلاه.
                        </td>
                    `;
                    attributesTableBody.appendChild(emptyRow);
                }

                // إغلاق النافذة المنبثقة
                modalInstance.hide();
            }, 300);
        });
    }

    // إضافة المعالج لجميع أزرار الحذف
    document.querySelectorAll('.delete-attr-btn').forEach(button => {
        button.addEventListener('click', function() {
            const attrId = this.getAttribute('data-attr-id');
            const attrName = this.closest('tr').querySelector('td:first-child').textContent;

            // تعيين المعرف في النموذج المخفي
            document.getElementById('delete-attr-id').value = attrId;

            // تعديل رسالة النافذة المنبثقة
            const modalBody = document.querySelector('#deleteAttributeModal .modal-body p');
            modalBody.innerHTML = `سيتم حذف الخاصية <strong>${attrName}</strong>`;

            // عرض النافذة المنبثقة
            const modalInstance = bootstrap.Modal.getInstance(deleteModal) || new bootstrap.Modal(deleteModal);
            modalInstance.show();
        });
    });
}


