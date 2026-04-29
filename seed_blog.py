import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esco_project.settings')
django.setup()

from blog.models import BlogPost, BlogCategory, BlogTag
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
author = User.objects.filter(is_staff=True).first()
cats = {c.slug: c for c in BlogCategory.objects.all()}
tags = {t.slug: t for t in BlogTag.objects.all()}

articles = [
    {
        "title": "دليل شراء المثقاب الكهربائي المناسب لاحتياجاتك",
        "title_en": "Complete Guide to Choosing the Right Power Drill",
        "slug": "guide-choosing-power-drill",
        "category": cats["buying-guides"],
        "excerpt": "تعرف على أنواع المثاقب الكهربائية والفروقات بينها وكيف تختار الأنسب لمشاريعك",
        "excerpt_en": "Learn about different types of power drills and how to choose the best one for your projects",
        "content": "<h2>لماذا اختيار المثقاب المناسب مهم؟</h2><p>المثقاب الكهربائي هو أحد أهم الأدوات في أي ورشة عمل أو منزل. اختيار المثقاب الخاطئ قد يكلفك الوقت والمال.</p><h2>أنواع المثاقب الكهربائية</h2><h3>1. المثقاب العادي (Drill Driver)</h3><p>مناسب للثقب في الخشب والمعادن الخفيفة وتثبيت البراغي. يعمل بسرعات متعددة.</p><ul><li>الاستخدام: أعمال منزلية خفيفة ومتوسطة</li><li>القوة: 400-800 واط</li><li>السعر: 15-45 دينار أردني</li></ul><h3>2. المثقاب الدقاق (Hammer Drill)</h3><p>يجمع بين الدوران والطرق، مما يجعله مثالياً للثقب في الخرسانة والطوب.</p><ul><li>الاستخدام: ثقب الجدران والخرسانة</li><li>القوة: 600-1200 واط</li><li>السعر: 25-80 دينار أردني</li></ul><h3>3. المثقاب اللاسلكي (Cordless Drill)</h3><p>يوفر حرية الحركة دون الحاجة لمصدر كهرباء.</p><ul><li>الاستخدام: متعدد الاستخدامات ومحمول</li><li>البطارية: 12V - 20V</li><li>السعر: 35-120 دينار أردني</li></ul><h2>معايير الاختيار</h2><ol><li><strong>نوع العمل:</strong> حدد ما ستستخدم المثقاب له</li><li><strong>القوة (الواط):</strong> كلما زادت القوة، زادت القدرة على التعامل مع المواد الصلبة</li><li><strong>السرعة:</strong> ابحث عن مثقاب بسرعات متعددة</li><li><strong>العلامة التجارية:</strong> اختر ماركات موثوقة مثل بوش، ماكيتا، أو ديوالت</li><li><strong>الضمان:</strong> تأكد من وجود ضمان وخدمة ما بعد البيع</li></ol><blockquote><strong>نصيحة من خبراء ESCO:</strong> إذا كنت مبتدئاً، ابدأ بمثقاب لاسلكي 12V فهو خفيف وسهل الاستخدام.</blockquote><h2>أفضل المثاقب المتوفرة في ESCO</h2><p>نوفر في المخازن الهندسية مجموعة واسعة من المثاقب من أشهر العلامات التجارية العالمية بأسعار تنافسية وضمان حقيقي.</p>",
        "content_en": "<h2>Why Choosing the Right Drill Matters</h2><p>A power drill is one of the most essential tools in any workshop or home. Choosing the wrong drill can cost you time and money.</p><h2>Types of Power Drills</h2><h3>1. Drill Driver</h3><p>Suitable for drilling in wood and light metals and driving screws. Comes with multiple speeds.</p><ul><li>Use: Light to medium household tasks</li><li>Power: 400-800W</li><li>Price: 15-45 JOD</li></ul><h3>2. Hammer Drill</h3><p>Combines rotation and hammering action, ideal for drilling into concrete and brick.</p><ul><li>Use: Drilling walls and concrete</li><li>Power: 600-1200W</li><li>Price: 25-80 JOD</li></ul><h3>3. Cordless Drill</h3><p>Provides freedom of movement without needing a power source.</p><ul><li>Use: Versatile and portable</li><li>Battery: 12V - 20V</li><li>Price: 35-120 JOD</li></ul><h2>Selection Criteria</h2><ol><li><strong>Type of Work:</strong> Determine what you will primarily use the drill for</li><li><strong>Power (Watts):</strong> Higher wattage means better handling of hard materials</li><li><strong>Speed:</strong> Look for a drill with multiple adjustable speeds</li><li><strong>Brand:</strong> Choose trusted brands like Bosch, Makita, or DeWalt</li><li><strong>Warranty:</strong> Ensure warranty and after-sales service</li></ol><blockquote><strong>ESCO Expert Tip:</strong> If you are a beginner, start with a 12V cordless drill - lightweight and easy to use.</blockquote><h2>Best Drills Available at ESCO</h2><p>At Engineering Stores Company, we offer a wide range of drills from leading global brands at competitive prices with genuine warranty.</p>",
        "status": "published",
        "is_featured": True,
        "published_at": timezone.now() - timedelta(days=2),
        "meta_title": "دليل شراء المثقاب الكهربائي | ESCO",
        "meta_description": "دليل شامل لاختيار المثقاب الكهربائي المناسب - أنواع المثاقب ومعايير الاختيار وأفضل الماركات",
        "meta_keywords": "مثقاب كهربائي, شراء مثقاب, بوش, ماكيتا, ديوالت",
        "featured_image_alt": "دليل شراء المثقاب الكهربائي",
        "featured_image_alt_en": "Guide to choosing the right power drill",
        "tag_slugs": ["power-drills", "power-tools", "bosch", "makita", "dewalt"],
    },
    {
        "title": "مقارنة بين بوش وماكيتا: أيهما أفضل للاستخدام المهني؟",
        "title_en": "Bosch vs Makita: Which is Better for Professional Use?",
        "slug": "bosch-vs-makita-professional",
        "category": cats["tool-comparisons"],
        "excerpt": "مقارنة تفصيلية بين عملاقي الأدوات الكهربائية بوش وماكيتا من حيث الجودة والمتانة والسعر",
        "excerpt_en": "A detailed comparison between Bosch and Makita in terms of quality, durability, and price",
        "content": "<h2>بوش vs ماكيتا: المقارنة الشاملة</h2><p>عند شراء أدوات كهربائية احترافية، غالباً ما يقع الاختيار بين بوش وماكيتا. كلتا العلامتين تتمتعان بسمعة عالمية ممتازة.</p><h2>نبذة عن كل علامة تجارية</h2><h3>بوش (Bosch) - ألمانيا</h3><p>تأسست عام 1886. تشتهر بالهندسة الدقيقة والابتكار التقني. توفر خطين: الأزرق للمحترفين والأخضر للهواة.</p><h3>ماكيتا (Makita) - اليابان</h3><p>تأسست عام 1915. رائدة في الأدوات اللاسلكية ومعروفة بمتانة منتجاتها.</p><h2>جدول المقارنة</h2><table class='table table-bordered'><thead><tr><th>المعيار</th><th>بوش</th><th>ماكيتا</th></tr></thead><tbody><tr><td>بلد المنشأ</td><td>ألمانيا</td><td>اليابان</td></tr><tr><td>نطاق الأسعار</td><td>متوسط إلى مرتفع</td><td>متوسط</td></tr><tr><td>المتانة</td><td>ممتازة</td><td>ممتازة</td></tr><tr><td>توفر قطع الغيار</td><td>ممتاز في الأردن</td><td>جيد جداً</td></tr><tr><td>البطاريات اللاسلكية</td><td>18V و 12V</td><td>18V LXT</td></tr></tbody></table><h2>المثاقب الكهربائية</h2><p><strong>بوش:</strong> تتميز بنظام SDS المبتكر للتغيير السريع لرؤوس الثقب. الموتورات قوية ومتينة.</p><p><strong>ماكيتا:</strong> تتميز بخفة الوزن وسهولة الاستخدام لفترات طويلة. بطاريات LXT توفر عمراً أطول.</p><h2>الخلاصة</h2><ul><li><strong>اختر بوش</strong> إذا كنت تبحث عن دقة عالية وتقنيات متقدمة</li><li><strong>اختر ماكيتا</strong> إذا كنت تعمل لساعات طويلة وتحتاج أدوات خفيفة ومتينة</li></ul><blockquote>في ESCO نوفر منتجات كلتا العلامتين. فريقنا جاهز لمساعدتك في الاختيار.</blockquote>",
        "content_en": "<h2>Bosch vs Makita: The Complete Comparison</h2><p>When buying professional power tools, the choice often comes down to Bosch and Makita. Both brands enjoy excellent global reputations.</p><h2>Brand Overview</h2><h3>Bosch - Germany</h3><p>Founded in 1886. Known for precise engineering and technical innovation. Offers Blue (professional) and Green (hobbyist) lines.</p><h3>Makita - Japan</h3><p>Founded in 1915. Pioneer in cordless tools, known for durability.</p><h2>Comparison Table</h2><table class='table table-bordered'><thead><tr><th>Criteria</th><th>Bosch</th><th>Makita</th></tr></thead><tbody><tr><td>Country of Origin</td><td>Germany</td><td>Japan</td></tr><tr><td>Price Range</td><td>Medium to High</td><td>Medium</td></tr><tr><td>Durability</td><td>Excellent</td><td>Excellent</td></tr><tr><td>Spare Parts</td><td>Excellent in Jordan</td><td>Very Good</td></tr><tr><td>Cordless Batteries</td><td>18V & 12V</td><td>18V LXT</td></tr></tbody></table><h2>Power Drills</h2><p><strong>Bosch:</strong> Features innovative SDS system for quick bit changes. Powerful and durable motors.</p><p><strong>Makita:</strong> Lightweight design, comfortable for extended use. LXT batteries last longer.</p><h2>Conclusion</h2><ul><li><strong>Choose Bosch</strong> for high precision and advanced technology</li><li><strong>Choose Makita</strong> for long work hours with lightweight, durable tools</li></ul><blockquote>At ESCO, we carry both brands. Our team is ready to help you choose.</blockquote>",
        "status": "published",
        "is_featured": True,
        "published_at": timezone.now() - timedelta(days=5),
        "meta_title": "مقارنة بوش وماكيتا | ESCO",
        "meta_description": "مقارنة شاملة بين بوش وماكيتا - الجودة والأسعار والمتانة",
        "meta_keywords": "بوش, ماكيتا, مقارنة أدوات, Bosch vs Makita",
        "featured_image_alt": "مقارنة بين بوش وماكيتا",
        "featured_image_alt_en": "Bosch vs Makita comparison",
        "tag_slugs": ["bosch", "makita", "power-tools", "power-drills"],
    },
    {
        "title": "10 نصائح للحفاظ على أدواتك الكهربائية وإطالة عمرها",
        "title_en": "10 Tips to Maintain Your Power Tools and Extend Their Lifespan",
        "slug": "10-tips-maintain-power-tools",
        "category": cats["maintenance-tips"],
        "excerpt": "نصائح عملية للحفاظ على أدواتك الكهربائية في أفضل حالة وتجنب الأعطال المكلفة",
        "excerpt_en": "Practical tips to keep your power tools in top condition and avoid costly breakdowns",
        "content": "<h2>أدواتك استثمار... حافظ عليها!</h2><p>الأدوات الكهربائية ليست رخيصة، والعناية بها يمكن أن يضاعف عمرها الافتراضي. إليك 10 نصائح ذهبية.</p><h2>1. نظف أدواتك بعد كل استخدام</h2><p>استخدم فرشاة ناعمة أو هواء مضغوط لإزالة الغبار من فتحات التهوية. تراكم الغبار هو العدو الأول للمحركات.</p><h2>2. خزن الأدوات في مكان جاف</h2><p>الرطوبة تسبب الصدأ وتلف الأجزاء الإلكترونية. استخدم حقيبة أدوات مقاومة للماء.</p><h2>3. افحص الأسلاك دورياً</h2><p>أي سلك مكشوف أو تالف يشكل خطر صدمة كهربائية ويجب استبداله فوراً.</p><h2>4. استخدم الملحقات الأصلية فقط</h2><p>الملحقات غير الأصلية تسبب إجهاداً زائداً على المحرك وقد تتلف الأداة.</p><h2>5. لا تضغط على الأداة أكثر من طاقتها</h2><p>دع الأداة تعمل بسرعتها الطبيعية. الضغط الزائد يسخن المحرك ويقصر عمره.</p><h2>6. اشحن البطاريات بشكل صحيح</h2><p>لا تترك البطاريات فارغة تماماً. اشحنها عند 20% واستخدم الشاحن الأصلي.</p><h2>7. زيّت الأجزاء المتحركة</h2><p>استخدم زيت تشحيم مخصص على التروس والمحامل كل 3-6 أشهر.</p><h2>8. افحص فرش الكربون</h2><p>في المحركات الفحمية، افحص فرش الكربون واستبدلها عند تآكلها.</p><h2>9. لا تسقط الأداة</h2><p>الصدمات تتلف التروس الداخلية، والحرارة المفرطة تتلف البطاريات.</p><h2>10. اعمل صيانة دورية</h2><p>كل 6-12 شهراً، أحضر أدواتك لمركز صيانة معتمد لفحص شامل.</p><blockquote><strong>هل تحتاج صيانة لأدواتك؟</strong> فريق ESCO جاهز لمساعدتك. زر أقرب فرع للحصول على فحص مجاني.</blockquote>",
        "content_en": "<h2>Your Tools Are an Investment... Protect Them!</h2><p>Power tools are not cheap, and proper care can double their lifespan. Here are 10 golden tips.</p><h2>1. Clean After Every Use</h2><p>Use a soft brush or compressed air to remove dust from ventilation slots. Dust is the number one enemy of motors.</p><h2>2. Store in a Dry Place</h2><p>Moisture causes rust and damages electronics. Use a waterproof tool bag.</p><h2>3. Inspect Cords Regularly</h2><p>Any exposed or damaged wire poses a shock hazard and must be replaced immediately.</p><h2>4. Use Original Accessories Only</h2><p>Non-original accessories cause excessive strain on the motor and can damage the tool.</p><h2>5. Don't Push Beyond Capacity</h2><p>Let the tool work at its natural speed. Excessive pressure overheats the motor.</p><h2>6. Charge Batteries Properly</h2><p>Don't leave batteries fully drained. Charge at 20% using only the original charger.</p><h2>7. Lubricate Moving Parts</h2><p>Apply tool lubricant on gears and bearings every 3-6 months.</p><h2>8. Check Carbon Brushes</h2><p>In brushed motors, inspect and replace carbon brushes when worn.</p><h2>9. Don't Drop Tools</h2><p>Impacts damage internal gears; excessive heat damages batteries.</p><h2>10. Schedule Professional Maintenance</h2><p>Every 6-12 months, bring tools to an authorized service center.</p><blockquote><strong>Need maintenance?</strong> The ESCO team is ready to help. Visit the nearest branch for a free inspection.</blockquote>",
        "status": "published",
        "is_featured": True,
        "published_at": timezone.now() - timedelta(days=8),
        "meta_title": "10 نصائح لصيانة الأدوات الكهربائية | ESCO",
        "meta_description": "نصائح عملية للحفاظ على أدواتك الكهربائية وإطالة عمرها",
        "meta_keywords": "صيانة أدوات, أدوات كهربائية, نصائح صيانة",
        "featured_image_alt": "نصائح صيانة الأدوات الكهربائية",
        "featured_image_alt_en": "Power tools maintenance tips",
        "tag_slugs": ["power-tools", "hand-tools", "home-maintenance", "safety-equipment"],
    },
    {
        "title": "كيف تبني رف تخزين خشبي بنفسك: مشروع نهاية الأسبوع",
        "title_en": "How to Build a Wooden Storage Shelf Yourself: A Weekend Project",
        "slug": "diy-wooden-storage-shelf",
        "category": cats["diy-projects"],
        "excerpt": "مشروع عملي سهل لبناء رف تخزين خشبي أنيق لمنزلك أو ورشتك",
        "excerpt_en": "A practical, easy project to build a wooden storage shelf for your home or workshop",
        "content": "<h2>مشروع نهاية الأسبوع: رف تخزين خشبي</h2><p>هل تحتاج مساحة تخزين إضافية؟ يمكنك بناء رف متين وأنيق خلال يوم واحد! مناسب للمبتدئين.</p><h2>الأدوات المطلوبة</h2><ul><li>مثقاب كهربائي / مفك كهربائي</li><li>منشار كهربائي أو يدوي</li><li>شريط قياس (متر)</li><li>ميزان مائي</li><li>ورق صنفرة (120 و 220)</li><li>مسامير خشب (5 سم)</li><li>غراء خشب</li></ul><h2>المواد المطلوبة</h2><ul><li>4 ألواح خشب صنوبر (180 × 20 × 2 سم) - للأرفف</li><li>2 لوح خشب (180 × 30 × 2 سم) - للجوانب</li><li>ورنيش أو طلاء خشب</li></ul><h2>خطوات التنفيذ</h2><h3>الخطوة 1: القياس والقص</h3><p>قس المساحة وحدد ارتفاع الرف. قص الألواح حسب المقاسات. تأكد من استقامة القطع.</p><h3>الخطوة 2: الصنفرة</h3><p>صنفرة جميع الأسطح بورق 120 أولاً ثم 220 للتنعيم النهائي.</p><h3>الخطوة 3: التجميع</h3><p>ضع غراء الخشب ثم ثبت الأرفف بالمسامير. استخدم الميزان المائي لكل رف.</p><h3>الخطوة 4: التشطيب</h3><p>بعد جفاف الغراء (24 ساعة)، ضع طبقتين من الورنيش مع صنفرة خفيفة بينهما.</p><h2>التكلفة التقديرية</h2><p>تكلفة المواد: 15-25 دينار أردني فقط!</p><blockquote><strong>جميع الأدوات والمواد متوفرة في فروع ESCO.</strong> فريقنا يساعدك في اختيار الخشب وقصه.</blockquote>",
        "content_en": "<h2>Weekend Project: Wooden Storage Shelf</h2><p>Need extra storage space? Build a sturdy shelf in just one day! Suitable for beginners.</p><h2>Tools Required</h2><ul><li>Power drill / electric screwdriver</li><li>Electric or hand saw</li><li>Measuring tape</li><li>Spirit level</li><li>Sandpaper (120 and 220 grit)</li><li>Wood screws (5cm)</li><li>Wood glue</li></ul><h2>Materials Required</h2><ul><li>4 pine boards (180 x 20 x 2 cm) - shelves</li><li>2 boards (180 x 30 x 2 cm) - sides</li><li>Varnish or wood paint</li></ul><h2>Steps</h2><h3>Step 1: Measure and Cut</h3><p>Measure the space and determine shelf height. Cut boards to size. Ensure straight cuts.</p><h3>Step 2: Sanding</h3><p>Sand all surfaces with 120 grit first, then 220 for final smoothing.</p><h3>Step 3: Assembly</h3><p>Apply wood glue, then secure shelves with screws. Use spirit level for each shelf.</p><h3>Step 4: Finishing</h3><p>After glue dries (24 hours), apply two coats of varnish with light sanding between.</p><h2>Estimated Cost</h2><p>Materials: Only 15-25 JOD!</p><blockquote><strong>All tools and materials available at ESCO branches.</strong> Our team can help with wood selection and cutting.</blockquote>",
        "status": "published",
        "is_featured": False,
        "published_at": timezone.now() - timedelta(days=12),
        "meta_title": "مشروع رف خشبي DIY | ESCO",
        "meta_description": "تعلم بناء رف تخزين خشبي بنفسك خطوة بخطوة",
        "meta_keywords": "مشروع DIY, رف خشبي, نجارة",
        "featured_image_alt": "مشروع رف تخزين خشبي",
        "featured_image_alt_en": "DIY wooden storage shelf project",
        "tag_slugs": ["woodworking", "hand-tools", "power-drills", "measuring-tools", "home-maintenance"],
    },
    {
        "title": "معدات السلامة المهنية: ما تحتاجه في ورشتك",
        "title_en": "Professional Safety Equipment: What You Need in Your Workshop",
        "slug": "workshop-safety-equipment-guide",
        "category": cats["buying-guides"],
        "excerpt": "دليل شامل لمعدات السلامة الأساسية في كل ورشة عمل",
        "excerpt_en": "A comprehensive guide to essential safety equipment for every workshop",
        "content": "<h2>السلامة أولاً!</h2><p>الحوادث يمكن أن تحدث لأي شخص. معدات السلامة ليست رفاهية بل ضرورة.</p><h2>حماية العينين</h2><h3>نظارات السلامة</h3><p>ضرورية عند استخدام المناشير والمثاقب. اختر نظارات ANSI Z87.1 مع تهوية جانبية.</p><h2>حماية السمع</h2><h3>أغطية الأذن</h3><p>الأدوات الكهربائية قد تصل ضوضاؤها إلى 100 ديسيبل. استخدم واقيات بمعدل خفض 25-30 ديسيبل.</p><h2>حماية الجهاز التنفسي</h2><h3>كمامات الغبار</h3><p>غبار الخشب والمعادن يسبب أمراضاً تنفسية. استخدم كمامة N95 على الأقل.</p><h2>حماية اليدين</h2><ul><li><strong>قفازات جلدية:</strong> للأعمال العامة</li><li><strong>قفازات مقاومة للقطع:</strong> مع الشفرات الحادة</li><li><strong>قفازات مطاطية:</strong> للمواد الكيميائية</li></ul><h2>حماية القدمين</h2><p>أحذية بمقدمة فولاذية ونعل مقاوم للانزلاق. ضرورية في أي ورشة.</p><h2>معدات إضافية</h2><ul><li><strong>طفاية حريق:</strong> نوع ABC</li><li><strong>حقيبة إسعافات أولية</strong></li><li><strong>ملابس عمل مقاومة للحريق</strong></li><li><strong>حزام أمان:</strong> للعمل على ارتفاعات</li></ul><blockquote>تسوق معدات السلامة من ESCO - معايير عالمية وأسعار منافسة. سلامتك استثمار!</blockquote>",
        "content_en": "<h2>Safety First!</h2><p>Accidents can happen to anyone. Safety equipment is a necessity, not a luxury.</p><h2>Eye Protection</h2><h3>Safety Glasses</h3><p>Essential with saws and drills. Choose ANSI Z87.1 rated glasses with side ventilation.</p><h2>Hearing Protection</h2><h3>Ear Muffs</h3><p>Power tools reach 100+ decibels. Use protection with 25-30 dB reduction rating.</p><h2>Respiratory Protection</h2><h3>Dust Masks</h3><p>Wood and metal dust causes serious respiratory diseases. Use N95 masks minimum.</p><h2>Hand Protection</h2><ul><li><strong>Leather gloves:</strong> General work</li><li><strong>Cut-resistant gloves:</strong> With sharp tools</li><li><strong>Rubber gloves:</strong> For chemicals</li></ul><h2>Foot Protection</h2><p>Steel-toe boots with slip-resistant soles. Essential in any workshop.</p><h2>Additional Equipment</h2><ul><li><strong>Fire extinguisher:</strong> ABC type</li><li><strong>First aid kit</strong></li><li><strong>Fire-resistant work clothing</strong></li><li><strong>Safety harness:</strong> For heights</li></ul><blockquote>Shop safety equipment from ESCO - international standards at competitive prices. Safety is an investment!</blockquote>",
        "status": "published",
        "is_featured": False,
        "published_at": timezone.now() - timedelta(days=15),
        "meta_title": "معدات السلامة المهنية | ESCO",
        "meta_description": "دليل شامل لمعدات السلامة المهنية - نظارات، قفازات، أحذية، كمامات",
        "meta_keywords": "معدات سلامة, سلامة مهنية, نظارات حماية, أحذية سلامة",
        "featured_image_alt": "معدات السلامة المهنية",
        "featured_image_alt_en": "Professional safety equipment",
        "tag_slugs": ["safety-equipment", "hand-tools", "power-tools"],
    },
]

created_count = 0
for article in articles:
    tag_slugs = article.pop("tag_slugs")
    if BlogPost.objects.filter(slug=article["slug"]).exists():
        print(f"Already exists: {article['slug']}")
        continue

    post = BlogPost(**article, author=author)
    post.save()

    for ts in tag_slugs:
        if ts in tags:
            post.tags.add(tags[ts])

    created_count += 1
    print(f"Created: {post.slug}")

print(f"\nDone! Created {created_count} articles. Total: {BlogPost.objects.count()}")
