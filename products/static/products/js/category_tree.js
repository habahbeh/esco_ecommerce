document.addEventListener('DOMContentLoaded', function() {
    // تفعيل الفئات في المسار النشط
    activateCategoryPath();
});

function activateCategoryPath() {
    // الحصول على مسار الفئة الحالي
    const currentCategoryPath = window.currentCategoryPath || [];

    if (!currentCategoryPath.length) return;

    // تفعيل الفئات في المسار
    currentCategoryPath.forEach(categoryId => {
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