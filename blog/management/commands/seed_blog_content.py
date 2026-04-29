"""
Seed comprehensive SEO-optimized blog content for ESCO Jordan.
Targets all major keyword clusters in the Jordan industrial tools market.
Competitor analysis covers: البشيتي، سرايا، جعفر شوب، رونيكس، فرسان الخيال
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from blog.models import BlogPost, BlogCategory, BlogTag, BlogPostFAQ
from accounts.models import User


CATEGORIES = [
    {
        'name': 'العدد الكهربائية',
        'name_en': 'Power Tools',
        'slug': 'power-tools',
        'description': 'دليلك الشامل للعدد الكهربائية والأجهزة الصناعية - مثاقب، مناشير، صواريخ قص، وأكثر',
        'description_en': 'Complete guide to power tools and industrial equipment - drills, saws, grinders and more',
        'icon': 'fa-bolt',
        'meta_title': 'العدد الكهربائية - أدوات كهربائية صناعية | ESCO الأردن',
        'meta_description': 'مقالات وأدلة شراء عن العدد الكهربائية والأجهزة الصناعية في الأردن. مثاقب، مناشير، صواريخ، وأكثر من ESCO.',
    },
    {
        'name': 'العدد اليدوية',
        'name_en': 'Hand Tools',
        'slug': 'hand-tools',
        'description': 'كل ما تحتاج معرفته عن العدد اليدوية - مفاتيح، مفكات، كماشات، شواكيش وأطقم عدة',
        'description_en': 'Everything about hand tools - wrenches, screwdrivers, pliers, hammers and tool sets',
        'icon': 'fa-wrench',
        'meta_title': 'العدد اليدوية - أدوات يدوية احترافية | ESCO الأردن',
        'meta_description': 'مقالات عن أفضل العدد اليدوية والأدوات الاحترافية في الأردن. مفاتيح ربط، مفكات، زراديات من ESCO.',
    },
    {
        'name': 'معدات اللحام',
        'name_en': 'Welding Equipment',
        'slug': 'welding-equipment',
        'description': 'أدلة شاملة عن معدات اللحام الكهربائي والأرجون وملحقاتها ومعدات الحماية',
        'description_en': 'Comprehensive guides on welding machines, argon welding, accessories and safety gear',
        'icon': 'fa-fire',
        'meta_title': 'معدات اللحام - ماكينات لحام صناعي | ESCO الأردن',
        'meta_description': 'دليل شامل لمعدات اللحام في الأردن. ماكينات لحام كهربائي، أرجون، MIG، TIG من ESCO.',
    },
    {
        'name': 'أدوات القياس',
        'name_en': 'Measuring Tools',
        'slug': 'measuring-tools',
        'description': 'أدوات القياس الدقيقة والمهنية - أجهزة ليزر، أمتار، فرجار، وأجهزة فحص',
        'description_en': 'Precision and professional measuring tools - laser levels, tape measures, calipers',
        'icon': 'fa-ruler-combined',
        'meta_title': 'أدوات القياس - أجهزة قياس دقيقة | ESCO الأردن',
        'meta_description': 'أدوات قياس احترافية في الأردن. أجهزة ليزر، أمتار، فرجار، ملتيميتر من ESCO.',
    },
    {
        'name': 'معدات السلامة المهنية',
        'name_en': 'Safety Equipment',
        'slug': 'safety-equipment',
        'description': 'معدات السلامة والحماية الشخصية للورش والمصانع والمواقع الإنشائية',
        'description_en': 'Safety and personal protective equipment for workshops, factories and construction sites',
        'icon': 'fa-hard-hat',
        'meta_title': 'معدات السلامة المهنية - حماية شخصية | ESCO الأردن',
        'meta_description': 'معدات سلامة مهنية في الأردن. خوذات، نظارات حماية، قفازات، أحذية سلامة من ESCO.',
    },
    {
        'name': 'معدات الرفع والنقل',
        'name_en': 'Lifting & Transport',
        'slug': 'lifting-transport',
        'description': 'معدات الرفع والنقل الصناعي - رافعات، ونشات، سلاسل، عربات تحميل',
        'description_en': 'Industrial lifting and transport equipment - hoists, winches, chains, trolleys',
        'icon': 'fa-dolly',
        'meta_title': 'معدات الرفع والنقل - رافعات صناعية | ESCO الأردن',
        'meta_description': 'معدات رفع ونقل صناعي في الأردن. رافعات هيدروليكية، ونشات، سلاسل رفع من ESCO.',
    },
    {
        'name': 'أدوات السباكة والصحية',
        'name_en': 'Plumbing Tools',
        'slug': 'plumbing-tools',
        'description': 'أدوات ولوازم السباكة والتمديدات الصحية للمحترفين',
        'description_en': 'Plumbing tools and sanitary supplies for professionals',
        'icon': 'fa-faucet',
        'meta_title': 'أدوات السباكة والصحية - لوازم سباكة | ESCO الأردن',
        'meta_description': 'أدوات سباكة احترافية في الأردن. مفاتيح أنابيب، قواطع مواسير، لوازم صحية من ESCO.',
    },
    {
        'name': 'أدوات الكهرباء والتمديدات',
        'name_en': 'Electrical Tools',
        'slug': 'electrical-tools',
        'description': 'عدد وأدوات الكهربائي - أجهزة فحص، أدوات تمديد، عدد كهربائية متخصصة',
        'description_en': 'Electrician tools - testing devices, wiring tools, specialized electrical equipment',
        'icon': 'fa-plug',
        'meta_title': 'أدوات الكهرباء والتمديدات - عدد كهربائي | ESCO الأردن',
        'meta_description': 'أدوات كهربائية متخصصة في الأردن. أجهزة فحص، ملتيميتر، عدد تمديدات من ESCO.',
    },
    {
        'name': 'مواد ومعدات البناء',
        'name_en': 'Construction Equipment',
        'slug': 'construction-equipment',
        'description': 'أدوات ومعدات البناء والتشييد - خلاطات، هزازات، أدوات تبليط وتسوية',
        'description_en': 'Construction tools and equipment - mixers, vibrators, tiling and leveling tools',
        'icon': 'fa-hard-hat',
        'meta_title': 'مواد ومعدات البناء - أدوات إنشائية | ESCO الأردن',
        'meta_description': 'معدات بناء وتشييد في الأردن. خلاطات باطون، هزازات، أدوات تبليط من ESCO.',
    },
    {
        'name': 'أدوات النجارة والخشب',
        'name_en': 'Carpentry Tools',
        'slug': 'carpentry-tools',
        'description': 'أدوات النجارة ومعالجة الخشب - مناشير، فريزات، صنفرة، وأدوات حفر',
        'description_en': 'Carpentry and woodworking tools - saws, routers, sanders, and drilling tools',
        'icon': 'fa-tree',
        'meta_title': 'أدوات النجارة والخشب - معدات نجارة | ESCO الأردن',
        'meta_description': 'أدوات نجارة احترافية في الأردن. مناشير خشب، فريزات، صنفرة كهربائية من ESCO.',
    },
    {
        'name': 'أدلة الشراء والمقارنات',
        'name_en': 'Buying Guides',
        'slug': 'buying-guides',
        'description': 'أدلة شراء شاملة ومقارنات بين أفضل الماركات والمنتجات لمساعدتك في اختيار الأنسب',
        'description_en': 'Comprehensive buying guides and brand comparisons to help you choose the best',
        'icon': 'fa-clipboard-check',
        'meta_title': 'أدلة شراء العدد والأدوات - مقارنات | ESCO الأردن',
        'meta_description': 'أدلة شراء ومقارنات شاملة لأفضل العدد والأدوات الصناعية في الأردن من ESCO.',
    },
    {
        'name': 'صيانة وعناية بالأدوات',
        'name_en': 'Maintenance & Care',
        'slug': 'maintenance-care',
        'description': 'نصائح وإرشادات للصيانة الدورية والعناية بالعدد والأدوات لإطالة عمرها',
        'description_en': 'Tips and guides for regular maintenance and tool care to extend their lifespan',
        'icon': 'fa-tools',
        'meta_title': 'صيانة وعناية بالأدوات - نصائح | ESCO الأردن',
        'meta_description': 'نصائح صيانة العدد والأدوات الصناعية. دليل العناية بالمعدات الكهربائية واليدوية من ESCO.',
    },
]

TAGS = [
    ('عدد صناعية', 'Industrial Tools'),
    ('أدوات كهربائية', 'Power Tools'),
    ('عدد يدوية', 'Hand Tools'),
    ('معدات لحام', 'Welding Equipment'),
    ('أدوات قياس', 'Measuring Tools'),
    ('سلامة مهنية', 'Safety Equipment'),
    ('معدات رفع', 'Lifting Equipment'),
    ('أدوات سباكة', 'Plumbing Tools'),
    ('أدوات كهربائي', 'Electrician Tools'),
    ('معدات بناء', 'Construction Equipment'),
    ('أدوات نجارة', 'Carpentry Tools'),
    ('بوش', 'Bosch'),
    ('ماكيتا', 'Makita'),
    ('ديوالت', 'DeWalt'),
    ('ستانلي', 'Stanley'),
    ('انكو', 'INGCO'),
    ('توتال', 'Total'),
    ('هيلتي', 'Hilti'),
    ('ميلووكي', 'Milwaukee'),
    ('دريل', 'Drill'),
    ('مثقاب', 'Drill Bit'),
    ('صاروخ جلخ', 'Angle Grinder'),
    ('منشار كهربائي', 'Electric Saw'),
    ('مفاتيح ربط', 'Wrenches'),
    ('مفكات', 'Screwdrivers'),
    ('شريط قياس', 'Tape Measure'),
    ('ميزان ليزر', 'Laser Level'),
    ('خوذة سلامة', 'Safety Helmet'),
    ('نظارات حماية', 'Safety Glasses'),
    ('قفازات حماية', 'Safety Gloves'),
    ('ماكينة لحام', 'Welding Machine'),
    ('كمبريسور', 'Compressor'),
    ('مولد كهربائي', 'Generator'),
    ('رافعة هيدروليكية', 'Hydraulic Jack'),
    ('عدد شحن', 'Cordless Tools'),
    ('عدد بطارية', 'Battery Tools'),
    ('الأردن', 'Jordan'),
    ('عمان', 'Amman'),
    ('ورش صناعية', 'Industrial Workshops'),
    ('مصانع', 'Factories'),
    ('مقاولات', 'Contracting'),
    ('صنفرة كهربائية', 'Electric Sander'),
    ('فريزة', 'Router'),
    ('مضخة ماء', 'Water Pump'),
    ('سلم المنيوم', 'Aluminum Ladder'),
    ('طقم عدة', 'Tool Set'),
    ('صندوق عدة', 'Tool Box'),
    ('أحذية سلامة', 'Safety Shoes'),
    ('حزام أمان', 'Safety Harness'),
    ('لحام أرجون', 'Argon Welding'),
]


def _p(text):
    return f'<p>{text}</p>'


def _h2(text):
    return f'<h2>{text}</h2>'


def _h3(text):
    return f'<h3>{text}</h3>'


def _ul(items):
    li = ''.join(f'<li>{item}</li>' for item in items)
    return f'<ul>{li}</ul>'


def _ol(items):
    li = ''.join(f'<li>{item}</li>' for item in items)
    return f'<ol>{li}</ol>'


POSTS = [
    # ─── POST 1: Power Tools Guide ───
    {
        'title': 'دليلك الشامل لاختيار أفضل العدد الكهربائية في الأردن 2025',
        'title_en': 'Complete Guide to Choosing the Best Power Tools in Jordan 2025',
        'slug': 'best-power-tools-jordan-guide',
        'category_slug': 'power-tools',
        'tags': ['أدوات كهربائية', 'عدد صناعية', 'بوش', 'ماكيتا', 'ديوالت', 'الأردن'],
        'excerpt': 'دليل شامل لاختيار أفضل العدد الكهربائية للمحترفين والهواة في الأردن. مقارنة بين أشهر الماركات العالمية مع نصائح الخبراء.',
        'excerpt_en': 'Complete guide to choosing the best power tools for professionals and hobbyists in Jordan. Comparison of top global brands with expert tips.',
        'card_icon': 'fa-bolt',
        'card_icon_color': '#2563eb',
        'meta_title': 'أفضل العدد الكهربائية في الأردن 2025 - دليل شراء شامل | ESCO',
        'meta_description': 'دليل شامل لاختيار أفضل العدد الكهربائية في الأردن. مقارنة بوش، ماكيتا، ديوالت مع أسعار ونصائح خبراء ESCO.',
        'meta_keywords': 'عدد كهربائية, أدوات كهربائية الأردن, دريل كهربائي, صاروخ جلخ, منشار كهربائي, بوش الأردن, ماكيتا, ديوالت',
        'content': (
            _h2('ما هي العدد الكهربائية وأهميتها؟') +
            _p('العدد الكهربائية هي الأدوات التي تعمل بالطاقة الكهربائية أو البطاريات القابلة للشحن، وتُستخدم في مختلف الأعمال الصناعية والحرفية والمنزلية. تتميز هذه الأدوات بقدرتها على إنجاز المهام بسرعة ودقة أكبر مقارنة بالأدوات اليدوية التقليدية.') +
            _p('في الأردن، يتزايد الطلب على العدد الكهربائية عالية الجودة من قبل المهندسين والفنيين وشركات المقاولات والورش الصناعية. توفر شركة مستودعات الهندسة ESCO مجموعة واسعة من أفضل الماركات العالمية لتلبية جميع الاحتياجات.') +

            _h2('أنواع العدد الكهربائية الأساسية') +

            _h3('1. المثاقب الكهربائية (الدريل)') +
            _p('المثقاب الكهربائي أو الدريل هو أكثر العدد الكهربائية استخداماً في الأردن. يتوفر بعدة أنواع تشمل:') +
            _ul([
                '<strong>الدريل العادي:</strong> مناسب لثقب الخشب والمعادن الخفيفة، بقوة تتراوح بين 400-700 واط',
                '<strong>دريل المطرقة (الهامر دريل):</strong> مثالي لثقب الباطون والحجر، يوفر قوة طرق إضافية',
                '<strong>الدريل اللاسلكي (شحن):</strong> يعمل بالبطارية ويوفر حرية الحركة، مثالي للأماكن التي لا تتوفر فيها كهرباء',
                '<strong>الهيلتي (هامر دريل احترافي):</strong> للتكسير والثقب في الباطون المسلح والصخور',
            ]) +

            _h3('2. صواريخ القص والجلخ (الجرايندر)') +
            _p('تُستخدم صواريخ القص والجلخ في قطع وصقل المعادن والحجر والبلاط. تتوفر بأحجام مختلفة تبدأ من 4.5 بوصة وحتى 9 بوصة. تُعد من أهم الأدوات في ورش الحدادة وأعمال البناء في الأردن.') +

            _h3('3. المناشير الكهربائية') +
            _p('تشمل المناشير الكهربائية عدة أنواع حسب الاستخدام:') +
            _ul([
                '<strong>المنشار الدائري:</strong> لقطع الخشب بشكل مستقيم ودقيق',
                '<strong>منشار التخريقة (الجيكسو):</strong> للقطع المنحني والتفصيلي',
                '<strong>المنشار الترددي (السيبر سو):</strong> لقطع المعادن والأنابيب',
                '<strong>منشار الزاوية (القص والتركيب):</strong> لقطع الخشب والألمنيوم بزوايا دقيقة',
            ]) +

            _h3('4. أدوات الصنفرة والتشطيب') +
            _p('تشمل الصنافر المدارية والحزامية وصنافر التفاصيل. تُستخدم في تنعيم الأسطح الخشبية والمعدنية وتجهيزها للدهان أو التشطيب النهائي.') +

            _h2('أفضل ماركات العدد الكهربائية في الأردن') +

            _h3('بوش (Bosch) - ألمانيا') +
            _p('تُعد بوش من أشهر وأعرق العلامات التجارية في مجال العدد الكهربائية عالمياً. تتميز منتجاتها بالمتانة والدقة والتكنولوجيا المتقدمة. توفر بوش خطين رئيسيين: الخط الأزرق للمحترفين والخط الأخضر للاستخدام المنزلي.') +

            _h3('ماكيتا (Makita) - اليابان') +
            _p('ماكيتا هي علامة يابانية عريقة تتميز بالموثوقية العالية وخفة الوزن. محركاتها الخالية من الفحم (Brushless) توفر عمراً أطول وكفاءة أعلى. تُفضل كثيراً من قبل النجارين والكهربائيين في الأردن.') +

            _h3('ديوالت (DeWalt) - أمريكا') +
            _p('ديوالت معروفة بمتانتها الاستثنائية وقدرتها على تحمل ظروف العمل القاسية. تتميز بنظام بطاريات 20 فولت MAX الذي يتوافق مع أكثر من 200 أداة مختلفة. مثالية لشركات المقاولات والمشاريع الكبيرة.') +

            _h3('انكو (INGCO)') +
            _p('انكو هي علامة تجارية تقدم أدوات بجودة جيدة وأسعار منافسة. تُعد خياراً ممتازاً للهواة وأصحاب الورش الصغيرة في الأردن الذين يبحثون عن أدوات موثوقة بميزانية معقولة.') +

            _h2('نصائح لاختيار العدد الكهربائية المناسبة') +
            _ol([
                '<strong>حدد طبيعة الاستخدام:</strong> هل تحتاجها للاستخدام المهني اليومي أم للمشاريع المنزلية؟',
                '<strong>اختر القوة المناسبة:</strong> القوة بالواط تحدد قدرة الأداة. للأعمال الثقيلة اختر قوة أعلى.',
                '<strong>سلكي أم لاسلكي:</strong> اللاسلكي يوفر حرية الحركة لكن السلكي يوفر قوة ثابتة.',
                '<strong>تحقق من الضمان:</strong> اختر منتجات بضمان رسمي في الأردن.',
                '<strong>توفر قطع الغيار:</strong> تأكد من توفر قطع الغيار والصيانة محلياً.',
                '<strong>الميزانية:</strong> لا تشترِ الأرخص دائماً - الأداة الجيدة استثمار طويل الأمد.',
            ]) +

            _h2('أين تشتري العدد الكهربائية في الأردن؟') +
            _p('توفر شركة مستودعات الهندسة ESCO في عمان أكبر تشكيلة من العدد الكهربائية الأصلية مع ضمان رسمي وأسعار منافسة. نخدم الأفراد والشركات والمؤسسات الحكومية في جميع أنحاء المملكة الأردنية الهاشمية.') +
            _p('سواء كنت مهندساً، فنياً، مقاولاً، أو صاحب ورشة صناعية، ستجد لدينا جميع احتياجاتك من العدد الكهربائية بأفضل الماركات العالمية وبأسعار تنافسية مع خدمة توصيل لجميع مناطق الأردن.')
        ),
        'content_en': (
            _h2('What Are Power Tools and Why Are They Important?') +
            _p('Power tools are tools powered by electricity or rechargeable batteries, used in various industrial, craft, and household applications. They excel at completing tasks faster and with greater precision compared to traditional hand tools.') +
            _p('In Jordan, demand for high-quality power tools continues to grow among engineers, technicians, contracting companies, and industrial workshops. ESCO Engineering Stores offers a wide range of the best global brands to meet all needs.') +

            _h2('Essential Types of Power Tools') +

            _h3('1. Electric Drills') +
            _p('The electric drill is the most widely used power tool in Jordan, available in several types including standard drills, hammer drills for concrete, cordless drills for mobility, and rotary hammers for heavy-duty concrete and rock drilling.') +

            _h3('2. Angle Grinders') +
            _p('Used for cutting and grinding metal, stone, and tiles. Available in sizes from 4.5 to 9 inches, they are essential tools in metalworking shops and construction sites across Jordan.') +

            _h3('3. Electric Saws') +
            _p('Including circular saws for straight cuts, jigsaws for curved cuts, reciprocating saws for metal and pipes, and miter saws for precise angle cuts in wood and aluminum.') +

            _h2('Top Power Tool Brands in Jordan') +
            _p('ESCO carries the best global brands including Bosch (Germany), Makita (Japan), DeWalt (USA), and INGCO for budget-friendly options. Each brand offers unique advantages depending on your professional needs and budget.') +

            _h2('Where to Buy Power Tools in Jordan') +
            _p('ESCO Engineering Stores in Amman offers the largest selection of original power tools with official warranty and competitive prices. We serve individuals, companies, and government institutions across the Hashemite Kingdom of Jordan.')
        ),
        'faqs': [
            {
                'question': 'ما هي أفضل ماركة عدد كهربائية في الأردن؟',
                'question_en': 'What is the best power tool brand in Jordan?',
                'answer': 'تعتمد أفضل ماركة على طبيعة استخدامك. للمحترفين، تُعد بوش وماكيتا وديوالت من أفضل الخيارات. للاستخدام المنزلي، تقدم انكو وتوتال أدوات جيدة بأسعار معقولة. في ESCO نوفر جميع هذه الماركات مع ضمان رسمي.',
                'answer_en': 'The best brand depends on your usage. For professionals, Bosch, Makita, and DeWalt are top choices. For home use, INGCO and Total offer good tools at reasonable prices. At ESCO we carry all these brands with official warranty.',
            },
            {
                'question': 'ما الفرق بين الدريل العادي ودريل المطرقة؟',
                'question_en': 'What is the difference between a regular drill and a hammer drill?',
                'answer': 'الدريل العادي يناسب الثقب في الخشب والمعادن الخفيفة فقط. أما دريل المطرقة (الهامر دريل) فيوفر حركة طرق إضافية تمكنه من ثقب الباطون والحجر. إذا كنت تعمل في البناء أو التمديدات، فإن دريل المطرقة هو الخيار الأمثل.',
                'answer_en': 'A regular drill is suitable for drilling wood and light metals only. A hammer drill provides additional impact action for drilling concrete and stone. If you work in construction, a hammer drill is the optimal choice.',
            },
            {
                'question': 'هل العدد الكهربائية اللاسلكية (الشحن) قوية بما يكفي؟',
                'question_en': 'Are cordless power tools powerful enough?',
                'answer': 'نعم، تطورت العدد اللاسلكية بشكل كبير وأصبحت توفر قوة مماثلة للسلكية في معظم التطبيقات. بطاريات 18-20 فولت الحديثة توفر أداءً ممتازاً. لكن للأعمال الثقيلة والمستمرة لساعات طويلة، قد تكون الأدوات السلكية أفضل.',
                'answer_en': 'Yes, cordless tools have evolved significantly and now offer power comparable to corded tools in most applications. Modern 18-20V batteries provide excellent performance, though corded tools may be better for continuous heavy-duty work.',
            },
            {
                'question': 'كم سعر الدريل الكهربائي في الأردن؟',
                'question_en': 'How much does an electric drill cost in Jordan?',
                'answer': 'تتراوح أسعار الدريل الكهربائي في الأردن حسب الماركة والنوع. الدريلات الاقتصادية تبدأ من 15-25 دينار، والمتوسطة من 40-80 دينار، والاحترافية من بوش أو ماكيتا من 90-200 دينار وأكثر. زوروا ESCO للاطلاع على أحدث الأسعار.',
                'answer_en': 'Electric drill prices in Jordan vary by brand and type. Budget drills start from 15-25 JOD, mid-range from 40-80 JOD, and professional Bosch or Makita drills from 90-200+ JOD. Visit ESCO for the latest prices.',
            },
        ],
    },

    # ─── POST 2: Hand Tools ───
    {
        'title': 'أفضل العدد اليدوية للمهندسين والفنيين في الأردن',
        'title_en': 'Best Hand Tools for Engineers and Technicians in Jordan',
        'slug': 'best-hand-tools-engineers-jordan',
        'category_slug': 'hand-tools',
        'tags': ['عدد يدوية', 'مفاتيح ربط', 'مفكات', 'عدد صناعية', 'ستانلي', 'الأردن'],
        'excerpt': 'تعرف على أفضل أنواع العدد اليدوية الاحترافية للمهندسين والفنيين. أطقم مفاتيح، مفكات، زراديات، وشواكيش من أشهر الماركات.',
        'excerpt_en': 'Discover the best professional hand tools for engineers and technicians. Wrench sets, screwdrivers, pliers, and hammers from top brands.',
        'card_icon': 'fa-wrench',
        'card_icon_color': '#059669',
        'meta_title': 'أفضل العدد اليدوية في الأردن - مفاتيح ومفكات احترافية | ESCO',
        'meta_description': 'أفضل العدد اليدوية للمهندسين والفنيين في الأردن. مفاتيح ربط، بوكسات، مفكات، زراديات من ESCO مستودعات الهندسة.',
        'meta_keywords': 'عدد يدوية, مفاتيح ربط, بوكسات, مفكات, زراديات, شواكيش, أطقم عدة, ستانلي, الأردن',
        'content': (
            _h2('أهمية العدد اليدوية في الأعمال الهندسية والصناعية') +
            _p('تُعد العدد اليدوية الركيزة الأساسية لأي مهندس أو فني محترف في الأردن. رغم تطور العدد الكهربائية، تبقى الأدوات اليدوية ضرورية في كثير من التطبيقات التي تتطلب دقة وتحكماً يدوياً. من صيانة المصانع إلى أعمال التمديدات الكهربائية والسباكة، لا غنى عن طقم عدة يدوية متكامل وعالي الجودة.') +

            _h2('أنواع العدد اليدوية الأساسية') +

            _h3('مفاتيح الربط والبوكسات') +
            _p('تُستخدم مفاتيح الربط لشد وفك البراغي والصواميل. تتوفر بعدة أنواع:') +
            _ul([
                '<strong>مفاتيح مفتوحة (Open-End):</strong> الأكثر شيوعاً، بفتحة على شكل U',
                '<strong>مفاتيح حلقية (Ring):</strong> توفر تماسكاً أفضل مع رأس البرغي',
                '<strong>مفاتيح كمبينيشن:</strong> مفتوحة من جهة وحلقية من الأخرى',
                '<strong>بوكسات (Socket Set):</strong> طقم بوكسات مع راتشت للعمل في الأماكن الضيقة',
                '<strong>مفتاح طوق (Allen Key):</strong> لبراغي الألن السداسية',
                '<strong>مفتاح فرنساوي (Adjustable):</strong> قابل للتعديل ليناسب أحجام مختلفة',
            ]) +

            _h3('المفكات') +
            _p('المفكات من أكثر الأدوات استخداماً يومياً:') +
            _ul([
                '<strong>مفك مسطح (Flathead):</strong> للبراغي ذات الشق المستقيم',
                '<strong>مفك صليبي (Phillips):</strong> للبراغي ذات الشق الصليبي',
                '<strong>مفك نجمة (Torx):</strong> للبراغي ذات الرأس النجمي',
                '<strong>مفك عزل كهربائي:</strong> معزول للعمل على الدوائر الكهربائية بأمان',
                '<strong>أطقم مفكات دقيقة:</strong> للإلكترونيات والأجهزة الحساسة',
            ]) +

            _h3('الزراديات والكماشات') +
            _p('تتوفر بأنواع متعددة حسب الاستخدام:') +
            _ul([
                '<strong>زرادية عادية:</strong> للإمساك والثني',
                '<strong>كماشة قطع:</strong> لقطع الأسلاك والمعادن الرقيقة',
                '<strong>زرادية طويلة الأنف:</strong> للعمل في الأماكن الضيقة',
                '<strong>كماشة كهربائي:</strong> معزولة للعمل الكهربائي',
                '<strong>زرادية قفل (Locking Pliers):</strong> تثبت بشكل محكم على القطعة',
            ]) +

            _h3('الشواكيش والمطارق') +
            _p('تتوفر الشواكيش بأنواع مختلفة تشمل شاكوش النجار، شاكوش الحداد، المطارق المطاطية للأعمال الحساسة، ومطارق التكسير الثقيلة للأعمال الإنشائية.') +

            _h2('أفضل ماركات العدد اليدوية') +
            _ul([
                '<strong>ستانلي (Stanley):</strong> علامة أمريكية عريقة تقدم أدوات متينة وعملية بأسعار متوسطة',
                '<strong>بيتا (Beta):</strong> علامة إيطالية مشهورة بجودتها الاستثنائية للمحترفين',
                '<strong>بوش (Bosch):</strong> تقدم خطاً كاملاً من العدد اليدوية بالجودة الألمانية المعروفة',
                '<strong>انكو (INGCO):</strong> خيار اقتصادي بجودة جيدة للورش والاستخدام العام',
                '<strong>كينج توني (King Tony):</strong> متخصصة في البوكسات والمفاتيح الاحترافية',
            ]) +

            _h2('كيف تختار طقم العدة المناسب؟') +
            _p('عند اختيار طقم عدة يدوية، يجب مراعاة طبيعة عملك. للميكانيكي تحتاج أطقم بوكسات ومفاتيح كمبينيشن. للكهربائي تحتاج مفكات معزولة وزراديات كهربائية. للنجار تحتاج شواكيش وأزاميل وأدوات قياس. في ESCO نوفر أطقم متكاملة لكل تخصص.') +

            _h2('اشترِ العدد اليدوية الأصلية من ESCO') +
            _p('في مستودعات الهندسة ESCO، نوفر أكبر تشكيلة من العدد اليدوية الأصلية في الأردن. جميع منتجاتنا مضمونة وبأسعار منافسة. نخدم المهندسين والفنيين والشركات والمصانع والورش في جميع أنحاء المملكة. تواصل معنا أو زُر أقرب فرع.')
        ),
        'content_en': (
            _h2('The Importance of Hand Tools in Engineering and Industrial Work') +
            _p('Hand tools are the foundation for any professional engineer or technician in Jordan. Despite advances in power tools, hand tools remain essential for applications requiring precision and manual control.') +
            _h2('Essential Types of Hand Tools') +
            _p('Key categories include wrenches and socket sets, screwdrivers, pliers and cutters, and hammers. Each type comes in various configurations for different professional needs.') +
            _h2('Buy Original Hand Tools from ESCO') +
            _p('ESCO Engineering Stores offers the largest selection of original hand tools in Jordan with warranty and competitive prices for engineers, technicians, companies, and workshops.')
        ),
        'faqs': [
            {
                'question': 'ما هي أهم العدد اليدوية التي يحتاجها كل فني في الأردن؟',
                'question_en': 'What are the most important hand tools every technician needs in Jordan?',
                'answer': 'يحتاج كل فني إلى: طقم مفاتيح كمبينيشن (8-24 ملم)، طقم بوكسات مع راتشت، مجموعة مفكات (مسطح وصليبي)، زرادية وكماشة قطع، شريط قياس، ميزان مياء، شاكوش، وسكين متعددة الاستخدام. في ESCO نوفر أطقم عدة متكاملة تحتوي على كل هذه الأدوات وأكثر.',
                'answer_en': 'Every technician needs: combination wrench set (8-24mm), socket set with ratchet, screwdriver set (flat and Phillips), pliers and wire cutters, tape measure, level, hammer, and utility knife. ESCO offers complete tool sets with all these and more.',
            },
            {
                'question': 'ما الفرق بين العدد اليدوية الأصلية والتقليد؟',
                'question_en': 'What is the difference between original and counterfeit hand tools?',
                'answer': 'العدد الأصلية مصنوعة من سبائك فولاذية عالية الجودة (كروم فاناديوم) وتخضع لمعاملة حرارية دقيقة، مما يمنحها متانة ومقاومة عالية للكسر والتآكل. التقليد يستخدم معادن رخيصة تتلف بسرعة وقد تسبب إصابات. دائماً اشترِ من موزع معتمد مثل ESCO.',
                'answer_en': 'Original tools are made from high-quality steel alloys (Chrome Vanadium) with precise heat treatment, providing durability and resistance to breakage. Counterfeits use cheap metals that damage quickly and can cause injuries. Always buy from authorized dealers like ESCO.',
            },
        ],
    },

    # ─── POST 3: Welding ───
    {
        'title': 'دليل معدات اللحام الصناعي في الأردن - أنواعها واستخداماتها',
        'title_en': 'Industrial Welding Equipment Guide in Jordan - Types and Applications',
        'slug': 'welding-equipment-guide-jordan',
        'category_slug': 'welding-equipment',
        'tags': ['معدات لحام', 'ماكينة لحام', 'لحام أرجون', 'عدد صناعية', 'الأردن', 'ورش صناعية'],
        'excerpt': 'كل ما تحتاج معرفته عن معدات اللحام في الأردن. أنواع ماكينات اللحام، الفرق بين اللحام الكهربائي والأرجون، ونصائح السلامة.',
        'excerpt_en': 'Everything you need to know about welding equipment in Jordan. Types of welding machines, differences between electric and argon welding, and safety tips.',
        'card_icon': 'fa-fire',
        'card_icon_color': '#dc2626',
        'meta_title': 'معدات اللحام في الأردن - ماكينات لحام كهربائي وأرجون | ESCO',
        'meta_description': 'دليل شامل لمعدات اللحام في الأردن. ماكينات لحام كهربائي، أرجون TIG، MIG. أفضل الماركات والأسعار من ESCO.',
        'meta_keywords': 'معدات لحام, ماكينة لحام, لحام كهربائي, لحام أرجون, TIG, MIG, اسياخ لحام, الأردن',
        'content': (
            _h2('أهمية اللحام في القطاع الصناعي الأردني') +
            _p('يُعد اللحام من أهم العمليات الصناعية في الأردن، حيث يُستخدم في تصنيع الهياكل المعدنية، صيانة المعدات، أعمال الحدادة، صناعة الأبواب والشبابيك، وتركيب المنشآت الصناعية. تعتمد جودة أعمال اللحام بشكل كبير على نوعية المعدات المستخدمة ومهارة اللحام.') +

            _h2('أنواع ماكينات اللحام') +

            _h3('1. لحام القوس الكهربائي (SMMA/Stick Welding)') +
            _p('أكثر أنواع اللحام انتشاراً في الأردن. يستخدم أسياخ لحام (إلكترودات) مغلفة لوصل المعادن. مناسب للحديد والفولاذ الكربوني. سهل الاستخدام ومنخفض التكلفة. يتوفر بقدرات مختلفة تبدأ من 160 أمبير للأعمال الخفيفة وحتى 400 أمبير للأعمال الثقيلة.') +

            _h3('2. لحام الأرجون TIG (Tungsten Inert Gas)') +
            _p('يستخدم غاز الأرجون لحماية منطقة اللحام من التأكسد. يوفر لحاماً نظيفاً ودقيقاً ومناسباً للألمنيوم والستانلس ستيل والمعادن الرقيقة. يتطلب مهارة أعلى لكنه يعطي نتائج احترافية متميزة.') +

            _h3('3. لحام MIG (Metal Inert Gas)') +
            _p('يستخدم سلك لحام متصل يتغذى تلقائياً مع غاز حماية. أسرع من TIG ومناسب للإنتاج الكمي. مثالي لورش الحدادة ومصانع الأبواب والشبابيك في الأردن.') +

            _h3('4. لحام البلازما') +
            _p('يستخدم قوس بلازما عالي الحرارة للقطع واللحام. مناسب للمعادن السميكة والقطع الدقيق. يُستخدم في الصناعات المتقدمة والورش الكبيرة.') +

            _h2('ملحقات ومستلزمات اللحام') +
            _ul([
                '<strong>أسياخ اللحام:</strong> بأقطار 2.5، 3.2، و4 ملم لتطبيقات مختلفة',
                '<strong>أسلاك اللحام MIG:</strong> بأقطار 0.8 و1.0 ملم',
                '<strong>قناع لحام أوتوماتيك:</strong> يغمق تلقائياً عند بدء اللحام لحماية العينين',
                '<strong>قفازات لحام جلدية:</strong> لحماية اليدين من الحرارة والشرر',
                '<strong>مريلة لحام:</strong> من الجلد الطبيعي للحماية',
                '<strong>فرش تنظيف اللحام:</strong> لإزالة الأكاسيد وتنظيف وصلات اللحام',
            ]) +

            _h2('نصائح السلامة أثناء اللحام') +
            _ol([
                'ارتدِ دائماً قناع اللحام المعتمد لحماية العينين من الأشعة فوق البنفسجية',
                'استخدم قفازات ومريلة جلدية لحماية الجسم من الشرر',
                'تأكد من التهوية الجيدة في مكان العمل',
                'أبعد المواد القابلة للاشتعال عن منطقة اللحام',
                'افحص كابلات الماكينة بانتظام وتأكد من سلامتها',
                'احتفظ بطفاية حريق قريبة من منطقة العمل',
            ]) +

            _h2('شراء معدات اللحام من ESCO') +
            _p('توفر مستودعات الهندسة ESCO أشمل تشكيلة من معدات اللحام في الأردن، من ماكينات اللحام الكهربائي والأرجون إلى جميع الملحقات ومعدات السلامة. نقدم خدمات ما بعد البيع والصيانة والدعم الفني لجميع عملائنا من الأفراد والشركات.')
        ),
        'content_en': (
            _h2('Importance of Welding in Jordan\'s Industrial Sector') +
            _p('Welding is one of the most important industrial processes in Jordan, used in metal structure fabrication, equipment maintenance, blacksmithing, door and window manufacturing, and industrial installation.') +
            _h2('Types of Welding Machines') +
            _p('The main types include Stick Welding (SMMA), TIG Welding (Tungsten Inert Gas) using argon, MIG Welding (Metal Inert Gas), and Plasma welding. Each has specific applications and advantages.') +
            _h2('Buy Welding Equipment from ESCO') +
            _p('ESCO Engineering Stores offers the most comprehensive range of welding equipment in Jordan, from electric and argon welding machines to all accessories and safety equipment.')
        ),
        'faqs': [
            {
                'question': 'ما الفرق بين اللحام الكهربائي ولحام الأرجون؟',
                'question_en': 'What is the difference between electric welding and argon welding?',
                'answer': 'اللحام الكهربائي (Stick) يستخدم أسياخ مغلفة وهو أبسط وأرخص، مناسب للحديد العادي. لحام الأرجون (TIG) يستخدم غاز الأرجون للحماية ويعطي لحاماً أنظف وأدق، مناسب للألمنيوم والستانلس ستيل. الأرجون أغلى لكنه أعلى جودة.',
                'answer_en': 'Electric (Stick) welding uses coated rods and is simpler and cheaper, suitable for regular iron. Argon (TIG) welding uses argon gas for protection, producing cleaner and more precise welds, suitable for aluminum and stainless steel.',
            },
            {
                'question': 'كم سعر ماكينة اللحام في الأردن؟',
                'question_en': 'How much does a welding machine cost in Jordan?',
                'answer': 'تتراوح أسعار ماكينات اللحام في الأردن: اللحام الكهربائي من 50-200 دينار، ماكينات MIG من 200-800 دينار، وماكينات TIG/أرجون من 300-1500 دينار حسب الماركة والقدرة. في ESCO نوفر خيارات لجميع الميزانيات.',
                'answer_en': 'Welding machine prices in Jordan range: electric stick from 50-200 JOD, MIG machines from 200-800 JOD, and TIG/argon machines from 300-1500 JOD depending on brand and capacity. ESCO offers options for all budgets.',
            },
        ],
    },

    # ─── POST 4: Safety Equipment ───
    {
        'title': 'معدات السلامة المهنية في الأردن - دليل الحماية الشخصية للعمال',
        'title_en': 'Occupational Safety Equipment in Jordan - Personal Protection Guide',
        'slug': 'safety-equipment-guide-jordan',
        'category_slug': 'safety-equipment',
        'tags': ['سلامة مهنية', 'خوذة سلامة', 'نظارات حماية', 'قفازات حماية', 'أحذية سلامة', 'حزام أمان', 'الأردن', 'مصانع'],
        'excerpt': 'دليل شامل لمعدات السلامة المهنية في الأردن. خوذات، نظارات حماية، قفازات، أحذية سلامة، أحزمة أمان ومعدات الحماية للمصانع والمواقع الإنشائية.',
        'excerpt_en': 'Comprehensive guide to occupational safety equipment in Jordan. Helmets, safety glasses, gloves, safety shoes, harnesses for factories and construction sites.',
        'card_icon': 'fa-hard-hat',
        'card_icon_color': '#f59e0b',
        'meta_title': 'معدات السلامة المهنية في الأردن - حماية شخصية | ESCO',
        'meta_description': 'دليل معدات السلامة المهنية في الأردن. خوذات، نظارات، قفازات، أحذية سلامة، أحزمة أمان. معتمدة دولياً من ESCO.',
        'meta_keywords': 'معدات سلامة, سلامة مهنية, خوذة سلامة, نظارات حماية, قفازات حماية, أحذية سلامة, حزام أمان, الأردن',
        'content': (
            _h2('أهمية معدات السلامة المهنية في الأردن') +
            _p('تُعد السلامة المهنية من أولويات القطاع الصناعي في الأردن. يُلزم قانون العمل الأردني أصحاب العمل بتوفير معدات الحماية الشخصية للعاملين في المصانع والمواقع الإنشائية والورش الصناعية. الاستثمار في معدات السلامة ليس فقط التزاماً قانونياً بل هو حماية لأثمن ما تملك الشركة - موظفيها.') +

            _h2('أنواع معدات الحماية الشخصية (PPE)') +

            _h3('1. حماية الرأس - خوذات السلامة') +
            _p('خوذة السلامة هي خط الدفاع الأول لحماية الرأس من السقوط والارتطام. يجب أن تكون معتمدة وفق المعايير الدولية (EN 397 أو ANSI Z89.1). تتوفر بألوان مختلفة حسب التخصص: أبيض للمهندسين، أصفر للعمال، أحمر للمشرفين.') +

            _h3('2. حماية العينين - نظارات ودروع الوجه') +
            _p('تحمي العينين من الشظايا والغبار والمواد الكيميائية والأشعة. تشمل نظارات حماية شفافة، نظارات مقاومة للصدمات، نظارات لحام، ودروع وجه كاملة للأعمال عالية الخطورة.') +

            _h3('3. حماية اليدين - القفازات') +
            _p('تتنوع القفازات حسب الاستخدام:') +
            _ul([
                '<strong>قفازات جلدية:</strong> للحام والأعمال الحرارية',
                '<strong>قفازات نتريل:</strong> مقاومة للمواد الكيميائية',
                '<strong>قفازات قماشية مطلية:</strong> للتحميل والتفريغ',
                '<strong>قفازات عازلة كهربائياً:</strong> للعمل على الشبكات الكهربائية',
                '<strong>قفازات مقاومة للقطع:</strong> للعمل مع المواد الحادة والزجاج',
            ]) +

            _h3('4. حماية القدمين - أحذية السلامة') +
            _p('أحذية السلامة الصناعية مصممة بمقدمة حديدية لحماية أصابع القدم من السقوط والدهس، ونعل مقاوم للانزلاق والثقب. معيار S3 يوفر أعلى مستوى حماية. ضرورية في المواقع الإنشائية والمصانع والمستودعات.') +

            _h3('5. الحماية من السقوط - أحزمة الأمان') +
            _p('أحزمة الأمان وأنظمة الحماية من السقوط إلزامية لأي عمل على ارتفاع يزيد عن مترين. تشمل حزام الجسم الكامل، حبل الإيقاف، ونقاط التثبيت. يجب فحصها دورياً واستبدالها عند تعرضها لحمل سقوط.') +

            _h3('6. حماية السمع') +
            _p('سدادات وأغطية الأذن ضرورية في بيئات العمل الصاخبة كالمصانع وورش الحدادة. التعرض المستمر للضوضاء فوق 85 ديسيبل يسبب ضرراً دائماً للسمع.') +

            _h3('7. حماية الجهاز التنفسي') +
            _p('أقنعة الغبار والكمامات المزودة بفلاتر ضرورية عند العمل مع المواد المتطايرة والدهانات والمواد الكيميائية. تتوفر من كمامات بسيطة FFP2 إلى أقنعة كاملة مع فلاتر متخصصة.') +

            _h2('متطلبات السلامة في المصانع والمواقع الأردنية') +
            _p('يفرض قانون العمل الأردني وأنظمة وزارة العمل على المنشآت الصناعية والإنشائية توفير معدات الحماية الشخصية المناسبة لجميع العاملين. يشمل ذلك إجراء تقييم مخاطر دوري وتدريب العاملين على استخدام المعدات بشكل صحيح.') +

            _h2('اشترِ معدات السلامة المعتمدة من ESCO') +
            _p('توفر مستودعات الهندسة ESCO مجموعة كاملة من معدات السلامة المهنية المعتمدة دولياً. نخدم المصانع وشركات المقاولات والمؤسسات الحكومية والخاصة في الأردن بمعدات سلامة عالية الجودة وبأسعار تنافسية. تواصل معنا لطلبات الجملة والعروض الخاصة للشركات.')
        ),
        'content_en': (
            _h2('Importance of Occupational Safety Equipment in Jordan') +
            _p('Occupational safety is a top priority in Jordan\'s industrial sector. Jordanian labor law requires employers to provide personal protective equipment for workers in factories, construction sites, and workshops.') +
            _h2('Types of Personal Protective Equipment (PPE)') +
            _p('Essential categories include head protection (helmets), eye protection (safety glasses and face shields), hand protection (various glove types), foot protection (safety shoes), fall protection (harnesses), hearing protection, and respiratory protection.') +
            _h2('Buy Certified Safety Equipment from ESCO') +
            _p('ESCO Engineering Stores provides internationally certified occupational safety equipment for factories, contractors, and institutions across Jordan at competitive prices.')
        ),
        'faqs': [
            {
                'question': 'ما هي معدات السلامة الإلزامية في المواقع الإنشائية في الأردن؟',
                'question_en': 'What safety equipment is mandatory at construction sites in Jordan?',
                'answer': 'في المواقع الإنشائية الأردنية يجب توفير: خوذة سلامة، حذاء سلامة بمقدمة حديدية، سترة عاكسة، ونظارات حماية كحد أدنى. عند العمل على ارتفاع يُضاف حزام أمان. في أعمال اللحام يُضاف قناع لحام وقفازات جلدية. ESCO توفر جميع هذه المعدات بمعايير دولية.',
                'answer_en': 'At Jordanian construction sites, minimum requirements are: safety helmet, steel-toe boots, reflective vest, and safety glasses. Working at height requires a safety harness. Welding requires a welding mask and leather gloves. ESCO provides all these to international standards.',
            },
            {
                'question': 'كم مرة يجب استبدال معدات السلامة؟',
                'question_en': 'How often should safety equipment be replaced?',
                'answer': 'تعتمد فترة الاستبدال على نوع المعدة: الخوذات كل 3-5 سنوات أو فوراً عند تعرضها لصدمة. القفازات عند ظهور تآكل أو ثقوب. الأحذية كل سنة للاستخدام اليومي الكثيف. أحزمة الأمان يجب فحصها كل 6 أشهر واستبدالها بعد أي حادثة سقوط.',
                'answer_en': 'Replacement depends on the type: helmets every 3-5 years or immediately after impact. Gloves when showing wear or holes. Shoes annually for heavy daily use. Harnesses should be inspected every 6 months and replaced after any fall incident.',
            },
        ],
    },

    # ─── POST 5: Measuring Tools ───
    {
        'title': 'أدوات القياس الدقيقة - دليل أجهزة القياس للمهندسين في الأردن',
        'title_en': 'Precision Measuring Tools - Guide for Engineers in Jordan',
        'slug': 'measuring-tools-guide-jordan',
        'category_slug': 'measuring-tools',
        'tags': ['أدوات قياس', 'شريط قياس', 'ميزان ليزر', 'عدد صناعية', 'الأردن'],
        'excerpt': 'دليل شامل لأدوات القياس الدقيقة في الأردن. أجهزة ليزر، أمتار، فرجار، ملتيميتر وأجهزة فحص كهربائية للمهندسين والفنيين.',
        'excerpt_en': 'Complete guide to precision measuring tools in Jordan. Laser devices, tape measures, calipers, multimeters for engineers and technicians.',
        'card_icon': 'fa-ruler-combined',
        'card_icon_color': '#7c3aed',
        'meta_title': 'أدوات القياس - أجهزة قياس دقيقة للمهندسين | ESCO الأردن',
        'meta_description': 'أدوات قياس دقيقة في الأردن. أجهزة ليزر، أمتار، فرجار، ملتيميتر. للمهندسين والفنيين من مستودعات الهندسة ESCO.',
        'meta_keywords': 'أدوات قياس, جهاز ليزر, ميزان ليزر, شريط قياس, فرجار, ملتيميتر, أدوات قياس كهربائية, الأردن',
        'content': (
            _h2('أهمية أدوات القياس في الأعمال الهندسية') +
            _p('الدقة في القياس هي أساس نجاح أي مشروع هندسي أو صناعي. سواء كنت مهندساً مدنياً يعمل على مشروع بناء، أو فنياً كهربائياً يتعامل مع دوائر كهربائية، أو نجاراً يحتاج لقطع دقيق - أدوات القياس الصحيحة هي مفتاح الجودة. خطأ في القياس بملليمترات قليلة قد يكلف آلاف الدنانير في إعادة العمل.') +

            _h2('أنواع أدوات القياس') +

            _h3('أدوات قياس الطول والمسافة') +
            _ul([
                '<strong>شريط القياس (المتر):</strong> أداة أساسية بأطوال 3 إلى 10 أمتار. اختر نوعاً متيناً بشريط عريض (25 ملم) مع قفل',
                '<strong>جهاز القياس بالليزر:</strong> يقيس المسافات بدقة عالية حتى 100 متر بضغطة زر. مثالي للمهندسين والمساحين',
                '<strong>المسطرة المعدنية والزاوية:</strong> لقياسات قصيرة ودقيقة في الورش',
                '<strong>عجلة القياس:</strong> لقياس المسافات الطويلة في المواقع المفتوحة',
            ]) +

            _h3('أدوات التسوية والاستقامة') +
            _ul([
                '<strong>ميزان الماء (المستوى):</strong> للتأكد من استقامة الأسطح أفقياً وعمودياً',
                '<strong>ميزان الليزر:</strong> يُسقط خطوطاً ليزرية أفقية وعمودية بدقة عالية. ضروري لأعمال التبليط والديكور',
                '<strong>ميزان الخيط (الشاقول):</strong> لفحص العمودية في أعمال البناء',
            ]) +

            _h3('أدوات القياس الدقيقة') +
            _ul([
                '<strong>الفرجار (القدمة ذات الورنية):</strong> لقياس السماكة والأقطار بدقة 0.02 ملم',
                '<strong>الميكرومتر:</strong> لقياسات أكثر دقة حتى 0.001 ملم',
                '<strong>مقياس العمق:</strong> لقياس عمق الثقوب والأخاديد',
                '<strong>مقياس السماكة (فيلر جيج):</strong> لقياس الفراغات الضيقة',
            ]) +

            _h3('أجهزة القياس الكهربائية') +
            _ul([
                '<strong>الملتيميتر الرقمي:</strong> لقياس الجهد والتيار والمقاومة. أداة لا غنى عنها لأي كهربائي',
                '<strong>جهاز فحص العزل (الميجر):</strong> لفحص عزل الأسلاك والمحركات',
                '<strong>كلامب ميتر:</strong> لقياس التيار بدون فصل الدائرة',
                '<strong>فاحص الطور:</strong> للتأكد من وجود الكهرباء وتحديد الأطوار',
            ]) +

            _h2('كيف تختار أدوات القياس المناسبة؟') +
            _p('اختيار أدوات القياس يعتمد على تخصصك ونوع العمل. المهندس المدني يحتاج ميزان ليزر وجهاز قياس مسافة بالليزر. الكهربائي يحتاج ملتيميتر وكلامب ميتر. الميكانيكي يحتاج فرجار وميكرومتر. في ESCO نوفر أدوات قياس لجميع التخصصات.') +

            _h2('أدوات القياس من ESCO') +
            _p('مستودعات الهندسة ESCO هي وجهتك الأولى لأدوات القياس الدقيقة في الأردن. نوفر أجهزة من أفضل الماركات العالمية بضمان رسمي، ونخدم المهندسين والشركات والمصانع بأسعار تنافسية وخدمة متميزة.')
        ),
        'content_en': (
            _h2('Importance of Measuring Tools in Engineering') +
            _p('Precision in measurement is the foundation of any successful engineering or industrial project. The right measuring tools are key to quality work.') +
            _h2('Types of Measuring Tools') +
            _p('Including tape measures, laser distance meters, levels (spirit and laser), precision calipers, micrometers, digital multimeters, insulation testers, and clamp meters.') +
            _h2('Measuring Tools from ESCO') +
            _p('ESCO Engineering Stores is your first destination for precision measuring tools in Jordan, offering top global brands with official warranty.')
        ),
        'faqs': [
            {
                'question': 'ما هو أفضل جهاز قياس مسافة بالليزر للمهندسين؟',
                'question_en': 'What is the best laser distance meter for engineers?',
                'answer': 'للمهندسين المحترفين نوصي بأجهزة بوش GLM أو ليكا ديستو. توفر دقة ±1.5 ملم ومدى حتى 100 متر. تتميز بوظائف حساب المساحة والحجم والمسافة غير المباشرة. متوفرة في ESCO بضمان رسمي.',
                'answer_en': 'For professional engineers, we recommend Bosch GLM or Leica Disto devices. They offer ±1.5mm accuracy and range up to 100m with area, volume, and indirect measurement functions. Available at ESCO with official warranty.',
            },
        ],
    },

    # ─── POST 6: Lifting Equipment ───
    {
        'title': 'معدات الرفع والنقل الصناعي في الأردن - رافعات وونشات',
        'title_en': 'Industrial Lifting and Transport Equipment in Jordan',
        'slug': 'lifting-transport-equipment-jordan',
        'category_slug': 'lifting-transport',
        'tags': ['معدات رفع', 'رافعة هيدروليكية', 'عدد صناعية', 'مصانع', 'الأردن'],
        'excerpt': 'دليل شامل لمعدات الرفع والنقل في الأردن. رافعات هيدروليكية، ونشات كهربائية، سلاسل رفع، عربات نقل للمصانع والمستودعات.',
        'excerpt_en': 'Complete guide to lifting and transport equipment in Jordan. Hydraulic jacks, electric hoists, lifting chains, trolleys for factories.',
        'card_icon': 'fa-dolly',
        'card_icon_color': '#0891b2',
        'meta_title': 'معدات الرفع والنقل - رافعات صناعية الأردن | ESCO',
        'meta_description': 'معدات رفع ونقل صناعي في الأردن. رافعات هيدروليكية، ونشات، سلاسل رفع، جكات من ESCO مستودعات الهندسة.',
        'meta_keywords': 'معدات رفع, رافعة هيدروليكية, ونش كهربائي, سلاسل رفع, جك, عربة نقل, الأردن',
        'content': (
            _h2('أنواع معدات الرفع والنقل الصناعي') +
            _p('تُعد معدات الرفع والنقل من العناصر الأساسية في أي مصنع أو مستودع أو موقع إنشائي في الأردن. تساهم في رفع كفاءة العمل وتقليل مخاطر الإصابات الناتجة عن الرفع اليدوي للأحمال الثقيلة.') +

            _h3('الرافعات الهيدروليكية (الجكات)') +
            _p('تتوفر بعدة أنواع: جكات أرضية (2-20 طن) لرفع المركبات والمعدات، جكات زجاجية محمولة للاستخدام الميداني، وجكات هيدروليكية صناعية للأحمال الثقيلة في المصانع.') +

            _h3('الونشات والروافع') +
            _ul([
                '<strong>ونش كهربائي:</strong> لرفع الأحمال حتى 5 طن في المستودعات والمصانع',
                '<strong>ونش يدوي (جنزير):</strong> لرفع الأحمال في الأماكن التي لا تتوفر فيها كهرباء',
                '<strong>ونش سلكي:</strong> للأحمال الثقيلة جداً والمسافات الطويلة',
                '<strong>رافعة شوكية يدوية:</strong> لنقل البضائع على الطبالي في المستودعات',
            ]) +

            _h3('سلاسل وأحزمة الرفع') +
            _p('سلاسل الرفع المعايرة وأحزمة الرفع النسيجية ضرورية لعمليات الرفع الآمنة. يجب أن تكون معتمدة ومفحوصة دورياً حسب معايير السلامة الدولية.') +

            _h3('عربات النقل') +
            _p('تشمل عربات يدوية للتحميل، عربات منصة، وعربات متخصصة لنقل الأسطوانات والبراميل. أساسية في المستودعات والمصانع.') +

            _h2('معايير السلامة لمعدات الرفع') +
            _p('يجب فحص جميع معدات الرفع دورياً بواسطة فني مؤهل. تشمل الفحوصات: سلامة السلاسل والأسلاك، عمل الفرامل والمكابح، سلامة الخطافات، واختبار التحميل الدوري.') +

            _h2('معدات الرفع من ESCO') +
            _p('نوفر في مستودعات الهندسة ESCO تشكيلة واسعة من معدات الرفع والنقل المعتمدة دولياً. من الرافعات الهيدروليكية البسيطة إلى الونشات الكهربائية الثقيلة. خدمة ما بعد البيع وقطع الغيار متوفرة لجميع المنتجات.')
        ),
        'content_en': (
            _h2('Types of Industrial Lifting and Transport Equipment') +
            _p('Lifting and transport equipment are essential in any factory, warehouse, or construction site in Jordan. They improve efficiency and reduce injury risks from manual heavy lifting.') +
            _h2('Lifting Equipment from ESCO') +
            _p('ESCO Engineering Stores provides internationally certified lifting and transport equipment with after-sales service and spare parts for all products.')
        ),
        'faqs': [
            {
                'question': 'ما هي أنواع الرافعات الهيدروليكية المتوفرة في ESCO؟',
                'question_en': 'What types of hydraulic jacks are available at ESCO?',
                'answer': 'نوفر في ESCO: جكات أرضية (2-20 طن)، جكات زجاجية محمولة (2-50 طن)، جكات تمساح طويلة للمعدات المنخفضة، ورافعات هيدروليكية صناعية. جميعها بضمان ومعتمدة للاستخدام الصناعي في الأردن.',
                'answer_en': 'ESCO offers floor jacks (2-20 ton), bottle jacks (2-50 ton), long-reach jacks for low equipment, and industrial hydraulic lifts. All with warranty and certified for industrial use in Jordan.',
            },
        ],
    },

    # ─── POST 7: Compressors and Generators ───
    {
        'title': 'كمبريسورات ومولدات كهربائية - دليل الشراء في الأردن',
        'title_en': 'Compressors and Generators - Buying Guide for Jordan',
        'slug': 'compressors-generators-guide-jordan',
        'category_slug': 'power-tools',
        'tags': ['كمبريسور', 'مولد كهربائي', 'عدد صناعية', 'ورش صناعية', 'الأردن'],
        'excerpt': 'دليل اختيار الكمبريسور والمولد الكهربائي المناسب في الأردن. أنواعها وأحجامها واستخداماتها في الورش والمصانع.',
        'excerpt_en': 'Guide to choosing the right compressor and generator in Jordan. Types, sizes, and applications for workshops and factories.',
        'card_icon': 'fa-fan',
        'card_icon_color': '#475569',
        'meta_title': 'كمبريسورات ومولدات كهربائية الأردن | ESCO مستودعات الهندسة',
        'meta_description': 'كمبريسورات هواء ومولدات كهربائية في الأردن. أنواع وأحجام مختلفة للورش والمصانع. أسعار تنافسية من ESCO.',
        'meta_keywords': 'كمبريسور, كمبريسور هواء, مولد كهربائي, جنريتور, ضاغط هواء, الأردن',
        'content': (
            _h2('كمبريسورات الهواء - أنواعها واستخداماتها') +
            _p('كمبريسور الهواء أو ضاغط الهواء من المعدات الأساسية في الورش الصناعية في الأردن. يُستخدم لتشغيل العدد الهوائية كالمسدسات والصنافر والرشاشات، وفي أعمال النفخ والتنظيف وتعبئة الإطارات.') +

            _h3('أنواع الكمبريسورات') +
            _ul([
                '<strong>كمبريسور مكبسي (Piston):</strong> الأكثر شيوعاً في الورش. يتوفر بأحجام 24 إلى 500 لتر',
                '<strong>كمبريسور لولبي (Screw):</strong> للاستخدام الصناعي المستمر في المصانع',
                '<strong>كمبريسور بدون زيت (Oil-Free):</strong> للتطبيقات التي تتطلب هواءً نظيفاً كالدهان والطعام',
                '<strong>كمبريسور محمول:</strong> للاستخدام في المواقع والأعمال الميدانية',
            ]) +

            _h2('المولدات الكهربائية') +
            _p('المولدات الكهربائية ضرورية كمصدر طاقة احتياطي للمصانع والمواقع الإنشائية في الأردن. تتوفر بقدرات مختلفة:') +
            _ul([
                '<strong>مولدات بنزين صغيرة (2-8 كيلوواط):</strong> للاستخدام المنزلي والورش الصغيرة',
                '<strong>مولدات ديزل متوسطة (10-50 كيلوواط):</strong> للورش الكبيرة والمواقع الإنشائية',
                '<strong>مولدات ديزل كبيرة (50-500+ كيلوواط):</strong> للمصانع والمنشآت الصناعية',
            ]) +

            _h2('نصائح اختيار الكمبريسور والمولد') +
            _ol([
                'حدد الاستخدام وعدد الأدوات التي ستعمل عليها في نفس الوقت',
                'احسب استهلاك الهواء أو الكهرباء المطلوب',
                'اختر حجماً أكبر بـ 25% من احتياجك الفعلي كاحتياطي',
                'تأكد من توفر الصيانة وقطع الغيار محلياً',
                'اختر ماركة موثوقة بضمان رسمي',
            ]) +

            _h2('كمبريسورات ومولدات من ESCO') +
            _p('مستودعات الهندسة ESCO توفر تشكيلة واسعة من الكمبريسورات والمولدات الكهربائية للورش والمصانع في الأردن. نوفر الاستشارة الفنية لمساعدتك في اختيار الجهاز المناسب مع خدمة التوصيل والتركيب والصيانة الدورية.')
        ),
        'content_en': (
            _h2('Air Compressors - Types and Applications') +
            _p('Air compressors are essential equipment in Jordan\'s industrial workshops, used to power pneumatic tools, painting, cleaning, and tire inflation.') +
            _h2('Electric Generators') +
            _p('Generators are essential as backup power for factories and construction sites in Jordan, available in various capacities from 2kW portable units to 500kW+ industrial units.') +
            _h2('Compressors and Generators from ESCO') +
            _p('ESCO offers a wide range with technical consultation, delivery, installation, and maintenance services.')
        ),
        'faqs': [
            {
                'question': 'ما حجم الكمبريسور المناسب لورشة حدادة في الأردن؟',
                'question_en': 'What compressor size is suitable for a blacksmith workshop in Jordan?',
                'answer': 'لورشة حدادة متوسطة تستخدم صاروخ قص وأدوات هوائية، تحتاج كمبريسور بسعة 200-300 لتر وقوة 3-5 حصان على الأقل. إذا كنت تستخدم عدة أدوات في نفس الوقت، اختر 500 لتر. زُر ESCO للاستشارة الفنية المجانية.',
                'answer_en': 'For a medium blacksmith workshop using grinders and pneumatic tools, you need a 200-300 liter, 3-5 HP compressor minimum. For multiple simultaneous tools, choose 500 liters. Visit ESCO for free technical consultation.',
            },
        ],
    },

    # ─── POST 8: Bosch vs Makita vs DeWalt ───
    {
        'title': 'مقارنة بوش وماكيتا وديوالت - أيهم الأفضل للعدد الكهربائية؟',
        'title_en': 'Bosch vs Makita vs DeWalt - Which is Best for Power Tools?',
        'slug': 'bosch-vs-makita-vs-dewalt-comparison',
        'category_slug': 'buying-guides',
        'tags': ['بوش', 'ماكيتا', 'ديوالت', 'أدوات كهربائية', 'عدد صناعية', 'الأردن'],
        'excerpt': 'مقارنة شاملة بين أشهر ثلاث ماركات للعدد الكهربائية في الأردن: بوش الألمانية، ماكيتا اليابانية، وديوالت الأمريكية.',
        'excerpt_en': 'Comprehensive comparison of the top three power tool brands in Jordan: Bosch (Germany), Makita (Japan), and DeWalt (USA).',
        'card_icon': 'fa-balance-scale',
        'card_icon_color': '#0d9488',
        'meta_title': 'مقارنة بوش وماكيتا وديوالت - أفضل عدد كهربائية | ESCO',
        'meta_description': 'مقارنة شاملة بين بوش، ماكيتا، وديوالت في الأردن. المميزات والعيوب والأسعار لكل ماركة من مستودعات الهندسة ESCO.',
        'meta_keywords': 'بوش مقابل ماكيتا, بوش مقابل ديوالت, أفضل ماركة عدد كهربائية, مقارنة عدد, الأردن',
        'content': (
            _h2('لماذا المقارنة مهمة قبل الشراء؟') +
            _p('عند شراء عدد كهربائية في الأردن، يواجه المحترفون والهواة سؤالاً شائعاً: أي ماركة أختار؟ بوش الألمانية، ماكيتا اليابانية، أم ديوالت الأمريكية؟ كل ماركة لها نقاط قوة وتخصصات مختلفة. في هذا الدليل من ESCO نقدم مقارنة موضوعية لمساعدتك.') +

            _h2('بوش (Bosch) - الهندسة الألمانية') +
            _h3('نقاط القوة') +
            _ul([
                'تكنولوجيا متقدمة وابتكارات مستمرة',
                'خطان متخصصان: الأزرق للمحترفين والأخضر للمنزل',
                'أفضل أدوات قياس في السوق (أجهزة ليزر)',
                'نظام بطاريات 18V موحد عبر جميع الأدوات',
                'ضمان رسمي ممتد وخدمة عملاء ممتازة في الأردن',
            ]) +
            _h3('الأنسب لـ') +
            _p('المهندسين والفنيين الذين يحتاجون دقة وتكنولوجيا متقدمة. أعمال التمديدات الكهربائية والسباكة والنجارة الدقيقة.') +

            _h2('ماكيتا (Makita) - الموثوقية اليابانية') +
            _h3('نقاط القوة') +
            _ul([
                'أكبر مجموعة أدوات لاسلكية على منصة 18V LXT (أكثر من 200 أداة)',
                'محركات Brushless بدون فحم لعمر أطول وكفاءة أعلى',
                'خفة الوزن وتوازن ممتاز في التصميم',
                'سمعة ممتازة في المتانة والموثوقية',
                'سعر تنافسي مقارنة بالجودة المقدمة',
            ]) +
            _h3('الأنسب لـ') +
            _p('النجارين والعاملين في تشطيب المباني. من يحتاج أدوات خفيفة للعمل لساعات طويلة. الورش التي تحتاج تنوعاً كبيراً في الأدوات.') +

            _h2('ديوالت (DeWalt) - القوة الأمريكية') +
            _h3('نقاط القوة') +
            _ul([
                'أقوى عزم دوران في فئتها - مثالية للأعمال الثقيلة',
                'نظام بطاريات FlexVolt (20V/60V) الأقوى في السوق',
                'متانة استثنائية تتحمل ظروف العمل القاسية في المواقع',
                'حقائب تخزين TSTAK المتينة ونظام تنظيم متكامل',
                'خيار مفضل لشركات المقاولات والمشاريع الكبيرة',
            ]) +
            _h3('الأنسب لـ') +
            _p('شركات المقاولات والبناء. من يحتاج أدوات تتحمل الاستخدام القاسي يومياً. المشاريع الكبيرة التي تتطلب قوة وأداء عالي.') +

            _h2('جدول المقارنة السريع') +
            '<table><thead><tr><th>المعيار</th><th>بوش</th><th>ماكيتا</th><th>ديوالت</th></tr></thead><tbody>' +
            '<tr><td>بلد المنشأ</td><td>ألمانيا</td><td>اليابان</td><td>أمريكا</td></tr>' +
            '<tr><td>السعر</td><td>مرتفع</td><td>متوسط-مرتفع</td><td>مرتفع</td></tr>' +
            '<tr><td>المتانة</td><td>ممتازة</td><td>ممتازة</td><td>استثنائية</td></tr>' +
            '<tr><td>التكنولوجيا</td><td>الأفضل</td><td>متقدمة</td><td>جيدة جداً</td></tr>' +
            '<tr><td>تنوع الأدوات</td><td>واسع</td><td>الأوسع</td><td>واسع</td></tr>' +
            '<tr><td>خفة الوزن</td><td>جيدة</td><td>الأفضل</td><td>جيدة</td></tr>' +
            '<tr><td>القوة</td><td>ممتازة</td><td>ممتازة</td><td>الأفضل</td></tr>' +
            '</tbody></table>' +

            _h2('الخلاصة - أيهم تختار؟') +
            _p('لا توجد ماركة "أفضل بالمطلق" - الأفضل هو ما يناسب احتياجاتك. في مستودعات الهندسة ESCO نوفر الماركات الثلاث بضمان رسمي، ويسعد فريقنا مساعدتك في اختيار الأنسب لعملك وميزانيتك. زُرنا في أي من فروعنا في عمان أو تسوق عبر موقعنا esco.jo.')
        ),
        'content_en': (
            _h2('Why Comparison Matters Before Buying') +
            _p('When buying power tools in Jordan, professionals face a common question: Bosch, Makita, or DeWalt? Each brand has unique strengths.') +
            _h2('Bosch - German Engineering') +
            _p('Advanced technology, two professional lines (Blue/Green), best measuring tools, unified 18V battery system.') +
            _h2('Makita - Japanese Reliability') +
            _p('Largest 18V cordless range (200+ tools), brushless motors, lightweight design, excellent value.') +
            _h2('DeWalt - American Power') +
            _p('Strongest torque, FlexVolt battery system, exceptional durability for tough conditions.') +
            _h2('Conclusion') +
            _p('ESCO carries all three brands with official warranty. Visit us in Amman or shop at esco.jo for expert advice.')
        ),
        'faqs': [
            {
                'question': 'أيهم أفضل بوش أم ماكيتا في الأردن؟',
                'question_en': 'Which is better, Bosch or Makita in Jordan?',
                'answer': 'كلاهما ممتاز. بوش أفضل في التكنولوجيا وأدوات القياس والدقة. ماكيتا أفضل في خفة الوزن وتنوع الأدوات اللاسلكية والسعر التنافسي. للنجارين ماكيتا غالباً أفضل، للكهربائيين بوش غالباً أنسب. زُر ESCO لتجربة الأداتين.',
                'answer_en': 'Both are excellent. Bosch excels in technology, measuring tools, and precision. Makita leads in lightweight design, cordless variety, and value. For carpenters, Makita is often preferred; for electricians, Bosch is typically better. Visit ESCO to try both.',
            },
            {
                'question': 'هل ديوالت متوفرة في الأردن مع ضمان؟',
                'question_en': 'Is DeWalt available in Jordan with warranty?',
                'answer': 'نعم، ديوالت متوفرة بالكامل في الأردن من خلال موزعين معتمدين مثل ESCO مستودعات الهندسة. جميع المنتجات بضمان رسمي مع توفر قطع الغيار وخدمة الصيانة.',
                'answer_en': 'Yes, DeWalt is fully available in Jordan through authorized distributors like ESCO Engineering Stores. All products come with official warranty, spare parts, and maintenance service.',
            },
        ],
    },

    # ─── POST 9: Cordless Tools ───
    {
        'title': 'العدد اللاسلكية (الشحن) - ثورة الأدوات الكهربائية في الأردن',
        'title_en': 'Cordless Power Tools - The Tool Revolution in Jordan',
        'slug': 'cordless-battery-tools-guide',
        'category_slug': 'power-tools',
        'tags': ['عدد شحن', 'عدد بطارية', 'أدوات كهربائية', 'بوش', 'ماكيتا', 'ديوالت', 'الأردن'],
        'excerpt': 'كل ما تحتاج معرفته عن العدد اللاسلكية القابلة للشحن. أنواع البطاريات، أفضل الماركات، ومتى تختار اللاسلكي بدل السلكي.',
        'excerpt_en': 'Everything about cordless rechargeable tools. Battery types, best brands, and when to choose cordless over corded.',
        'card_icon': 'fa-battery-full',
        'card_icon_color': '#16a34a',
        'meta_title': 'العدد اللاسلكية الشحن - أفضل أدوات بطارية الأردن | ESCO',
        'meta_description': 'دليل العدد اللاسلكية (الشحن) في الأردن. بطاريات ليثيوم، 18V، 20V. أفضل الماركات والأسعار من ESCO.',
        'meta_keywords': 'عدد لاسلكية, عدد شحن, دريل شحن, بطارية ليثيوم, 18V, 20V, أدوات لاسلكية, الأردن',
        'content': (
            _h2('لماذا العدد اللاسلكية؟') +
            _p('شهدت السنوات الأخيرة ثورة حقيقية في عالم العدد الكهربائية مع تطور تكنولوجيا البطاريات. أصبحت الأدوات اللاسلكية القابلة للشحن توفر قوة مماثلة للسلكية مع حرية حركة كاملة. في المواقع الإنشائية والأماكن التي لا تتوفر فيها كهرباء في الأردن، أصبحت هذه الأدوات ضرورة لا غنى عنها.') +

            _h2('أنواع البطاريات') +
            _h3('بطاريات الليثيوم أيون (Li-Ion)') +
            _p('الأكثر شيوعاً حالياً. خفيفة الوزن، لا تعاني من تأثير الذاكرة، تحتفظ بشحنتها لفترة طويلة. تتوفر بفولتيات 12V، 18V، 20V، و36V.') +

            _h3('نظام فولتية البطاريات') +
            _ul([
                '<strong>12 فولت:</strong> للأعمال الخفيفة والإلكترونيات. مثالي للاستخدام المنزلي',
                '<strong>18 فولت (20V MAX):</strong> المعيار المهني الأكثر شيوعاً. يغطي 90% من التطبيقات',
                '<strong>36 فولت (FlexVolt):</strong> للأعمال الثقيلة جداً. بديل حقيقي للأدوات السلكية الكبيرة',
            ]) +

            _h2('أشهر أنظمة البطاريات') +
            _ul([
                '<strong>بوش 18V Professional:</strong> نظام موحد يعمل مع جميع أدوات بوش الاحترافية',
                '<strong>ماكيتا 18V LXT:</strong> أكبر منصة أدوات لاسلكية مع أكثر من 200 أداة متوافقة',
                '<strong>ديوالت 20V MAX / FlexVolt:</strong> نظام فريد يتحول بين 20V و60V حسب الأداة',
            ]) +

            _h2('متى تختار اللاسلكي ومتى السلكي؟') +
            _p('اختر اللاسلكي عندما: تحتاج حرية الحركة، تعمل في مواقع بلا كهرباء، تنتقل كثيراً بين المواقع. اختر السلكي عندما: تحتاج قوة ثابتة لساعات متواصلة، تعمل في ورشة ثابتة، أو تستخدم أدوات ثقيلة جداً كصواريخ القص الكبيرة.') +

            _h2('عدد لاسلكية من ESCO') +
            _p('نوفر في مستودعات الهندسة ESCO أحدث العدد اللاسلكية من بوش وماكيتا وديوالت مع بطاريات أصلية وشواحن سريعة. نقدم أيضاً أطقم كومبو (عدة أدوات مع بطاريات) بأسعار مميزة للمحترفين.')
        ),
        'content_en': (
            _h2('Why Cordless Tools?') +
            _p('Cordless rechargeable tools now match corded tools in power while offering complete mobility. Essential for construction sites in Jordan.') +
            _h2('Battery Types and Voltage Systems') +
            _p('Modern Li-Ion batteries come in 12V (light duty), 18V/20V MAX (professional standard), and 36V/FlexVolt (heavy duty) platforms.') +
            _h2('Cordless Tools from ESCO') +
            _p('ESCO offers the latest cordless tools from Bosch, Makita, and DeWalt with original batteries and fast chargers, plus combo kits at special prices.')
        ),
        'faqs': [
            {
                'question': 'ما الفرق بين 18 فولت و20 فولت MAX؟',
                'question_en': 'What is the difference between 18V and 20V MAX?',
                'answer': 'في الحقيقة هما نفس الشيء تقريباً! 20V MAX هو قياس الجهد بدون حمل، بينما 18V هو الجهد الاسمي تحت الحمل. ديوالت تستخدم تسمية 20V MAX وماكيتا وبوش تستخدم 18V، لكن الأداء متماثل. لا تنخدع بالأرقام فقط.',
                'answer_en': 'They are essentially the same! 20V MAX is the no-load voltage, while 18V is the nominal voltage under load. DeWalt uses 20V MAX branding while Makita and Bosch use 18V, but performance is equivalent.',
            },
        ],
    },

    # ─── POST 10: Workshop Setup ───
    {
        'title': 'تجهيز ورشة صناعية متكاملة في الأردن - دليل المعدات والأدوات',
        'title_en': 'Setting Up a Complete Industrial Workshop in Jordan',
        'slug': 'industrial-workshop-setup-guide-jordan',
        'category_slug': 'buying-guides',
        'tags': ['ورش صناعية', 'عدد صناعية', 'مصانع', 'مقاولات', 'الأردن', 'عمان'],
        'excerpt': 'دليل شامل لتجهيز ورشة صناعية أو ورشة حدادة أو نجارة أو كهرباء في الأردن. قائمة كاملة بالمعدات والأدوات اللازمة.',
        'excerpt_en': 'Complete guide for setting up an industrial workshop in Jordan. Full list of required equipment and tools.',
        'card_icon': 'fa-industry',
        'card_icon_color': '#1e40af',
        'meta_title': 'تجهيز ورشة صناعية في الأردن - دليل المعدات الكامل | ESCO',
        'meta_description': 'دليل تجهيز ورشة صناعية متكاملة في الأردن. قوائم معدات لورش الحدادة والنجارة والكهرباء والسباكة من ESCO.',
        'meta_keywords': 'تجهيز ورشة, ورشة صناعية, معدات ورشة, ورشة حدادة, ورشة نجارة, ورشة كهرباء, الأردن',
        'content': (
            _h2('لماذا يحتاج تجهيز الورشة تخطيطاً دقيقاً؟') +
            _p('تجهيز ورشة صناعية في الأردن هو استثمار كبير يتطلب تخطيطاً دقيقاً لضمان كفاءة العمل وتحقيق أفضل عائد. الورشة المجهزة جيداً توفر الوقت والجهد وتقلل التكاليف على المدى الطويل. في هذا الدليل من مستودعات الهندسة ESCO، نقدم لك قوائم تجهيز شاملة لأنواع الورش المختلفة.') +

            _h2('تجهيز ورشة حدادة') +
            _ul([
                'ماكينة لحام كهربائي (200-300 أمبير)',
                'ماكينة لحام أرجون/MIG (اختياري للأعمال المتقدمة)',
                'صاروخ قص وجلخ 7 بوصة و4.5 بوصة',
                'منشار حديد (آلي أو يدوي)',
                'مثقاب عمودي (دريل بنش)',
                'كمبريسور هواء 200-300 لتر',
                'منقلة وملزمة حداد',
                'طقم مفاتيح وبوكسات',
                'أدوات قياس (شريط قياس، زاوية، مسطرة)',
                'معدات سلامة كاملة (قناع لحام، قفازات، حذاء سلامة)',
            ]) +

            _h2('تجهيز ورشة نجارة') +
            _ul([
                'منشار طاولة (Table Saw)',
                'منشار قص وتركيب (Miter Saw)',
                'فريزة (Router) مع طاولة',
                'منشار تخريقة (Jigsaw)',
                'صنفرة مدارية وحزامية',
                'دريل ومفك شحن',
                'مسحقة (Planer)',
                'كمبريسور صغير مع مسمار هوائي',
                'ملزمة نجار وطاولة عمل',
                'أدوات قياس دقيقة (شريط، زاوية، مسطرة T)',
            ]) +

            _h2('تجهيز ورشة كهرباء') +
            _ul([
                'ملتيميتر رقمي احترافي',
                'كلامب ميتر',
                'جهاز فحص عزل (ميجر)',
                'طقم مفكات معزولة (VDE)',
                'زراديات وكماشات كهربائية معزولة',
                'دريل شحن مع طقم ريش',
                'فاحص طور / فاحص مقابس',
                'أدوات تقشير وقص أسلاك',
                'سلم ألمنيوم مع عزل',
                'حقيبة عدة كهربائي متكاملة',
            ]) +

            _h2('معدات مشتركة لجميع الورش') +
            _ul([
                'طاولة عمل متينة',
                'إضاءة LED مناسبة',
                'تهوية وشفط مناسبة',
                'طفاية حريق',
                'صندوق إسعافات أولية',
                'لوحة كهرباء مع حماية تسريب (ELCB)',
            ]) +

            _h2('جهّز ورشتك من ESCO') +
            _p('مستودعات الهندسة ESCO هي شريكك المثالي لتجهيز ورشتك الصناعية في الأردن. نوفر جميع المعدات والأدوات من أفضل الماركات العالمية تحت سقف واحد. نقدم عروضاً خاصة لتجهيز الورش بالكامل مع خدمة الاستشارة الفنية المجانية والتوصيل. تواصل معنا لعرض سعر مخصص لمشروعك.')
        ),
        'content_en': (
            _h2('Workshop Setup Planning') +
            _p('Setting up an industrial workshop in Jordan requires careful planning. A well-equipped workshop saves time, effort, and costs.') +
            _h2('Equipment Lists') +
            _p('We provide complete equipment lists for blacksmith workshops, carpentry workshops, electrical workshops, and common shared equipment.') +
            _h2('Equip Your Workshop from ESCO') +
            _p('ESCO is your ideal partner for workshop setup in Jordan. We offer special packages with free technical consultation and delivery.')
        ),
        'faqs': [
            {
                'question': 'كم تكلفة تجهيز ورشة حدادة في الأردن؟',
                'question_en': 'How much does it cost to set up a blacksmith workshop in Jordan?',
                'answer': 'تعتمد التكلفة على حجم الورشة ونوعية المعدات. ورشة حدادة أساسية يمكن تجهيزها بـ 3,000-5,000 دينار. ورشة متوسطة متكاملة من 8,000-15,000 دينار. ورشة كبيرة احترافية من 20,000 دينار فأكثر. ESCO تقدم عروض تجهيز شاملة بأسعار منافسة.',
                'answer_en': 'Cost depends on workshop size and equipment quality. Basic workshop: 3,000-5,000 JOD. Medium complete workshop: 8,000-15,000 JOD. Large professional: 20,000+ JOD. ESCO offers comprehensive setup packages at competitive prices.',
            },
        ],
    },

    # ─── POST 11: Plumbing Tools ───
    {
        'title': 'أدوات السباكة الاحترافية - دليل السباك في الأردن',
        'title_en': 'Professional Plumbing Tools - Plumber\'s Guide in Jordan',
        'slug': 'plumbing-tools-guide-jordan',
        'category_slug': 'plumbing-tools',
        'tags': ['أدوات سباكة', 'عدد يدوية', 'عدد صناعية', 'الأردن'],
        'excerpt': 'دليل شامل لأدوات السباكة في الأردن. مفاتيح أنابيب، قواطع مواسير، أدوات لحام مواسير، وكل ما يحتاجه السباك المحترف.',
        'excerpt_en': 'Complete guide to plumbing tools in Jordan. Pipe wrenches, pipe cutters, soldering tools, and everything a professional plumber needs.',
        'card_icon': 'fa-faucet',
        'card_icon_color': '#0ea5e9',
        'meta_title': 'أدوات السباكة في الأردن - عدد سباكة احترافية | ESCO',
        'meta_description': 'أدوات سباكة احترافية في الأردن. مفاتيح أنابيب، قواطع مواسير، لوازم تمديدات صحية من ESCO مستودعات الهندسة.',
        'meta_keywords': 'أدوات سباكة, مفتاح أنابيب, قاطع مواسير, عدد سباك, تمديدات صحية, الأردن',
        'content': (
            _h2('الأدوات الأساسية لكل سباك في الأردن') +
            _p('السباكة من المهن الأساسية في الأردن، سواء في البناء الجديد أو أعمال الصيانة. يحتاج السباك المحترف إلى مجموعة متنوعة من الأدوات لإنجاز عمله بكفاءة وجودة.') +

            _h3('مفاتيح الأنابيب') +
            _p('مفتاح الأنابيب (البايب رنش) هو الأداة الرئيسية للسباك. يتوفر بأحجام مختلفة من 8 بوصة إلى 36 بوصة. النوع الأمريكي الثقيل (Ridgid) هو المعيار المهني.') +

            _h3('قواطع المواسير') +
            _p('تشمل قواطع المواسير النحاسية والحديدية وقواطع مواسير PPR والPVC. تتوفر بأنواع يدوية وكهربائية حسب قطر الماسورة وكمية العمل.') +

            _h3('أدوات اللحام والتسنين') +
            _p('أدوات لحام المواسير النحاسية (شعلة غاز ولحام فضة)، أجهزة لحام مواسير PPR الحرارية، وأدوات تسنين المواسير الحديدية.') +

            _h2('أدوات السباكة المتخصصة') +
            _ul([
                '<strong>سوستة تسليك:</strong> لفتح المجاري المسدودة',
                '<strong>كاميرا فحص مجاري:</strong> لتشخيص مشاكل الصرف',
                '<strong>جهاز فحص تسريب:</strong> لكشف تسريبات المياه داخل الجدران',
                '<strong>مضخة ضغط اختبار:</strong> لاختبار شبكة المياه قبل التشغيل',
                '<strong>ثني مواسير:</strong> لثني المواسير بزوايا دقيقة',
            ]) +

            _h2('أدوات السباكة من ESCO') +
            _p('مستودعات الهندسة ESCO توفر أشمل تشكيلة من أدوات ولوازم السباكة في الأردن. من المفاتيح والقواطع إلى أجهزة اللحام والفحص. أدوات أصلية بضمان وأسعار منافسة لجميع السباكين والشركات.')
        ),
        'content_en': (
            _h2('Essential Tools for Every Plumber in Jordan') +
            _p('Plumbing tools include pipe wrenches, pipe cutters, PPR welding machines, threading tools, drain snakes, and testing equipment.') +
            _h2('Plumbing Tools from ESCO') +
            _p('ESCO provides the most comprehensive range of plumbing tools in Jordan, from basic wrenches to specialized testing equipment.')
        ),
        'faqs': [
            {
                'question': 'ما هي أدوات السباكة الأساسية التي يحتاجها كل سباك؟',
                'question_en': 'What are the essential plumbing tools every plumber needs?',
                'answer': 'يحتاج كل سباك إلى: مفاتيح أنابيب (12 و18 بوصة)، قاطع مواسير، شريط تيفلون، مفاتيح ربط، زرادية ماء (ووتر بمب)، مستوى، شريط قياس، ومنشار حديد صغير. للتخصص في PPR يحتاج جهاز لحام حراري. جميعها متوفرة في ESCO.',
                'answer_en': 'Every plumber needs: pipe wrenches (12" and 18"), pipe cutter, Teflon tape, wrenches, water pump pliers, level, tape measure, and small hacksaw. For PPR specialization, a thermal welding machine. All available at ESCO.',
            },
        ],
    },

    # ─── POST 12: Electrical Tools ───
    {
        'title': 'عدد وأدوات الكهربائي - دليل شامل لفنيي الكهرباء في الأردن',
        'title_en': 'Electrician Tools - Complete Guide for Electrical Technicians in Jordan',
        'slug': 'electrician-tools-guide-jordan',
        'category_slug': 'electrical-tools',
        'tags': ['أدوات كهربائي', 'عدد صناعية', 'أدوات كهربائية', 'الأردن'],
        'excerpt': 'دليل أدوات الكهربائي الاحترافي في الأردن. ملتيميتر، مفكات معزولة، زراديات كهربائية، وأجهزة فحص التمديدات.',
        'excerpt_en': 'Professional electrician tools guide in Jordan. Multimeters, insulated screwdrivers, electrical pliers, and testing devices.',
        'card_icon': 'fa-plug',
        'card_icon_color': '#eab308',
        'meta_title': 'أدوات الكهربائي - عدد كهربائية للفنيين | ESCO الأردن',
        'meta_description': 'أدوات الكهربائي في الأردن. ملتيميتر، مفكات VDE معزولة، أجهزة فحص كهربائية من مستودعات الهندسة ESCO.',
        'meta_keywords': 'أدوات كهربائي, ملتيميتر, مفكات معزولة, أجهزة فحص كهربائية, عدد كهربائي, VDE, الأردن',
        'content': (
            _h2('أدوات الكهربائي الأساسية') +
            _p('يتطلب عمل الكهربائي في الأردن مجموعة متخصصة من الأدوات التي توفر الأمان والدقة. سلامة الكهربائي ومن حوله تعتمد بشكل كبير على جودة أدواته وعزلها الكهربائي.') +

            _h3('أجهزة القياس والفحص الكهربائي') +
            _ul([
                '<strong>ملتيميتر رقمي:</strong> لقياس الجهد (AC/DC) والتيار والمقاومة والاستمرارية. أداة لا غنى عنها',
                '<strong>كلامب ميتر:</strong> لقياس التيار بدون فصل الدائرة. ضروري لأعمال الصيانة',
                '<strong>فاحص الطور / قلم فحص:</strong> للتأكد من وجود الكهرباء بسرعة وأمان',
                '<strong>ميجر (فاحص عزل):</strong> لفحص عزل الأسلاك والمحركات والمحولات',
                '<strong>فاحص مقابس:</strong> للتأكد من صحة توصيل المقابس الكهربائية',
            ]) +

            _h3('مفكات كهربائية معزولة (VDE)') +
            _p('المفكات المعزولة وفق معيار VDE تحمي الكهربائي حتى جهد 1000 فولت. يجب أن يمتلك الكهربائي مجموعة كاملة من المفكات المعزولة بأحجام مختلفة (مسطح وصليبي).') +

            _h3('زراديات وكماشات كهربائية') +
            _ul([
                '<strong>كماشة قطع أسلاك معزولة:</strong> لقطع الأسلاك بأمان',
                '<strong>زرادية طويلة الأنف معزولة:</strong> للعمل في الأماكن الضيقة',
                '<strong>أداة تقشير أسلاك:</strong> لإزالة العزل عن نهايات الأسلاك',
                '<strong>كبّاسة أطراف أسلاك (كريمبر):</strong> لتركيب الأطراف والكوسات',
            ]) +

            _h2('أدوات الكهربائي من ESCO') +
            _p('مستودعات الهندسة ESCO توفر جميع أدوات الكهربائي من أفضل الماركات العالمية المعتمدة. جميع أدوات العزل معتمدة VDE/IEC. نخدم فنيي الكهرباء والشركات والمقاولين في جميع أنحاء الأردن.')
        ),
        'content_en': (
            _h2('Essential Electrician Tools') +
            _p('Electrician work in Jordan requires specialized tools that ensure safety and precision, including digital multimeters, clamp meters, insulated screwdrivers (VDE), insulated pliers, wire strippers, and crimping tools.') +
            _h2('Electrician Tools from ESCO') +
            _p('ESCO provides all VDE/IEC certified electrician tools from top global brands for technicians and contractors across Jordan.')
        ),
        'faqs': [
            {
                'question': 'ما هو أفضل ملتيميتر لفنيي الكهرباء في الأردن؟',
                'question_en': 'What is the best multimeter for electricians in Jordan?',
                'answer': 'للفنيين المحترفين نوصي بملتيميترات Fluke أو UNI-T من الفئة CAT III/CAT IV. توفر دقة عالية وحماية من التيار الزائد. أجهزة Fluke 117 أو 179 ممتازة للكهربائيين. متوفرة في ESCO مع ضمان.',
                'answer_en': 'For professionals, we recommend Fluke or UNI-T multimeters rated CAT III/CAT IV. Fluke 117 or 179 are excellent for electricians. Available at ESCO with warranty.',
            },
        ],
    },

    # ─── POST 13: Tool Maintenance ───
    {
        'title': 'صيانة العدد الكهربائية واليدوية - نصائح لإطالة عمر أدواتك',
        'title_en': 'Power and Hand Tool Maintenance - Tips to Extend Tool Life',
        'slug': 'tool-maintenance-tips-guide',
        'category_slug': 'maintenance-care',
        'tags': ['عدد صناعية', 'أدوات كهربائية', 'عدد يدوية', 'الأردن'],
        'excerpt': 'نصائح عملية لصيانة العدد الكهربائية واليدوية والحفاظ عليها. كيف تحافظ على أدواتك وتطيل عمرها وتضمن أداءها الأمثل.',
        'excerpt_en': 'Practical tips for maintaining power and hand tools. How to care for your tools, extend their life, and ensure optimal performance.',
        'card_icon': 'fa-tools',
        'card_icon_color': '#64748b',
        'meta_title': 'صيانة العدد والأدوات - نصائح للحفاظ على أدواتك | ESCO',
        'meta_description': 'نصائح صيانة العدد الكهربائية واليدوية. كيف تحافظ على أدواتك وتطيل عمرها من خبراء مستودعات الهندسة ESCO.',
        'meta_keywords': 'صيانة أدوات, صيانة عدد كهربائية, العناية بالأدوات, نصائح صيانة, عدد صناعية',
        'content': (
            _h2('لماذا صيانة الأدوات مهمة؟') +
            _p('الأدوات الجيدة استثمار كبير. الصيانة المنتظمة تحافظ على أدائها وتطيل عمرها وتمنع الأعطال المفاجئة. أداة بقيمة 100 دينار مع صيانة جيدة تدوم سنوات أكثر من أداة بقيمة 200 دينار بدون صيانة.') +

            _h2('صيانة العدد الكهربائية') +
            _ol([
                '<strong>نظّف الأداة بعد كل استخدام:</strong> أزل الغبار والنشارة باستخدام هواء مضغوط',
                '<strong>افحص الكربون (الفحم):</strong> استبدل فحمات المحرك عند تآكلها لتجنب تلف المحرك',
                '<strong>تحقق من الكابل:</strong> افحص سلك الكهرباء بانتظام وتأكد من عدم وجود تلف في العزل',
                '<strong>زيّت الأجزاء المتحركة:</strong> استخدم زيت خفيف على التروس والمحامل دورياً',
                '<strong>خزّن بشكل صحيح:</strong> في مكان جاف ونظيف، داخل الحقيبة الأصلية',
                '<strong>لا تُحمّل الأداة فوق طاقتها:</strong> استخدم الأداة المناسبة للمهمة المناسبة',
            ]) +

            _h2('العناية بالبطاريات') +
            _ol([
                'لا تترك البطارية فارغة تماماً لفترة طويلة',
                'خزّن البطاريات في درجة حرارة معتدلة (15-25°C)',
                'استخدم الشاحن الأصلي فقط',
                'إذا كنت لن تستخدم البطارية لفترة، اشحنها إلى 50% قبل التخزين',
            ]) +

            _h2('صيانة العدد اليدوية') +
            _ul([
                'نظّف المفاتيح والبوكسات بعد الاستخدام وامسحها بقطعة قماش مزيتة لمنع الصدأ',
                'اشحذ الأدوات القاطعة (المقصات، الأزاميل، المناشير) بانتظام',
                'تحقق من إحكام رؤوس الشواكيش والمقابض',
                'خزّن الأدوات في صندوق أو حقيبة عدة لحمايتها',
            ]) +

            _h2('متى تستبدل أدواتك؟') +
            _p('استبدل أي أداة عند: ظهور تشققات في الجسم أو المقبض، اهتزاز غير طبيعي في العدد الكهربائية، تآكل واضح في الأجزاء المتحركة، أو انخفاض ملحوظ في الأداء رغم الصيانة.') +

            _h2('قطع غيار وصيانة من ESCO') +
            _p('مستودعات الهندسة ESCO توفر قطع غيار أصلية لجميع الماركات المتوفرة لدينا. كما نقدم نصائح الصيانة والدعم الفني. زُرنا أو تواصل معنا لأي استفسار عن صيانة أدواتك.')
        ),
        'content_en': (
            _h2('Why Tool Maintenance Matters') +
            _p('Regular maintenance preserves performance, extends tool life, and prevents unexpected failures. A well-maintained tool outlasts a more expensive neglected one.') +
            _h2('Maintenance Tips') +
            _p('Clean after every use, inspect carbon brushes, check cables, lubricate moving parts, store properly, and never overload tools. For batteries, avoid full discharge, store at moderate temperature, and use original chargers only.') +
            _h2('Spare Parts from ESCO') +
            _p('ESCO provides original spare parts and maintenance support for all brands we carry.')
        ),
        'faqs': [
            {
                'question': 'كل كم يجب صيانة العدد الكهربائية؟',
                'question_en': 'How often should power tools be maintained?',
                'answer': 'للاستخدام المهني اليومي: تنظيف بعد كل استخدام، فحص شامل كل شهر، وتغيير الفحمات كل 6-12 شهر حسب الاستخدام. للاستخدام المنزلي: فحص وتنظيف كل 3-6 أشهر. الصيانة الدورية تمنع 80% من الأعطال.',
                'answer_en': 'For daily professional use: clean after each use, full inspection monthly, replace carbon brushes every 6-12 months. For home use: inspect and clean every 3-6 months. Regular maintenance prevents 80% of failures.',
            },
        ],
    },

    # ─── POST 14: Construction Tools ───
    {
        'title': 'أدوات ومعدات البناء والتشييد في الأردن - دليل المقاولين',
        'title_en': 'Construction Tools and Equipment in Jordan - Contractor Guide',
        'slug': 'construction-tools-equipment-jordan',
        'category_slug': 'construction-equipment',
        'tags': ['معدات بناء', 'مقاولات', 'عدد صناعية', 'الأردن', 'عمان'],
        'excerpt': 'دليل شامل لأدوات ومعدات البناء في الأردن. خلاطات باطون، هزازات، أدوات تبليط وتسوية ومعدات إنشائية لشركات المقاولات.',
        'excerpt_en': 'Comprehensive guide to construction tools in Jordan. Concrete mixers, vibrators, tiling tools and equipment for contractors.',
        'card_icon': 'fa-hard-hat',
        'card_icon_color': '#ea580c',
        'meta_title': 'أدوات ومعدات البناء في الأردن - معدات مقاولات | ESCO',
        'meta_description': 'معدات بناء وتشييد في الأردن. خلاطات باطون، هزازات، قواطع بلاط، أدوات تسوية لشركات المقاولات من ESCO.',
        'meta_keywords': 'معدات بناء, أدوات بناء, خلاطة باطون, هزاز باطون, قاطع بلاط, أدوات تبليط, مقاولات, الأردن',
        'content': (
            _h2('قطاع البناء في الأردن') +
            _p('يُعد قطاع البناء والتشييد من أكبر القطاعات الاقتصادية في الأردن. مع النمو المستمر في المشاريع السكنية والتجارية والبنية التحتية، يتزايد الطلب على أدوات ومعدات البناء عالية الجودة. شركات المقاولات والمهندسون بحاجة إلى معدات موثوقة لتنفيذ المشاريع بكفاءة وجودة.') +

            _h2('معدات الخرسانة والباطون') +
            _ul([
                '<strong>خلاطة باطون:</strong> بأحجام مختلفة من 120 إلى 500 لتر للمشاريع المختلفة',
                '<strong>هزاز باطون:</strong> لضمان تماسك الخرسانة وإزالة الفقاعات الهوائية',
                '<strong>مسطحة باطون كهربائية:</strong> لتنعيم وتسوية الأسطح الخرسانية',
                '<strong>قاطع خرسانة:</strong> لقطع الفواصل والأخاديد في الخرسانة',
            ]) +

            _h2('أدوات التبليط والتسوية') +
            _ul([
                '<strong>قاطع بلاط يدوي:</strong> لقطع البلاط السيراميك والبورسلان',
                '<strong>صاروخ قطع بلاط بالماء:</strong> للقطع الدقيق والنظيف',
                '<strong>ميزان ليزر:</strong> لضمان استواء صفوف البلاط',
                '<strong>أدوات فرد اللاصق:</strong> مشاحيف مسننة بأحجام مختلفة',
                '<strong>نظام تسوية بلاط:</strong> كليبسات وأسافين لضمان استواء البلاط',
            ]) +

            _h2('أدوات البناء العامة') +
            _ul([
                '<strong>سقالات ألمنيوم:</strong> خفيفة وآمنة للعمل على الارتفاعات',
                '<strong>عربات يدوية ونقل:</strong> لنقل مواد البناء في الموقع',
                '<strong>دريل تكسير (هيلتي):</strong> لتكسير الباطون وفتح الثقوب الكبيرة',
                '<strong>صاروخ قص 14 بوصة:</strong> لقطع الحديد والباطون',
            ]) +

            _h2('معدات البناء من ESCO') +
            _p('مستودعات الهندسة ESCO هي المورد الموثوق لشركات المقاولات في الأردن. نوفر جميع معدات وأدوات البناء من ماركات عالمية بأسعار منافسة. خدمة توصيل للمواقع الإنشائية وعروض خاصة للكميات الكبيرة. تواصل معنا لعرض سعر مخصص لمشروعك.')
        ),
        'content_en': (
            _h2('Construction Sector in Jordan') +
            _p('Construction is one of Jordan\'s largest economic sectors, with growing demand for quality tools and equipment.') +
            _h2('Construction Equipment from ESCO') +
            _p('ESCO is the trusted supplier for contractors in Jordan, offering all construction tools at competitive prices with site delivery and bulk discounts.')
        ),
        'faqs': [
            {
                'question': 'هل ESCO توفر معدات بناء بالجملة لشركات المقاولات؟',
                'question_en': 'Does ESCO supply construction equipment in bulk for contractors?',
                'answer': 'نعم، مستودعات الهندسة ESCO تقدم عروض جملة خاصة لشركات المقاولات والمشاريع الكبيرة. نوفر عروض أسعار مخصصة وخدمة توصيل مباشرة للموقع. تواصل مع قسم المبيعات للحصول على عرض سعر لمشروعك.',
                'answer_en': 'Yes, ESCO offers special bulk pricing for contracting companies and large projects with customized quotes and direct site delivery. Contact our sales department for a project quote.',
            },
        ],
    },

    # ─── POST 15: ESCO B2B ───
    {
        'title': 'مستودعات الهندسة ESCO - شريكك الموثوق للعدد والأدوات الصناعية في الأردن',
        'title_en': 'ESCO Engineering Stores - Your Trusted Partner for Industrial Tools in Jordan',
        'slug': 'esco-engineering-stores-jordan',
        'category_slug': 'buying-guides',
        'tags': ['عدد صناعية', 'الأردن', 'عمان', 'مصانع', 'مقاولات', 'ورش صناعية'],
        'excerpt': 'تعرف على مستودعات الهندسة ESCO، أكبر مورد للعدد والأدوات الصناعية في الأردن. خدمات الأفراد والشركات والمؤسسات.',
        'excerpt_en': 'Learn about ESCO Engineering Stores, the largest supplier of industrial tools in Jordan. Services for individuals, companies, and institutions.',
        'card_icon': 'fa-building',
        'card_icon_color': '#1e3a5f',
        'meta_title': 'مستودعات الهندسة ESCO - أكبر مورد عدد صناعية في الأردن',
        'meta_description': 'مستودعات الهندسة ESCO أكبر مورد للعدد والأدوات الصناعية في الأردن منذ 1994. نخدم الأفراد والشركات والمصانع. زُرنا في عمان.',
        'meta_keywords': 'مستودعات الهندسة, ESCO, عدد صناعية الأردن, أدوات صناعية عمان, مورد عدد الأردن, أدوات هندسية',
        'content': (
            _h2('عن مستودعات الهندسة ESCO') +
            _p('بدأت شركة مستودعات الهندسة ESCO كمحل صغير للعدد والأدوات على الطريق الرئيسي لمنطقة سحاب الصناعية. واليوم، أصبحنا أحد أكبر موردي العدد والأدوات الصناعية في الأردن، بمساحة تزيد عن 7000 متر مربع تغطي جميع احتياجات القطاع الصناعي والإنشائي في المملكة الأردنية الهاشمية.') +

            _h2('منتجاتنا') +
            _p('نوفر أكثر من 15,000 صنف من العدد والأدوات والمعدات الصناعية:') +
            _ul([
                '<strong>العدد الكهربائية:</strong> مثاقب، مناشير، صواريخ، صنافر من بوش وماكيتا وديوالت',
                '<strong>العدد اليدوية:</strong> مفاتيح، بوكسات، مفكات، زراديات من ستانلي وبيتا',
                '<strong>معدات اللحام:</strong> ماكينات لحام كهربائي وأرجون وMIG مع جميع الملحقات',
                '<strong>أدوات القياس:</strong> أجهزة ليزر، أمتار، فرجار، ملتيميتر',
                '<strong>معدات السلامة:</strong> خوذات، نظارات، قفازات، أحذية، أحزمة أمان',
                '<strong>معدات الرفع والنقل:</strong> رافعات، ونشات، سلاسل، عربات',
                '<strong>أدوات السباكة والكهرباء:</strong> عدد متخصصة لجميع الحرف',
                '<strong>معدات البناء:</strong> خلاطات، هزازات، قواطع، أدوات تبليط',
            ]) +

            _h2('خدماتنا') +
            _h3('خدمة الشركات والمؤسسات (B2B)') +
            _p('نقدم خدمات متخصصة لشركات المقاولات والمصانع والمؤسسات الحكومية تشمل عروض أسعار مخصصة، حسابات آجلة للعملاء المعتمدين، وتوصيل مباشر للمواقع.') +

            _h3('خدمة ما بعد البيع') +
            _p('نوفر ضماناً رسمياً على جميع منتجاتنا مع خدمة صيانة وقطع غيار أصلية. فريق الدعم الفني لدينا جاهز لمساعدتك في اختيار الأدوات المناسبة والاستشارات الفنية.') +

            _h3('التسوق الإلكتروني') +
            _p('يمكنك تصفح وشراء جميع منتجاتنا عبر موقعنا الإلكتروني esco.jo مع خدمة توصيل لجميع مناطق الأردن.') +

            _h2('فروعنا في عمان') +
            _p('نعمل من عدة مواقع في عمان لتسهيل الوصول لجميع عملائنا. زُر أقرب فرع أو تواصل معنا عبر الرقم 0799998185 أو البريد contact@esco.jo.') +

            _h2('لماذا تختار ESCO؟') +
            _ul([
                'أكبر تشكيلة عدد وأدوات صناعية في الأردن',
                'منتجات أصلية 100% بضمان رسمي',
                'أسعار تنافسية وعروض مستمرة',
                'خدمة عملاء احترافية ودعم فني',
                'توصيل لجميع مناطق المملكة',
                'خبرة أكثر من 25 عاماً في السوق الأردني',
            ])
        ),
        'content_en': (
            _h2('About ESCO Engineering Stores') +
            _p('ESCO started as a small hardware shop and grew to become one of Jordan\'s largest industrial tool suppliers, operating from over 7,000 square meters.') +
            _h2('Our Products') +
            _p('We offer over 15,000 items including power tools, hand tools, welding equipment, measuring tools, safety equipment, lifting equipment, and construction tools from top global brands.') +
            _h2('Why Choose ESCO?') +
            _p('Largest selection in Jordan, 100% original products with official warranty, competitive prices, professional customer service, nationwide delivery, and over 25 years of market experience.')
        ),
        'faqs': [
            {
                'question': 'هل ESCO تبيع بالجملة والتجزئة؟',
                'question_en': 'Does ESCO sell wholesale and retail?',
                'answer': 'نعم، مستودعات الهندسة ESCO تبيع بالجملة والتجزئة. نقدم أسعاراً خاصة للكميات الكبيرة وحسابات آجلة لشركات المقاولات والمصانع والموزعين. الأفراد مرحب بهم أيضاً في جميع فروعنا وعبر موقعنا الإلكتروني.',
                'answer_en': 'Yes, ESCO sells both wholesale and retail. We offer special bulk pricing and credit accounts for contractors, factories, and distributors. Individuals are also welcome at all branches and online.',
            },
            {
                'question': 'هل يمكنني الشراء أونلاين من ESCO؟',
                'question_en': 'Can I buy online from ESCO?',
                'answer': 'نعم، يمكنك تصفح وشراء جميع منتجاتنا عبر موقعنا الإلكتروني esco.jo. نوفر خدمة توصيل لجميع مناطق الأردن. يمكنك أيضاً الاتصال على 0799998185 للطلب هاتفياً أو للاستفسار عن المنتجات.',
                'answer_en': 'Yes, you can browse and buy all products at esco.jo with delivery across Jordan. You can also call 0799998185 for phone orders or product inquiries.',
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed comprehensive SEO-optimized blog content for ESCO Jordan'

    def handle(self, *args, **options):
        author = User.objects.filter(first_name__icontains='mohammad').first()
        if not author:
            author = User.objects.filter(is_staff=True).first()
        if not author:
            self.stderr.write('No staff user found. Create one first.')
            return
        self.stdout.write(f'Author: {author.get_full_name() or author.email}')

        # Create categories
        cat_map = {}
        for cat_data in CATEGORIES:
            cat, created = BlogCategory.objects.update_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'name_en': cat_data['name_en'],
                    'description': cat_data['description'],
                    'description_en': cat_data['description_en'],
                    'icon': cat_data['icon'],
                    'meta_title': cat_data['meta_title'],
                    'meta_description': cat_data['meta_description'],
                    'is_active': True,
                    'sort_order': CATEGORIES.index(cat_data),
                },
            )
            cat_map[cat_data['slug']] = cat
            self.stdout.write(f'  {"Created" if created else "Updated"} category: {cat.name}')

        # Create tags
        tag_map = {}
        for name_ar, name_en in TAGS:
            slug = slugify(name_en, allow_unicode=True).lower()
            if not slug:
                slug = slugify(name_ar, allow_unicode=True)
            tag, created = BlogTag.objects.update_or_create(
                slug=slug,
                defaults={'name': name_ar, 'name_en': name_en},
            )
            tag_map[name_ar] = tag

        self.stdout.write(f'  Created/updated {len(TAGS)} tags')

        # Create posts
        now = timezone.now()
        for i, post_data in enumerate(POSTS):
            post, created = BlogPost.objects.update_or_create(
                slug=post_data['slug'],
                defaults={
                    'title': post_data['title'],
                    'title_en': post_data['title_en'],
                    'category': cat_map.get(post_data['category_slug']),
                    'author': author,
                    'excerpt': post_data['excerpt'],
                    'excerpt_en': post_data['excerpt_en'],
                    'content': post_data['content'],
                    'content_en': post_data['content_en'],
                    'card_icon': post_data.get('card_icon', 'fa-newspaper'),
                    'card_icon_color': post_data.get('card_icon_color', '#2563eb'),
                    'status': 'published',
                    'is_featured': i < 5,
                    'meta_title': post_data['meta_title'],
                    'meta_description': post_data['meta_description'],
                    'meta_keywords': post_data['meta_keywords'],
                    'published_at': now - timezone.timedelta(days=len(POSTS) - i),
                },
            )

            # Set tags
            post_tags = [tag_map[t] for t in post_data.get('tags', []) if t in tag_map]
            post.tags.set(post_tags)

            # Create FAQs
            for j, faq_data in enumerate(post_data.get('faqs', [])):
                BlogPostFAQ.objects.update_or_create(
                    post=post,
                    question=faq_data['question'],
                    defaults={
                        'question_en': faq_data.get('question_en', ''),
                        'answer': faq_data['answer'],
                        'answer_en': faq_data.get('answer_en', ''),
                        'sort_order': j,
                        'is_active': True,
                    },
                )

            self.stdout.write(f'  {"Created" if created else "Updated"} post: {post.title[:60]}...')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created {len(CATEGORIES)} categories, {len(TAGS)} tags, '
            f'{len(POSTS)} posts with FAQs.'
        ))
