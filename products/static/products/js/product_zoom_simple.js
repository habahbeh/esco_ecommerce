/**
 * حل مباشر لمشكلة عدم ظهور مربع التكبير
 * قم بنسخ هذا الكود في ملف product_zoom_fix.js
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("تهيئة نظام التكبير مع التركيز على إظهار مربع التكبير");

    // الحصول على حاوية الصورة والصورة نفسها
    const container = document.querySelector('.main-image-container');
    const mainImage = document.querySelector('.main-image-container img');

    if (!container || !mainImage) {
        console.error("لم يتم العثور على عناصر التكبير");
        return;
    }

    // ضبط أنماط الحاوية والصورة
    container.style.position = 'relative';
    container.style.overflow = 'hidden';
    container.style.height = '500px';
    container.style.border = '1px solid #eee';
    container.style.borderRadius = '8px';
    container.style.cursor = 'zoom-in';

    mainImage.style.width = '100%';
    mainImage.style.height = '100%';
    mainImage.style.objectFit = 'contain';

    // إنشاء عدسة التكبير
    const zoomLens = document.createElement('div');
    zoomLens.classList.add('zoom-lens');
    zoomLens.style.position = 'absolute';
    zoomLens.style.width = '100px';
    zoomLens.style.height = '100px';
    zoomLens.style.border = '2px solid #3498db';
    zoomLens.style.borderRadius = '50%';
    zoomLens.style.display = 'none';
    zoomLens.style.pointerEvents = 'none';
    zoomLens.style.backgroundColor = 'rgba(255, 255, 255, 0.3)';
    zoomLens.style.zIndex = '50';

    // إنشاء مربع التكبير (نافذة النتيجة) - بتحسينات خاصة لضمان الظهور
    const zoomBox = document.createElement('div');
    zoomBox.classList.add('zoom-result');

    // أنماط أساسية لمربع التكبير
    zoomBox.style.position = 'absolute';
    zoomBox.style.width = '300px';
    zoomBox.style.height = '300px';
    zoomBox.style.border = '3px solid #3498db';
    zoomBox.style.backgroundColor = 'white';
    zoomBox.style.zIndex = '1000';
    zoomBox.style.overflow = 'hidden';
    zoomBox.style.display = 'none';
    zoomBox.style.boxShadow = '0 0 15px rgba(0, 0, 0, 0.3)';

    // تحديد موضع مربع التكبير - داخل الحاوية في الزاوية اليمنى
    zoomBox.style.top = '10px';
    zoomBox.style.right = '10px';

    // إضافة هامش أمان للتأكد من عدم خروج المربع عن حدود الشاشة
    if (window.innerWidth < 768) {
        // للشاشات الصغيرة، ضع المربع أسفل الصورة
        zoomBox.style.top = 'auto';
        zoomBox.style.bottom = '-320px';
        zoomBox.style.right = '0';
        zoomBox.style.left = '0';
        zoomBox.style.margin = '0 auto';
    }

    // صورة النتيجة داخل مربع التكبير
    const resultImage = new Image();
    resultImage.src = mainImage.src;
    resultImage.style.position = 'absolute';
    resultImage.style.maxWidth = 'none';
    zoomBox.appendChild(resultImage);

    // إضافة رسالة توضيحية لمربع التكبير
    const zoomMessage = document.createElement('div');
    zoomMessage.textContent = 'منطقة التكبير';
    zoomMessage.style.position = 'absolute';
    zoomMessage.style.bottom = '5px';
    zoomMessage.style.right = '5px';
    zoomMessage.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    zoomMessage.style.color = 'white';
    zoomMessage.style.padding = '3px 8px';
    zoomMessage.style.fontSize = '11px';
    zoomMessage.style.borderRadius = '3px';
    zoomMessage.style.zIndex = '1001';
    zoomBox.appendChild(zoomMessage);

    // إضافة عدسة التكبير ومربع التكبير إلى الحاوية
    container.appendChild(zoomLens);
    container.appendChild(zoomBox);

    // مؤشرات لحالة التكبير
    let isZooming = false;
    let imgRect;
    const zoomLevel = 3;

    // بدء عملية التكبير
    function startZoom() {
        console.log("بدء التكبير - يجب أن يظهر مربع التكبير");
        imgRect = mainImage.getBoundingClientRect();
        isZooming = true;

        // تحديث صورة النتيجة
        resultImage.src = mainImage.src;

        // إظهار عدسة التكبير ومربع التكبير بوضوح
        zoomLens.style.display = 'block';
        zoomBox.style.display = 'block';

        // إضافة إطار واضح للحاوية لتأكيد نشاط التكبير
        container.style.border = '1px solid #3498db';


    }

    // إيقاف عملية التكبير
    function stopZoom() {
        console.log("إيقاف التكبير");
        isZooming = false;
        zoomLens.style.display = 'none';
        zoomBox.style.display = 'none';
        container.style.border = '1px solid #eee';
    }

    // تحريك العدسة وتحديث الصورة المكبرة
    function moveZoom(e) {
        if (!isZooming) return;

        // منع السلوك الافتراضي
        e.preventDefault();

        // الحصول على موضع المؤشر
        const mouseX = e.clientX;
        const mouseY = e.clientY;

        // حساب موضع المؤشر بالنسبة للصورة
        const {left, top, width, height} = imgRect;
        let posX = mouseX - left;
        let posY = mouseY - top;

        // التأكد من أن المؤشر داخل الصورة
        if (posX < 0) posX = 0;
        if (posY < 0) posY = 0;
        if (posX > width) posX = width;
        if (posY > height) posY = height;

        // موضع العدسة
        const lensWidth = zoomLens.offsetWidth;
        const lensHeight = zoomLens.offsetHeight;
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

        // حساب نسب المؤشر
        const mouseXPercent = posX / width;
        const mouseYPercent = posY / height;

        // أبعاد الصورة المكبرة
        const zoomedWidth = width * zoomLevel;
        const zoomedHeight = height * zoomLevel;

        // موضع الصورة المكبرة
        const resultX = mouseXPercent * (zoomedWidth - zoomBox.offsetWidth);
        const resultY = mouseYPercent * (zoomedHeight - zoomBox.offsetHeight);

        // تحديث حجم وموضع الصورة المكبرة
        resultImage.style.width = `${zoomedWidth}px`;
        resultImage.style.height = `${zoomedHeight}px`;
        resultImage.style.left = `${-resultX}px`;
        resultImage.style.top = `${-resultY}px`;
    }

    // إضافة الأحداث
    container.addEventListener('mouseenter', startZoom);
    container.addEventListener('mouseleave', stopZoom);
    container.addEventListener('mousemove', moveZoom);

    // إضافة زر اختبار مربع التكبير

});