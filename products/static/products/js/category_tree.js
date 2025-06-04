/**
 * شجرة الفئات - JavaScript محسن
 * يدير وظائف شجرة الفئات للتوسيع والطي والتحديد
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing category tree...');

    // التأكد من وجود شجرة الفئات
    const categoryTree = document.getElementById('categoryTree');
    if (!categoryTree) {
        console.warn('Category tree element not found');
        return;
    }

    // التحقق من وجود المتغير الذي يحدد مسار الفئة الحالية
    if (typeof currentCategoryPath === 'undefined') {
        console.warn('currentCategoryPath variable not defined, using empty array');
        window.currentCategoryPath = [];
    }

    // إضافة مستمعي الأحداث لأزرار التوسيع والطي
    initializeToggleListeners();

    // فتح الفئات التي تحتوي على الفئة الحالية تلقائياً
    expandCurrentCategoryPath();

    // تمييز الفئة الحالية في الشجرة
    highlightCurrentCategory();

    // إضافة مؤثرات التحويم
    addHoverEffects();

    console.log('Category tree initialized successfully');
});

/**
 * إضافة مستمعات الأحداث لأزرار التوسيع والطي
 */
function initializeToggleListeners() {
    // الحصول على جميع أيقونات التبديل
    const toggleIcons = document.querySelectorAll('.toggle-icon');
    console.log(`Found ${toggleIcons.length} toggle icons`);

    // إضافة مستمع حدث لكل أيقونة
    toggleIcons.forEach(icon => {
        icon.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            // العثور على عنصر الفئة الأب
            const categoryItem = this.closest('.category-item');
            // العثور على قائمة الفئات الفرعية
            const subcategoryList = categoryItem.querySelector('.subcategory-list');

            // تبديل حالة القائمة الفرعية
            if (subcategoryList) {
                const isExpanded = subcategoryList.style.display !== 'none';

                if (isExpanded) {
                    // إغلاق القائمة
                    subcategoryList.style.display = 'none';
                    this.classList.remove('expanded');
                    console.log(`Collapsed category: ${categoryItem.querySelector('.category-link').textContent.trim()}`);
                } else {
                    // فتح القائمة
                    subcategoryList.style.display = 'block';
                    this.classList.add('expanded');
                    console.log(`Expanded category: ${categoryItem.querySelector('.category-link').textContent.trim()}`);
                }
            }
        });
    });
}

/**
 * تمييز الفئة الحالية في الشجرة
 */
function highlightCurrentCategory() {
    // إذا كان المسار فارغاً، لا نقوم بأي إجراء
    if (!currentCategoryPath || currentCategoryPath.length === 0) {
        console.log('No current category to highlight');
        return;
    }

    console.log(`Current category path: ${JSON.stringify(currentCategoryPath)}`);

    // تمييز الفئة الحالية (أول عنصر في المسار)
    const currentCategoryId = currentCategoryPath[0];
    const currentCategoryItem = document.querySelector(`.category-item[data-category-id="${currentCategoryId}"]`);

    if (currentCategoryItem) {
        // تمييز الفئة الحالية
        const categoryLink = currentCategoryItem.querySelector('.category-link');
        if (categoryLink) {
            categoryLink.classList.add('active');
            categoryLink.style.fontWeight = 'bold';
            categoryLink.style.color = '#0d6efd';  // لون أزرق
            console.log(`Highlighted current category: ${categoryLink.textContent.trim()}`);
        }
    } else {
        console.warn(`Category with ID ${currentCategoryId} not found in the tree`);
    }
}

/**
 * فتح مسار الفئة الحالية تلقائياً
 */
function expandCurrentCategoryPath() {
    // إذا كان المسار فارغاً، لا نقوم بأي إجراء
    if (!currentCategoryPath || currentCategoryPath.length === 0) {
        console.log('No category path to expand');
        return;
    }

    console.log(`Expanding category path: ${JSON.stringify(currentCategoryPath)}`);

    // فتح كل فئة في المسار
    for (let categoryId of currentCategoryPath) {
        const categoryItem = document.querySelector(`.category-item[data-category-id="${categoryId}"]`);
        if (categoryItem) {
            const toggleIcon = categoryItem.querySelector('.toggle-icon');
            const subcategoryList = categoryItem.querySelector('.subcategory-list');

            // فتح قائمة الفئات الفرعية إذا كانت موجودة
            if (toggleIcon && subcategoryList) {
                // تغيير حالة الأيقونة
                toggleIcon.classList.add('expanded');
                // إظهار الفئات الفرعية
                subcategoryList.style.display = 'block';
                console.log(`Expanded category in path: ${categoryItem.querySelector('.category-link').textContent.trim()}`);
            }
        } else {
            console.warn(`Category with ID ${categoryId} not found in the tree`);
        }
    }
}

/**
 * إضافة مؤثرات التحويم
 */
function addHoverEffects() {
    // إضافة مؤثرات التحويم على عناصر الفئات
    const categoryItems = document.querySelectorAll('.category-item');

    categoryItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.classList.add('hover');
        });

        item.addEventListener('mouseleave', function() {
            this.classList.remove('hover');
        });
    });
}

/**
 * دالة للتشخيص - تظهر معلومات حول شجرة الفئات في وحدة التحكم
 */
function debugCategoryTree() {
    console.group('Category Tree Debug Info');

    const tree = document.getElementById('categoryTree');
    if (!tree) {
        console.error('Category tree element not found');
        console.groupEnd();
        return;
    }

    const rootItems = tree.querySelectorAll(':scope > li.category-item');
    console.log(`Root categories: ${rootItems.length}`);

    if (rootItems.length === 0) {
        const emptyMessage = tree.querySelector('.no-categories');
        console.log(`Empty message found: ${emptyMessage ? 'Yes' : 'No'}`);
        if (emptyMessage) {
            console.log(`Message text: ${emptyMessage.textContent.trim()}`);
        }
    } else {
        rootItems.forEach(item => {
            const name = item.querySelector('.category-link').textContent.trim();
            const hasChildren = item.querySelector('.subcategory-list') !== null;
            console.log(`- ${name} (has children: ${hasChildren ? 'Yes' : 'No'})`);
        });
    }

    console.log(`Current path: ${JSON.stringify(currentCategoryPath)}`);
    console.groupEnd();
}

// تشغيل التشخيص بعد 1 ثانية من تحميل الصفحة
setTimeout(debugCategoryTree, 1000);