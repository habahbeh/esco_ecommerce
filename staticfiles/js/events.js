/**
 * ESCO Events JavaScript
 * جافاسكريبت لإدارة عرض الفعاليات في الموقع
 */

(function() {
    'use strict';

    // تهيئة الفعاليات عند تحميل الصفحة
    document.addEventListener('DOMContentLoaded', function() {
        initEventBanner();
    });

    /**
     * تهيئة الشريط الإعلاني للفعاليات
     */
    function initEventBanner() {
        // التحقق من أن المستخدم لم يقم بإغلاق الشريط مسبقاً
        const bannerClosed = localStorage.getItem('eventBannerClosed');
        if (bannerClosed === 'true') {
            return;
        }

        // جلب بيانات الفعالية النشطة
        fetch('/events/api/active-banner/')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.event) {
                    displayEventBanner(data.event);
                }
            })
            .catch(error => {
                console.error('Error fetching event banner:', error);
            });

        // إعداد زر الإغلاق
        const closeButton = document.getElementById('eventBannerClose');
        if (closeButton) {
            closeButton.addEventListener('click', function() {
                closeEventBanner(true); // حفظ حالة الإغلاق
            });
        }
    }

    /**
     * عرض الشريط الإعلاني بمعلومات الفعالية
     */
    function displayEventBanner(event) {
        const banner = document.getElementById('eventBanner');
        if (!banner) return;

        // ملء بيانات الشريط
        document.getElementById('eventBannerImage').src = event.banner_image;
        document.getElementById('eventBannerImage').alt = event.title;
        document.getElementById('eventBannerTitle').textContent = event.title;
        document.getElementById('eventBannerDescription').textContent = event.short_description;

        // إعداد زر العرض
        const button = document.getElementById('eventBannerButton');
        button.textContent = event.button_text;
        button.href = event.registration_url || event.url;

        // إضافة حالة الفعالية
        const statusElement = document.getElementById('eventBannerStatus');
        statusElement.textContent = event.status;
        statusElement.className = 'event-banner-status ' + event.status;

        // عرض الشريط بتأثير حركي
        banner.style.display = 'block';
        setTimeout(() => {
            banner.classList.add('show');

            // تعديل هامش الصفحة ليتناسب مع ارتفاع الشريط
            const bannerHeight = banner.offsetHeight;
            document.body.style.paddingTop = bannerHeight + 'px';

            // تعديل موضع الهيدر
            const header = document.getElementById('header');
            if (header) {
                header.style.top = bannerHeight + 'px';
            }
        }, 100);
    }

    /**
     * إغلاق الشريط الإعلاني
     */
    function closeEventBanner(savePreference = false) {
        const banner = document.getElementById('eventBanner');
        if (!banner) return;

        banner.classList.remove('show');

        // إزالة الهوامش والتنسيقات
        setTimeout(() => {
            banner.style.display = 'none';
            document.body.style.paddingTop = '';

            // إعادة موضع الهيدر
            const header = document.getElementById('header');
            if (header) {
                header.style.top = '';
            }
        }, 300);

        // حفظ تفضيلات المستخدم إذا طلب ذلك
        if (savePreference) {
            localStorage.setItem('eventBannerClosed', 'true');

            // مسح التفضيل بعد يوم واحد
            setTimeout(() => {
                localStorage.removeItem('eventBannerClosed');
            }, 24 * 60 * 60 * 1000);
        }
    }

    // إتاحة دوال معينة للاستخدام الخارجي
    window.ESCO_Events = {
        closeEventBanner: closeEventBanner
    };
})();