from django.db import migrations


ABOUT_AR = """\
<p>تأسست شركة المخازن الهندسية للتجارة والصناعة عام 1994، وهي شركة للبيع المباشر للمستهلك. وتقدم الشركة خدمات ما بعد البيع كما تقوم الشركة بالمساعدة بتأسيس المصانع بالكامل، وقد اتجهت شركة المخازن الهندسية للتجارة والصناعة عام 2007 الى تنويع انشطتها، فقامت بتوسيع نطاق خبراتها بحيث يشمل الاستشارات الصناعية.</p>
<p>ويبلغ عدد الأصناف التي تتعامل بها الشركة ما فوق 60000 صنف. وقامت الشركة بطباعة نشرة ارشادية توضح الأصناف التي تتعامل بها الشركة وتطبيق نظام البار كود.</p>
<p>تتفوق شركة المخازن الهندسية للتجارة والصناعة في إقامة علاقات تعاونية دائمة مع عملائها من خلال التقنيات المبتكرة وحلول تحسين الأداء. ونتيجة لخبرات الشركة المشهود بها بالإضافة إلى الجودة العالية التي تمتاز بها خدماتها وحجم قاعدة عملائها، فقد اثبتت الشركة أنها إحدى الشركات الرائدة في مجال البيع المباشر للمصانع.</p>
<p>تتمثل مهمة الشركة في مواصلة العمل على زيادة تغطيتها الجغرافية لتتصدر قائمة الشركات المتقدمة على المستوى الاقليمي. وبفضل وجود كوادر بارعة بالشركة، من مديري مشروعات ومهندسين ومتمرسين، تضمن توفر أكثر الموارد المناسبة عند الحاجة إليها وتوصيل البضاعة للمصانع بالوقت المناسب دون تأخير.</p>
<p>إن هدف الشركة تأمين كافة لوازم المصانع حتى تتمكن المصانع من ايجاد منتجاتهم تحت سقف واحد - نقطة تسوق واحدة لمصنعك.</p>
"""

ABOUT_EN = """\
<p>Engineering Stores for Trading and Industry (ESCO) was founded in 1994 as a direct-to-consumer company. ESCO provides comprehensive after-sales services and assists in establishing complete factories. In 2007, the company diversified its activities, expanding its expertise to include industrial consulting services.</p>
<p>The company handles over 60,000 product items and has published a detailed catalog describing its full product range, along with an implemented barcode system.</p>
<p>ESCO excels at building lasting, cooperative relationships with its clients through innovative technology and performance-improvement solutions. Thanks to its recognized expertise, the high quality of its services, and its large customer base, ESCO has proven itself a leader in direct sales to factories.</p>
<p>The company's mission is to continuously expand its geographic reach to lead the list of advanced companies at the regional level. With a talented team of project managers, engineers, and seasoned specialists, ESCO ensures that the right resources are available when needed and that goods are delivered to factories on time, without delay.</p>
<p>ESCO's goal is to supply all factory needs so that manufacturers can find their products under one roof — a single shopping point for your factory.</p>
"""


def seed_about(apps, schema_editor):
    StaticContent = apps.get_model('core', 'StaticContent')
    StaticContent.objects.update_or_create(
        key='about',
        defaults={'content_ar': ABOUT_AR, 'content_en': ABOUT_EN},
    )


def unseed_about(apps, schema_editor):
    StaticContent = apps.get_model('core', 'StaticContent')
    StaticContent.objects.filter(key='about').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_slideritem_description_en_slideritem_subtitle_en_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_about, unseed_about),
    ]
