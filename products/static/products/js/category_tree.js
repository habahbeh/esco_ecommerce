document.addEventListener('DOMContentLoaded', function() {
    initCategoryToggle();
    applyCategoryIcons();
    activateCategoryPath();
});

var CATEGORY_ICON_MAP = {
    375: 'fas fa-faucet',
    3:   'fas fa-wind',
    6:   'fas fa-ring',
    14:  'fas fa-o',
    47:  'fas fa-industry',
    1:   'fas fa-wrench',
    7:   'fas fa-tachometer-alt',
    10:  'fas fa-hard-hat',
    12:  'fas fa-scroll',
    5:   'fas fa-grip-lines',
    16:  'fas fa-dolly',
    48:  'fas fa-water',
    46:  'fas fa-magnet',
    24:  'fas fa-tape',
    17:  'fas fa-cogs',
    26:  'fas fa-paint-roller',
    21:  'fas fa-fire',
    19:  'fas fa-pen-ruler',
    255: 'fas fa-spray-can',
    13:  'fas fa-bolt',
    18:  'fas fa-screwdriver',
};

var KEYWORD_ICON_MAP = [
    { kw: ['drill', 'درل', 'ثقب'],           icon: 'fas fa-compact-disc' },
    { kw: ['saw', 'منشار', 'قص'],            icon: 'fas fa-cut' },
    { kw: ['pump', 'مضخ', 'طلمب'],           icon: 'fas fa-water' },
    { kw: ['valve', 'صمام', 'محبس'],         icon: 'fas fa-valve' },
    { kw: ['pipe', 'بربيش', 'خرطوم', 'ماسورة'], icon: 'fas fa-grip-lines' },
    { kw: ['wire', 'سلك', 'كيبل'],           icon: 'fas fa-ethernet' },
    { kw: ['tape', 'لاصق', 'تيب', 'شريط'],   icon: 'fas fa-tape' },
    { kw: ['lock', 'قفل'],                   icon: 'fas fa-lock' },
    { kw: ['light', 'إضاء', 'اضاء', 'لمبة'], icon: 'fas fa-lightbulb' },
    { kw: ['motor', 'موتور', 'محرك'],        icon: 'fas fa-fan' },
    { kw: ['wheel', 'عجل', 'دولاب'],         icon: 'fas fa-circle-notch' },
    { kw: ['brush', 'فرشا'],                 icon: 'fas fa-paint-brush' },
    { kw: ['glove', 'قفاز', 'كف'],           icon: 'fas fa-mitten' },
    { kw: ['glass', 'نظار'],                 icon: 'fas fa-glasses' },
    { kw: ['helmet', 'خوذ'],                 icon: 'fas fa-hard-hat' },
    { kw: ['gauge', 'ساعة', 'مقياس'],        icon: 'fas fa-tachometer-alt' },
    { kw: ['bearing', 'بلي', 'رولمان'],      icon: 'fas fa-circle' },
    { kw: ['chain', 'سلسل', 'جنزير'],        icon: 'fas fa-link' },
    { kw: ['spray', 'بخاخ', 'رش'],           icon: 'fas fa-spray-can' },
    { kw: ['key', 'مفتاح', 'مفك'],           icon: 'fas fa-key' },
    { kw: ['hammer', 'مطرق', 'شاكوش'],       icon: 'fas fa-hammer' },
    { kw: ['measure', 'قياس', 'متر', 'ميزان'], icon: 'fas fa-ruler' },
    { kw: ['clamp', 'مشبك', 'كلامب'],        icon: 'fas fa-compress-alt' },
    { kw: ['weld', 'لحام', 'لحم'],           icon: 'fas fa-fire' },
    { kw: ['screw', 'براغي', 'مسمار', 'صمولة'], icon: 'fas fa-screwdriver' },
    { kw: ['paint', 'دهان', 'طلاء'],         icon: 'fas fa-fill-drip' },
    { kw: ['seal', 'اورنج', 'حلق'],          icon: 'fas fa-ring' },
    { kw: ['hose', 'هوز'],                   icon: 'fas fa-grip-lines' },
    { kw: ['nozzle', 'بشبوري', 'فوهة'],      icon: 'fas fa-pen-nib' },
    { kw: ['filter', 'فلتر'],                icon: 'fas fa-filter' },
    { kw: ['jack', 'جك', 'رافع'],            icon: 'fas fa-arrows-alt-v' },
];

function getIconClass(catId, catName) {
    if (CATEGORY_ICON_MAP[catId]) return CATEGORY_ICON_MAP[catId];

    var nameLower = (catName || '').toLowerCase();
    for (var i = 0; i < KEYWORD_ICON_MAP.length; i++) {
        var entry = KEYWORD_ICON_MAP[i];
        for (var j = 0; j < entry.kw.length; j++) {
            if (nameLower.indexOf(entry.kw[j].toLowerCase()) !== -1) {
                return entry.icon;
            }
        }
    }
    return 'fas fa-folder';
}

function generateSectionColor(index) {
    var hue = (index * 137.508) % 360;
    return {
        bg: 'hsl(' + hue + ', 78%, 93%)',
        color: 'hsl(' + hue + ', 55%, 33%)',
        line: 'hsl(' + hue + ', 40%, 82%)'
    };
}

