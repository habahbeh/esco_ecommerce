"""Country lookup: English GeoIP name -> Arabic name + flag emoji + ISO code.

Flag emojis use Unicode regional indicator pairs derived from the ISO 3166-1
alpha-2 code. Browsers render them as country flags on most platforms.
"""

# (Arabic name, ISO alpha-2 code)
_COUNTRY_AR = {
    # Arab League
    "Jordan": ("الأردن", "JO"),
    "Hashemite Kingdom of Jordan": ("الأردن", "JO"),
    "Saudi Arabia": ("السعودية", "SA"),
    "United Arab Emirates": ("الإمارات", "AE"),
    "Kuwait": ("الكويت", "KW"),
    "Qatar": ("قطر", "QA"),
    "Bahrain": ("البحرين", "BH"),
    "Oman": ("عُمان", "OM"),
    "Yemen": ("اليمن", "YE"),
    "Iraq": ("العراق", "IQ"),
    "Syria": ("سوريا", "SY"),
    "Lebanon": ("لبنان", "LB"),
    "Palestine": ("فلسطين", "PS"),
    "State of Palestine": ("فلسطين", "PS"),
    "Egypt": ("مصر", "EG"),
    "Libya": ("ليبيا", "LY"),
    "Tunisia": ("تونس", "TN"),
    "Algeria": ("الجزائر", "DZ"),
    "Morocco": ("المغرب", "MA"),
    "Mauritania": ("موريتانيا", "MR"),
    "Sudan": ("السودان", "SD"),
    "Somalia": ("الصومال", "SO"),
    "Djibouti": ("جيبوتي", "DJ"),
    "Comoros": ("جزر القمر", "KM"),

    # Major economies
    "United States": ("الولايات المتحدة", "US"),
    "United Kingdom": ("المملكة المتحدة", "GB"),
    "Germany": ("ألمانيا", "DE"),
    "France": ("فرنسا", "FR"),
    "Italy": ("إيطاليا", "IT"),
    "Spain": ("إسبانيا", "ES"),
    "Portugal": ("البرتغال", "PT"),
    "Netherlands": ("هولندا", "NL"),
    "Belgium": ("بلجيكا", "BE"),
    "Switzerland": ("سويسرا", "CH"),
    "Austria": ("النمسا", "AT"),
    "Sweden": ("السويد", "SE"),
    "Norway": ("النرويج", "NO"),
    "Denmark": ("الدنمارك", "DK"),
    "Finland": ("فنلندا", "FI"),
    "Ireland": ("أيرلندا", "IE"),
    "Greece": ("اليونان", "GR"),
    "Poland": ("بولندا", "PL"),
    "Czechia": ("التشيك", "CZ"),
    "Czech Republic": ("التشيك", "CZ"),
    "Romania": ("رومانيا", "RO"),
    "Hungary": ("المجر", "HU"),
    "Ukraine": ("أوكرانيا", "UA"),
    "Russia": ("روسيا", "RU"),
    "Russian Federation": ("روسيا", "RU"),
    "Turkey": ("تركيا", "TR"),
    "Türkiye": ("تركيا", "TR"),
    "Israel": ("إسرائيل", "IL"),
    "Iran": ("إيران", "IR"),
    "Pakistan": ("باكستان", "PK"),
    "India": ("الهند", "IN"),
    "China": ("الصين", "CN"),
    "Hong Kong": ("هونغ كونغ", "HK"),
    "Japan": ("اليابان", "JP"),
    "South Korea": ("كوريا الجنوبية", "KR"),
    "Korea, Republic of": ("كوريا الجنوبية", "KR"),
    "Singapore": ("سنغافورة", "SG"),
    "Malaysia": ("ماليزيا", "MY"),
    "Indonesia": ("إندونيسيا", "ID"),
    "Thailand": ("تايلاند", "TH"),
    "Vietnam": ("فيتنام", "VN"),
    "Philippines": ("الفلبين", "PH"),
    "Australia": ("أستراليا", "AU"),
    "New Zealand": ("نيوزيلندا", "NZ"),
    "Canada": ("كندا", "CA"),
    "Mexico": ("المكسيك", "MX"),
    "Brazil": ("البرازيل", "BR"),
    "Argentina": ("الأرجنتين", "AR"),
    "Chile": ("تشيلي", "CL"),
    "Colombia": ("كولومبيا", "CO"),
    "Peru": ("بيرو", "PE"),
    "Venezuela": ("فنزويلا", "VE"),
    "South Africa": ("جنوب أفريقيا", "ZA"),
    "Nigeria": ("نيجيريا", "NG"),
    "Kenya": ("كينيا", "KE"),
    "Ethiopia": ("إثيوبيا", "ET"),
    "Ghana": ("غانا", "GH"),
    "Tanzania": ("تنزانيا", "TZ"),
    "Afghanistan": ("أفغانستان", "AF"),
    "Bangladesh": ("بنغلاديش", "BD"),
    "Sri Lanka": ("سريلانكا", "LK"),
    "Nepal": ("نيبال", "NP"),
    "Azerbaijan": ("أذربيجان", "AZ"),
    "Armenia": ("أرمينيا", "AM"),
    "Georgia": ("جورجيا", "GE"),
    "Kazakhstan": ("كازاخستان", "KZ"),
    "Uzbekistan": ("أوزبكستان", "UZ"),
    "Turkmenistan": ("تركمانستان", "TM"),
}


def iso_to_flag(iso_code):
    """ISO alpha-2 -> Unicode flag emoji (regional indicator pair)."""
    if not iso_code or len(iso_code) != 2:
        return '🏳️'
    code = iso_code.upper()
    return chr(0x1F1E6 + ord(code[0]) - ord('A')) + chr(0x1F1E6 + ord(code[1]) - ord('A'))


def get_country_info(english_name):
    """Return (arabic_name, iso_code, flag_emoji) for an English country name.

    Falls back to (english_name, '', generic_flag) if unknown.
    """
    if not english_name:
        return ('', '', '🏳️')
    info = _COUNTRY_AR.get(english_name)
    if info:
        ar, iso = info
        return (ar, iso, iso_to_flag(iso))
    return (english_name, '', '🏳️')
