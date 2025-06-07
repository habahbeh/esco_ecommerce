/**
 * dashboard.js - وظائف JavaScript للوحة التحكم
 * المسار: dashboard/static/dashboard/js/dashboard.js
 */

document.addEventListener('DOMContentLoaded', function() {
    // المتغيرات العامة
    const body = document.querySelector('body');
    const sidebar = document.getElementById('sidebar');
    const sidebarCollapseDesktop = document.getElementById('sidebarCollapseDesktop');
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const menuItems = document.querySelectorAll('.menu-item > a');
    const isRTL = document.documentElement.lang === 'ar' || document.documentElement.dir === 'rtl';

    /**
     * ===== وظائف الشريط الجانبي =====
     */

    // تبديل حالة الشريط الجانبي (للأجهزة المكتبية)
    if (sidebarCollapseDesktop) {
        sidebarCollapseDesktop.addEventListener('click', function() {
            body.classList.toggle('sidebar-collapsed');

            // حفظ تفضيل المستخدم في التخزين المحلي للمتصفح
            const isCollapsed = body.classList.contains('sidebar-collapsed');
            localStorage.setItem('sidebar_collapsed', isCollapsed);

            // الحفاظ على انتقال سلس للمحتوى
            adjustMainContentForSidebar();
        });
    }

    // فتح/إغلاق الشريط الجانبي (للأجهزة المحمولة)
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function(e) {
            e.preventDefault();
            body.classList.toggle('sidebar-open');

            // تغيير أيقونة الزر
            const icon = this.querySelector('i');
            if (icon) {
                if (body.classList.contains('sidebar-open')) {
                    icon.className = 'fa fa-times';
                } else {
                    icon.className = 'fa fa-bars';
                }
            }
        });
    }

    // إغلاق الشريط الجانبي عند النقر خارجه (للأجهزة المحمولة)
    document.addEventListener('click', function(event) {
        const isSidebarOpen = body.classList.contains('sidebar-open');
        const clickedInsideSidebar = sidebar && sidebar.contains(event.target);
        const clickedOnToggler = sidebarCollapse && sidebarCollapse.contains(event.target);

        if (isSidebarOpen && !clickedInsideSidebar && !clickedOnToggler) {
            body.classList.remove('sidebar-open');

            // إعادة أيقونة الزر
            if (sidebarCollapse) {
                const icon = sidebarCollapse.querySelector('i');
                if (icon) {
                    icon.className = 'fa fa-bars';
                }
            }
        }
    });

    // استعادة حالة الشريط الجانبي من التخزين المحلي
    const initializeSidebar = () => {
        const isCollapsed = localStorage.getItem('sidebar_collapsed') === 'true';
        if (isCollapsed) {
            body.classList.add('sidebar-collapsed');
        }

        // ضبط المحتوى الرئيسي بناءً على حالة الشريط الجانبي
        adjustMainContentForSidebar();

        // إضافة التأثيرات المرئية للشريط الجانبي
        enhanceSidebarVisuals();
    };

    // ضبط المحتوى الرئيسي بناءً على حالة الشريط الجانبي
    const adjustMainContentForSidebar = () => {
        const mainContent = document.querySelector('.main-content-wrapper');
        if (!mainContent) return;

        const isCollapsed = body.classList.contains('sidebar-collapsed');
        const sidebarWidth = isCollapsed ?
            getComputedStyle(document.documentElement).getPropertyValue('--sidebar-collapsed-width') :
            getComputedStyle(document.documentElement).getPropertyValue('--sidebar-width');

        // تعيين هوامش المحتوى بناءً على اتجاه اللغة وحالة الشريط الجانبي
        if (window.innerWidth > 992) {
            if (isRTL) {
                mainContent.style.marginRight = sidebarWidth;
                mainContent.style.marginLeft = '0';
            } else {
                mainContent.style.marginLeft = sidebarWidth;
                mainContent.style.marginRight = '0';
            }
        } else {
            mainContent.style.marginLeft = '0';
            mainContent.style.marginRight = '0';
        }
    };

    // إضافة تأثيرات مرئية للشريط الجانبي
    const enhanceSidebarVisuals = () => {
        // إضافة تأثير عند التمرير على عناصر القائمة
        const menuLinks = document.querySelectorAll('.menu-item > a, .submenu li a');
        menuLinks.forEach(link => {
            link.addEventListener('mouseenter', function() {
                this.style.transition = 'all 0.3s ease';
                this.style.transform = 'translateX(' + (isRTL ? '-3px' : '3px') + ')';
            });

            link.addEventListener('mouseleave', function() {
                this.style.transform = 'translateX(0)';
            });
        });

        // معالجة اللوجو في الشريط الجانبي
        setupLogo();
    };

    // ضبط اللوجو وتنسيقه
    const setupLogo = () => {
        const logoElement = document.querySelector('.logo-container .logo');
        if (!logoElement) return;

        logoElement.addEventListener('load', function() {
            // قياس نسبة العرض إلى الارتفاع للوجو
            const aspectRatio = this.naturalWidth / this.naturalHeight;

            // ضبط حجم اللوجو بناءً على شكله
            if (aspectRatio > 2.5) { // اللوجو عريض/أفقي
                this.style.maxWidth = '85%';
                this.style.maxHeight = '35px';
            } else if (aspectRatio >= 0.8 && aspectRatio <= 1.2) { // اللوجو مربع تقريبًا
                this.style.maxHeight = '40px';
                this.style.maxWidth = '40px';
            } else if (aspectRatio < 0.8) { // اللوجو عمودي
                this.style.maxHeight = '40px';
                this.style.width = 'auto';
            }
        });

        // تنفيذ الوظيفة إذا كان اللوجو محملاً بالفعل
        if (logoElement.complete) {
            logoElement.dispatchEvent(new Event('load'));
        }
    };

    /**
     * ===== وظائف القائمة =====
     */

    // تبديل القوائم الفرعية
    menuItems.forEach(function(item) {
        item.addEventListener('click', function(e) {
            const parent = this.parentElement;

            // تحقق مما إذا كانت القائمة تحتوي على قوائم فرعية
            const hasSubmenu = parent.querySelector('.submenu');
            if (hasSubmenu) {
                e.preventDefault();

                // إضافة أو إزالة الفئة "نشط"
                const wasActive = parent.classList.contains('active');

                // إغلاق جميع القوائم المفتوحة الأخرى (سلوك الأكورديون)
                if (!wasActive && !e.ctrlKey) { // اضغط على مفتاح Ctrl للسماح بفتح عدة قوائم
                    document.querySelectorAll('.menu-item.active').forEach(function(activeItem) {
                        if (activeItem !== parent && !activeItem.contains(parent) && !parent.contains(activeItem)) {
                            activeItem.classList.remove('active');
                        }
                    });
                }

                // تبديل حالة النشاط
                parent.classList.toggle('active');

                // تأثير الانتقال السلس
                const submenu = hasSubmenu;
                if (submenu) {
                    if (parent.classList.contains('active')) {
                        const height = submenu.scrollHeight;
                        submenu.style.maxHeight = height + 'px';
                    } else {
                        submenu.style.maxHeight = '0';
                    }
                }
            }
        });
    });

    // فتح القائمة النشطة تلقائيًا
    const initializeActiveMenus = () => {
        // البحث عن العناصر النشطة في الصفحة الحالية
        const currentPath = window.location.pathname;
        const menuLinks = document.querySelectorAll('.menu-item > a, .submenu li a');

        let activeItemFound = false;

        menuLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && (currentPath === href || currentPath.startsWith(href))) {
                // تمييز الرابط كنشط
                link.classList.add('active');

                // تمييز العنصر الأب كنشط
                let parentLi = link.closest('li');
                if (parentLi) {
                    parentLi.classList.add('active');

                    // إذا كان داخل قائمة فرعية، افتح القائمة الرئيسية
                    const parentSubmenu = parentLi.closest('.submenu');
                    if (parentSubmenu) {
                        const parentMenuItem = parentSubmenu.closest('.menu-item');
                        if (parentMenuItem) {
                            parentMenuItem.classList.add('active');
                            parentSubmenu.style.maxHeight = parentSubmenu.scrollHeight + 'px';
                        }
                    }
                }

                activeItemFound = true;
            }
        });

        // إذا لم يتم العثور على عنصر نشط، افتح لوحة التحكم الرئيسية بشكل افتراضي
        if (!activeItemFound) {
            const dashboardLink = document.querySelector('.menu-item > a[href*="dashboard_home"]');
            if (dashboardLink) {
                dashboardLink.classList.add('active');
                dashboardLink.closest('li').classList.add('active');
            }
        }
    };

    /**
     * ===== وظائف الإشعارات =====
     */

    // تحديث الإشعارات وإدارتها
    const initializeNotifications = () => {
        // تحديد جميع الإشعارات كمقروءة
        const markAllReadBtn = document.querySelector('.mark-all-read');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', function(e) {
                e.preventDefault();

                // إرسال طلب AJAX لتحديث حالة الإشعارات
                $.ajax({
                    url: '/dashboard/notifications/mark-all-read/',
                    type: 'POST',
                    success: function(response) {
                        if (response.success) {
                            // إزالة فئة "unread" من جميع الإشعارات
                            document.querySelectorAll('.notification-item.unread').forEach(function(item) {
                                item.classList.remove('unread');
                            });

                            // تحديث عدد الإشعارات غير المقروءة
                            const badge = document.querySelector('.notification-badge');
                            if (badge) {
                                badge.style.display = 'none';
                            }

                            // إظهار رسالة نجاح
                            showToast('تم تحديد جميع الإشعارات كمقروءة', 'success');
                        }
                    }
                });
            });
        }

        // تحديث عداد الإشعارات
        updateNotificationsCount();
    };

    // تحديث عدد الإشعارات
    const updateNotificationsCount = () => {
        const unreadNotifications = document.querySelectorAll('.notification-item.unread');
        const badge = document.querySelector('.notification-badge');

        if (badge) {
            if (unreadNotifications.length > 0) {
                badge.textContent = unreadNotifications.length;
                badge.style.display = 'block';
            } else {
                badge.style.display = 'none';
            }
        }
    };

    /**
     * ===== وظائف عامة =====
     */

    // تهيئة التلميحات (tooltips)
    const initializeTooltips = () => {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    };

    // تهيئة النوافذ المنبثقة (popovers)
    const initializePopovers = () => {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        const popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    };

    // إظهار إشعار توست
    const showToast = (message, type = 'info') => {
        // إنشاء عنصر توست
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        // إنشاء محتوى التوست
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        // إضافة التوست إلى الصفحة
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            // إنشاء حاوية للتوست إذا لم تكن موجودة
            const container = document.createElement('div');
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(container);
            container.appendChild(toast);
        } else {
            toastContainer.appendChild(toast);
        }

        // إظهار التوست
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 3000
        });
        bsToast.show();
    };

    // إخفاء تنبيهات النظام تلقائيًا
    const autoHideAlerts = () => {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            setTimeout(function() {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    };

    /**
     * ===== تهيئة جداول البيانات =====
     */
    const initializeDataTables = () => {
        const dataTables = document.querySelectorAll('.data-table');
        if (dataTables.length > 0 && typeof $.fn.DataTable !== 'undefined') {
            dataTables.forEach(function(table) {
                const tableId = table.id;
                if (tableId && !$.fn.DataTable.isDataTable(`#${tableId}`)) {
                    // تهيئة الجدول مع الإعدادات المخصصة
                    $(`#${tableId}`).DataTable({
                        language: {
                            url: document.documentElement.lang === 'ar' ?
                                '//cdn.datatables.net/plug-ins/1.10.25/i18n/Arabic.json' :
                                '//cdn.datatables.net/plug-ins/1.10.25/i18n/English.json'
                        },
                        responsive: true,
                        stateSave: true,
                        pageLength: 25,
                        dom: '<"datatable-header"fl><"datatable-scroll"t><"datatable-footer"ip>',
                        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "الكل"]],
                        initComplete: function() {
                            // إضافة فئات Bootstrap للعناصر
                            const wrapper = $(this).closest('.dataTables_wrapper');
                            wrapper.find('.dataTables_length select').addClass('form-select form-select-sm');
                            wrapper.find('.dataTables_filter input').addClass('form-control form-control-sm');
                            wrapper.find('.dataTables_filter input').attr('placeholder', 'بحث...');
                        }
                    });
                }
            });
        }
    };

    /**
     * ===== وظائف التحميل المتكاسل للصور =====
     */
    const initializeLazyLoading = () => {
        if ('IntersectionObserver' in window) {
            const lazyImages = document.querySelectorAll('.lazy-load');

            const imageObserver = new IntersectionObserver(function(entries, observer) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        const image = entry.target;
                        const dataSrc = image.getAttribute('data-src');

                        if (dataSrc) {
                            image.src = dataSrc;
                            image.classList.remove('lazy-load');
                            image.removeAttribute('data-src');

                            // إضافة تأثير ظهور تدريجي
                            image.style.opacity = '0';
                            setTimeout(() => {
                                image.style.transition = 'opacity 0.5s ease';
                                image.style.opacity = '1';
                            }, 10);
                        }

                        imageObserver.unobserve(image);
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.01
            });

            lazyImages.forEach(function(image) {
                imageObserver.observe(image);
            });
        } else {
            // Fallback لمتصفحات قديمة
            const lazyImages = document.querySelectorAll('.lazy-load');
            lazyImages.forEach(function(image) {
                const dataSrc = image.getAttribute('data-src');
                if (dataSrc) {
                    image.src = dataSrc;
                    image.classList.remove('lazy-load');
                    image.removeAttribute('data-src');
                }
            });
        }
    };

    /**
     * ===== تهيئة المخططات =====
     */
    const initializeCharts = () => {
        // تكوين عام للمخططات
        if (typeof Chart !== 'undefined') {
            Chart.defaults.font.family = document.documentElement.lang === 'ar' ?
                "'Cairo', 'Tajawal', sans-serif" :
                "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif";

            Chart.defaults.color = '#4a5568';
            Chart.defaults.scale.grid.color = 'rgba(0,0,0,0.05)';
            Chart.defaults.plugins.tooltip.titleFont.weight = 'bold';
            Chart.defaults.plugins.tooltip.bodyFont.size = 13;
            Chart.defaults.plugins.tooltip.padding = 10;
            Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(0,0,0,0.7)';
            Chart.defaults.plugins.tooltip.borderColor = 'rgba(0,0,0,0.1)';
            Chart.defaults.plugins.tooltip.borderWidth = 1;
            Chart.defaults.plugins.tooltip.displayColors = true;
            Chart.defaults.plugins.tooltip.boxWidth = 10;
            Chart.defaults.plugins.tooltip.boxHeight = 10;
            Chart.defaults.plugins.tooltip.boxPadding = 3;
            Chart.defaults.plugins.legend.position = 'top';
            Chart.defaults.plugins.legend.align = 'center';
            Chart.defaults.plugins.legend.labels.padding = 15;
            Chart.defaults.plugins.legend.labels.boxWidth = 12;
            Chart.defaults.plugins.legend.labels.font = {
                family: document.documentElement.lang === 'ar' ?
                    "'Cairo', 'Tajawal', sans-serif" :
                    "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
                size: 13,
                weight: 'normal'
            };
        }
    };

    /**
     * ===== وظائف التمرير السلس =====
     */
    const initializeSmoothScroll = () => {
        const smoothScrollLinks = document.querySelectorAll('a.smooth-scroll');
        smoothScrollLinks.forEach(function(link) {
            link.addEventListener('click', function(e) {
                e.preventDefault();

                const targetId = this.getAttribute('href');
                if (targetId && targetId.startsWith('#')) {
                    const targetElement = document.querySelector(targetId);
                    if (targetElement) {
                        const headerOffset = 70; // ارتفاع الهيدر
                        const elementPosition = targetElement.getBoundingClientRect().top;
                        const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                        window.scrollTo({
                            top: offsetPosition,
                            behavior: 'smooth'
                        });
                    }
                }
            });
        });
    };

    /**
     * ===== تنفيذ التهيئة =====
     */
    // تهيئة الشريط الجانبي
    initializeSidebar();

    // تهيئة القوائم النشطة
    initializeActiveMenus();

    // تهيئة الإشعارات
    initializeNotifications();

    // تهيئة التلميحات والنوافذ المنبثقة
    initializeTooltips();
    initializePopovers();

    // إخفاء التنبيهات تلقائيًا
    autoHideAlerts();

    // تهيئة جداول البيانات إذا كانت متاحة
    if (typeof $.fn.DataTable !== 'undefined') {
        initializeDataTables();
    }

    // تهيئة التحميل المتكاسل للصور
    initializeLazyLoading();

    // تهيئة المخططات إذا كانت متاحة
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }

    // تهيئة التمرير السلس
    initializeSmoothScroll();

    // إعادة ضبط المحتوى عند تغيير حجم النافذة
    window.addEventListener('resize', function() {
        adjustMainContentForSidebar();
    });

    // الاستجابة للتغييرات في الاتجاه (RTL/LTR)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'dir' || mutation.attributeName === 'lang') {
                // تحديث المتغيرات
                isRTL = document.documentElement.lang === 'ar' || document.documentElement.dir === 'rtl';

                // إعادة ضبط التخطيط
                adjustMainContentForSidebar();
            }
        });
    });

    observer.observe(document.documentElement, { attributes: true });
});

/**
 * وظائف مساعدة عامة للاستخدام في مختلف أجزاء التطبيق
 */

// تنسيق الأرقام
function formatNumber(number, decimals = 2, decimalSeparator = '.', thousandsSeparator = ',') {
    return number.toFixed(decimals)
        .replace('.', decimalSeparator)
        .replace(/\B(?=(\d{3})+(?!\d))/g, thousandsSeparator);
}

// تنسيق العملة
function formatCurrency(amount, currencySymbol = 'ر.س', position = 'after') {
    const formattedAmount = formatNumber(amount);
    return position === 'after' ?
        `${formattedAmount} ${currencySymbol}` :
        `${currencySymbol} ${formattedAmount}`;
}

// التحقق من صحة البريد الإلكتروني
function validateEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

// التحقق من صحة رقم الهاتف
function validatePhone(phone) {
    // تحقق من أرقام الهاتف المحلية (السعودية) والدولية
    const re = /^(\+?966|0)?5\d{8}$/;
    return re.test(String(phone).trim());
}

// الحصول على معلمات الاستعلام من عنوان URL
function getQueryParams() {
    const params = {};
    window.location.search.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(str, key, value) {
        params[key] = decodeURIComponent(value);
    });
    return params;
}