function getNameFromIcon(iconEl) {
    var linkBtn = iconEl.closest('.category-link-btn');
    if (linkBtn) {
        var nameSpan = linkBtn.querySelector('.category-name');
        if (nameSpan) return nameSpan.textContent.trim();
    }
    return '';
}

// Custom collapse toggle - no Bootstrap dependency
function initCategoryToggle() {
    document.addEventListener('click', function(e) {
        var btn = e.target.closest('button[data-collapse-target]');
        if (!btn) return;

        var targetSelector = btn.getAttribute('data-collapse-target');
        var target = document.querySelector(targetSelector);
        if (!target) return;

        var icon = btn.querySelector('.expand-icon i');
        if (target.classList.contains('show')) {
            target.classList.remove('show');
            btn.classList.add('collapsed');
            btn.setAttribute('aria-expanded', 'false');
            if (icon) icon.className = 'fas fa-plus';
        } else {
            target.classList.add('show');
            btn.classList.remove('collapsed');
            btn.setAttribute('aria-expanded', 'true');
            if (icon) icon.className = 'fas fa-minus';
        }
    });
}

function applyCategoryIcons() {
    var accordion = document.getElementById('categoryAccordion');
    if (!accordion) return;

    var topItems = [];
    var children = accordion.children;
    for (var i = 0; i < children.length; i++) {
        if (children[i].classList.contains('category-item')) {
            topItems.push(children[i]);
        }
    }

    for (var idx = 0; idx < topItems.length; idx++) {
        var item = topItems[idx];
        var section = generateSectionColor(idx);

        var header = null;
        var itemChildren = item.children;
        for (var c = 0; c < itemChildren.length; c++) {
            if (itemChildren[c].tagName === 'H2' || itemChildren[c].classList.contains('accordion-header')) {
                header = itemChildren[c];
                break;
            }
        }

        if (header) {
            var catIcon = header.querySelector('.cat-icon[data-cat-id]');
            if (catIcon) {
                var catId = parseInt(catIcon.getAttribute('data-cat-id'));
                var catName = getNameFromIcon(catIcon);
                catIcon.style.background = section.bg;
                catIcon.style.color = section.color;
                var iconEl = catIcon.querySelector('i');
                if (iconEl) iconEl.className = getIconClass(catId, catName);
            }
        }

        var subIcons = item.querySelectorAll('.subcategory-accordion .cat-icon[data-cat-id]');
        for (var s = 0; s < subIcons.length; s++) {
            var el = subIcons[s];
            var subId = parseInt(el.getAttribute('data-cat-id'));
            var subName = getNameFromIcon(el);
            el.style.background = section.bg;
            el.style.color = section.color;
            var ic = el.querySelector('i');
            if (ic) ic.className = getIconClass(subId, subName);
        }

        var leafIcons = item.querySelectorAll('.leaf-icon[data-cat-id]');
        for (var l = 0; l < leafIcons.length; l++) {
            leafIcons[l].style.color = section.color;
            leafIcons[l].style.background = section.bg;
        }

        var subAccordions = item.querySelectorAll('.subcategory-accordion');
        for (var a = 0; a < subAccordions.length; a++) {
            subAccordions[a].style.setProperty('--tree-line-color', section.line);
        }
    }
}

function activateCategoryPath() {
    var currentCategoryPath = window.currentCategoryPath || [];
    if (!currentCategoryPath.length) return;

    for (var p = 0; p < currentCategoryPath.length; p++) {
        var categoryId = currentCategoryPath[p];
        var categoryItem = document.querySelector('.category-item[data-category-id="' + categoryId + '"]');
        if (!categoryItem) continue;

        // Mark leaf link as active
        var simpleLink = categoryItem.querySelector('.category-link');
        if (simpleLink) {
            simpleLink.classList.add('active');
        }

        // Expand this item if it has children
        var btn = categoryItem.querySelector('button[data-collapse-target]');
        var collapse = categoryItem.querySelector('.category-collapse');
        if (btn && collapse) {
            btn.classList.remove('collapsed');
            btn.setAttribute('aria-expanded', 'true');
            collapse.classList.add('show');
            var icon = btn.querySelector('.expand-icon i');
            if (icon) icon.className = 'fas fa-minus';
        }

        // Open ALL parent collapses up the tree
        var el = categoryItem;
        while (el) {
            var parentCollapse = el.parentElement ? el.parentElement.closest('.category-collapse') : null;
            if (!parentCollapse) break;
            parentCollapse.classList.add('show');
            var parentBtn = document.querySelector('[data-collapse-target="#' + parentCollapse.id + '"]');
            if (parentBtn) {
                parentBtn.classList.remove('collapsed');
                parentBtn.setAttribute('aria-expanded', 'true');
                var pIcon = parentBtn.querySelector('.expand-icon i');
                if (pIcon) pIcon.className = 'fas fa-minus';
            }
            el = parentCollapse;
        }
    }

    // Scroll the active item into view within the sidebar
    var activeLink = document.querySelector('.category-link.active');
    if (activeLink) {
        var sidebar = activeLink.closest('.category-sidebar');
        if (sidebar) {
            setTimeout(function() {
                activeLink.scrollIntoView({ block: 'center', behavior: 'smooth' });
            }, 100);
        }
    }
}
