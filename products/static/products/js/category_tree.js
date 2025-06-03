/**
 * File: products/static/products/js/category_tree.js
 * التفاعل مع شجرة الفئات
 */

document.addEventListener('DOMContentLoaded', function() {
    // تهيئة شجرة الفئات
    initCategoryTree();
});

/**
 * تهيئة شجرة الفئات
 */
function initCategoryTree() {
    // إضافة مستمعي الأحداث لأزرار التوسيع والطي
    const toggleIcons = document.querySelectorAll('.toggle-icon');
    toggleIcons.forEach(icon => {
        icon.addEventListener('click', toggleCategory);
    });

    // استعادة حالة الشجرة من localStorage
    restoreTreeState();

    // تمييز الفئة الحالية ومسارها
    highlightCurrentCategory();
}

/**
 * توسيع أو طي فئة
 * @param {Event} e - حدث النقر
 */
function toggleCategory(e) {
    e.preventDefault();

    const categoryItem = this.closest('.category-item');
    const subcategoryList = categoryItem.querySelector('.subcategory-list');
    const categoryId = categoryItem.dataset.categoryId;

    // تبديل حالة التوسيع
    if (categoryItem.classList.contains('expanded')) {
        // طي الفئة
        categoryItem.classList.remove('expanded');
        subcategoryList.style.display = 'none';

        // حفظ الحالة
        saveTreeState(categoryId, false);
    } else {
        // توسيع الفئة
        categoryItem.classList.add('expanded');
        subcategoryList.style.display = 'block';

        // حفظ الحالة
        saveTreeState(categoryId, true);
    }
}

/**
 * حفظ حالة شجرة الفئات في localStorage
 * @param {string} categoryId - معرف الفئة
 * @param {boolean} isExpanded - هل الفئة موسعة
 */
function saveTreeState(categoryId, isExpanded) {
    // التحقق من دعم localStorage
    if (!isLocalStorageAvailable()) {
        return;
    }

    // الحصول على الحالة الحالية من localStorage
    let treeState = getTreeState();

    // تحديث حالة الفئة
    treeState[categoryId] = isExpanded;

    // حفظ الحالة المحدثة
    localStorage.setItem('categoryTreeState', JSON.stringify(treeState));
}

/**
 * استعادة حالة شجرة الفئات من localStorage
 */
function restoreTreeState() {
    // التحقق من دعم localStorage
    if (!isLocalStorageAvailable()) {
        return;
    }

    // الحصول على حالة الشجرة
    const treeState = getTreeState();

    // تطبيق الحالة على الفئات
    for (const categoryId in treeState) {
        const isExpanded = treeState[categoryId];
        const categoryItem = document.querySelector(`.category-item[data-category-id="${categoryId}"]`);

        if (categoryItem && isExpanded) {
            // توسيع الفئة
            categoryItem.classList.add('expanded');
            const subcategoryList = categoryItem.querySelector('.subcategory-list');
            if (subcategoryList) {
                subcategoryList.style.display = 'block';
            }
        }
    }
}

/**
 * الحصول على حالة شجرة الفئات من localStorage
 * @returns {Object} - حالة الشجرة
 */
function getTreeState() {
    // التحقق من دعم localStorage
    if (!isLocalStorageAvailable()) {
        return {};
    }

    // الحصول على الحالة من localStorage
    const storedState = localStorage.getItem('categoryTreeState');

    return storedState ? JSON.parse(storedState) : {};
}

/**
 * التحقق من توفر localStorage
 * @returns {boolean} - هل localStorage متوفر
 */
function isLocalStorageAvailable() {
    try {
        const test = 'test';
        localStorage.setItem(test, test);
        localStorage.removeItem(test);
        return true;
    } catch (e) {
        return false;
    }
}

/**
 * تمييز الفئة الحالية ومسارها في الشجرة
 */
function highlightCurrentCategory() {
    // التحقق إذا كان متغير المسار موجود (يتم تعريفه في قالب category_detail.html)
    if (typeof currentCategoryPath === 'undefined') {
        return;
    }

    // تمييز كل فئة في المسار
    currentCategoryPath.forEach(categoryId => {
        const categoryItem = document.querySelector(`.category-item[data-category-id="${categoryId}"]`);

        if (categoryItem) {
            // تمييز الفئة الحالية
            if (categoryId === currentCategoryPath[0]) {
                categoryItem.classList.add('category-active');
            } else {
                // تمييز فئات المسار
                categoryItem.classList.add('category-path');
            }

            // توسيع الفئات الأب
            const parentUl = categoryItem.closest('.subcategory-list');
            if (parentUl) {
                const parentLi = parentUl.closest('.category-item');
                if (parentLi) {
                    parentLi.classList.add('expanded');
                    parentUl.style.display = 'block';

                    // حفظ حالة التوسيع
                    saveTreeState(parentLi.dataset.categoryId, true);
                }
            }
        }
    });
}