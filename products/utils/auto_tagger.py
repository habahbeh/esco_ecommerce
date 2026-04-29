import re
from collections import Counter
from django.utils.html import strip_tags

ARABIC_STOP_WORDS = {
    'في', 'من', 'على', 'إلى', 'عن', 'مع', 'هذا', 'هذه', 'ذلك', 'تلك',
    'التي', 'الذي', 'الذين', 'اللتان', 'اللذان', 'هو', 'هي', 'هم', 'هن',
    'أنا', 'نحن', 'أنت', 'أنتم', 'كان', 'كانت', 'يكون', 'تكون', 'لا', 'لم',
    'لن', 'قد', 'ما', 'ذو', 'ذات', 'كل', 'بعض', 'أي', 'غير', 'بين',
    'حتى', 'عند', 'لدى', 'منذ', 'خلال', 'بعد', 'قبل', 'فوق', 'تحت',
    'أو', 'ثم', 'لكن', 'بل', 'إن', 'أن', 'إذا', 'لأن', 'حيث', 'كما',
    'أيضا', 'جدا', 'فقط', 'أكثر', 'أقل', 'يتم', 'يمكن', 'عبر', 'ضمن',
    'حول', 'دون', 'ليس', 'ليست', 'واحد', 'اثنان', 'ثلاثة', 'وهو', 'وهي',
    'الى', 'او', 'لانه', 'لان', 'ان', 'عليه', 'عليها',
}

ENGLISH_STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'shall', 'can', 'need', 'dare',
    'this', 'that', 'these', 'those', 'it', 'its', 'he', 'she', 'they',
    'we', 'you', 'i', 'my', 'your', 'his', 'her', 'our', 'their',
    'not', 'no', 'nor', 'as', 'if', 'than', 'too', 'very', 'just',
    'about', 'above', 'after', 'again', 'all', 'also', 'any', 'each',
    'every', 'into', 'more', 'most', 'other', 'some', 'such', 'up', 'out',
}

INDUSTRY_TERMS_AR = {
    'ستانلس': 'ستانلس ستيل',
    'ستيل': 'ستانلس ستيل',
    'بي في سي': 'PVC',
    'هيدروليك': 'هيدروليك',
    'نيوماتيك': 'نيوماتيك',
    'كهربائي': 'كهربائي',
    'صناعي': 'صناعي',
}


def extract_keywords(text, max_keywords=15):
    if not text:
        return []

    text = strip_tags(text)
    text = re.sub(r'[^\w\s؀-ۿ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    words = text.split()

    filtered = []
    for word in words:
        word_lower = word.lower()
        if len(word) < 2:
            continue
        if word in ARABIC_STOP_WORDS or word_lower in ARABIC_STOP_WORDS or word_lower in ENGLISH_STOP_WORDS:
            continue
        if word.isdigit():
            continue
        filtered.append(word_lower)

    word_counts = Counter(filtered)

    bigrams = []
    for i in range(len(filtered) - 1):
        bigram = f"{filtered[i]} {filtered[i+1]}"
        bigrams.append(bigram)
    bigram_counts = Counter(bigrams)

    scored = {}
    for word, count in word_counts.items():
        if count >= 2 or len(word) > 4:
            scored[word] = count * (1 + len(word) * 0.1)

    for bigram, count in bigram_counts.items():
        if count >= 2:
            scored[bigram] = count * 3

    sorted_keywords = sorted(scored.items(), key=lambda x: x[1], reverse=True)
    return [kw for kw, score in sorted_keywords[:max_keywords]]


def _build_meta_title(product):
    parts = []
    if product.name:
        parts.append(product.name)
    if product.brand:
        brand = product.brand.name
        if brand.lower() not in (product.name or '').lower():
            parts.append(brand)
    if product.category:
        cat = product.category.name
        if cat.lower() not in (product.name or '').lower():
            parts.append(cat)
    title = ' - '.join(parts)
    if len(title) > 190:
        title = title[:190].rsplit(' ', 1)[0]
    return title


def _build_meta_description(product):
    if product.short_description:
        desc = strip_tags(product.short_description).strip()
        if len(desc) >= 20:
            return desc[:160].rsplit(' ', 1)[0] if len(desc) > 160 else desc

    if product.description:
        desc = strip_tags(product.description).strip()
        desc = re.sub(r'\s+', ' ', desc)
        if len(desc) >= 20:
            return desc[:160].rsplit(' ', 1)[0] if len(desc) > 160 else desc

    parts = []
    if product.name:
        parts.append(product.name)
    if product.brand:
        parts.append(product.brand.name)
    if product.category:
        parts.append(product.category.name)
    parts.append('ESCO Jordan')
    return ' | '.join(parts)


def auto_tag_product(product, save=True):
    parts = []
    if product.name:
        parts.append(product.name)
    if product.name_en:
        parts.append(product.name_en)
    if product.description:
        parts.append(strip_tags(product.description))
    if product.short_description:
        parts.append(strip_tags(product.short_description))
    if hasattr(product, 'description_en') and product.description_en:
        parts.append(strip_tags(product.description_en))

    combined_text = ' '.join(parts)
    keywords = extract_keywords(combined_text, max_keywords=15)

    if product.category:
        cat_name = product.category.name.lower()
        if cat_name not in keywords:
            keywords.insert(0, cat_name)
    if product.brand:
        brand_name = product.brand.name.lower()
        if brand_name not in keywords:
            keywords.insert(0, brand_name)

    keywords = keywords[:15]

    if keywords:
        product.meta_keywords = ', '.join(keywords)
        product.search_keywords = ' '.join(keywords)

    product.meta_title = _build_meta_title(product)
    product.meta_description = _build_meta_description(product)

    if save:
        product.save(update_fields=[
            'meta_keywords', 'search_keywords',
            'meta_title', 'meta_description',
        ])

    return keywords
