import time
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_CHATBOT_ASSET_VERSION = str(int(time.time()))


@register.simple_tag
def chatbot_widget():
    v = _CHATBOT_ASSET_VERSION
    return mark_safe(f'''
<div id="esco-chatbot-root"></div>
<script>
(function(){{
    var loaded = false;
    function loadChatbot(){{
        if(loaded) return;
        loaded = true;
        fetch('/api/chatbot/config/', {{credentials:'same-origin'}})
        .then(function(r){{return r.json()}})
        .then(function(cfg){{
            if(!cfg.enabled) return;
            if(!cfg.show_on_mobile && window.innerWidth < 768) return;
            window.__ESCO_CHATBOT_CONFIG = cfg;
            var link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = '/static/chatbot/css/chatbot-widget.css?v={v}';
            document.head.appendChild(link);
            var script = document.createElement('script');
            script.src = '/static/chatbot/js/chatbot-widget.js?v={v}';
            document.body.appendChild(script);
        }}).catch(function(){{}});
    }}
    if(document.readyState === 'complete'){{
        setTimeout(loadChatbot, 1000);
    }} else {{
        window.addEventListener('load', function(){{setTimeout(loadChatbot, 1000)}});
    }}
}})();
</script>
''')
