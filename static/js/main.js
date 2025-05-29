// وظائف مساعدة لتحسين تجربة المستخدم
document.addEventListener('DOMContentLoaded', function() {
    // إضافة تأثيرات التمرير السلس لروابط الموقع
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // إضافة تأثير عند النقر على زر إضافة إلى السلة
    const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');
    if (addToCartButtons) {
        addToCartButtons.forEach(button => {
            button.addEventListener('click', function() {
                // إضافة فئة للتأثير المرئي
                this.classList.add('btn-success');

                // إعادة الزر إلى الحالة الأصلية بعد ثانية واحدة
                setTimeout(() => {
                    this.classList.remove('btn-success');
                }, 1000);
            });
        });
    }
});