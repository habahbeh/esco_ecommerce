import re
from . import knowledge


def detect_language(text):
    arabic_words = len(re.findall(r'[؀-ۿ]+', text))
    latin_words = len(re.findall(r'[a-zA-Z]+', text))
    if arabic_words > latin_words:
        return 'ar'
    if latin_words > arabic_words:
        return 'en'
    if arabic_words > 0:
        return 'ar'
    return 'ar'


def build_system_prompt(settings, language='ar'):
    custom_prompt = settings.system_prompt_ar if language == 'ar' else (settings.system_prompt_en or settings.system_prompt_ar)
    if custom_prompt:
        if not settings.show_price_in_response:
            custom_prompt += "\n\nIMPORTANT: NEVER mention prices or costs — direct the customer to the product page for pricing."
        return custom_prompt

    price_rule = ""
    if settings.show_price_in_response:
        product_format = '"ID:NUMBER | Name | Price | ..."'
        price_rule = "- WRONG: describing product name/price in text when using [PRODUCT:] tags"
    else:
        product_format = '"ID:NUMBER | Name"'
        price_rule = "- NEVER mention prices or costs — direct the customer to the product page for pricing"

    return f"""You are ESCO's sales assistant (esco.jo) — an industrial equipment store in Jordan.

RULES:
- Reply in the SAME language the customer uses (Arabic or English only, NEVER Chinese/Japanese/Korean)
- Default to Arabic if unsure
- NEVER use Markdown (no ** ## * _ ` symbols)
- Keep responses short: 2-4 sentences + product tags
- Each numbered item on its own line

PRODUCTS:
- Context below lists products as {product_format}
- Use [PRODUCT:NUMBER] with the EXACT numeric ID from context
- NEVER invent IDs or repeat product details in text — the system shows a card automatically
- If no products in context, do NOT use [PRODUCT:] tags
- Example: "إليك بعض الخيارات:\\n\\n[PRODUCT:42]\\n[PRODUCT:15]\\n\\nهل تريد تفاصيل أكثر؟"
{price_rule}

COMPARE: use [COMPARE:id1,id2] with exact IDs from context

LEADS: if customer wants to order/quote, suggest sharing their address for delivery.

ESCO (إسكو) — Jordan, industrial equipment and supplies."""


def build_messages(settings, user_message, conversation_history, language='ar'):
    msg_language = detect_language(user_message)

    system_prompt = build_system_prompt(settings, msg_language)
    knowledge_context = _gather_knowledge(settings, user_message, msg_language)

    if settings.show_categories_in_response:
        categories_context = knowledge.get_categories_tree(msg_language)
        if categories_context:
            system_prompt += f"\n\nAvailable store categories (use these to guide the customer):\n{categories_context}"

    if knowledge_context:
        system_prompt += f"\n\nAvailable information (use [PRODUCT:id] with the EXACT numeric ID shown below — do NOT invent IDs):\n{knowledge_context}"

    messages = [{"role": "system", "content": system_prompt}]

    history_limit = min(settings.max_history_messages, 6)
    for msg in conversation_history[-history_limit:]:
        messages.append({"role": msg['role'], "content": msg['content']})

    messages.append({"role": "user", "content": user_message})
    return messages, msg_language


def parse_response(response_text, language='ar', chatbot_settings=None):
    if not response_text:
        fallback = 'عذراً، لم أتمكن من الرد. حاول مرة أخرى.' if language == 'ar' else 'Sorry, I could not respond. Please try again.'
        return {'text': fallback, 'rich_content': {}, 'quick_replies': []}

    rich_content = {}
    clean_text = response_text

    product_matches = re.findall(r'\[PRODUCT:(\d+)\]', response_text)
    if product_matches:
        product_ids = list(dict.fromkeys(int(pid) for pid in product_matches))
        products = knowledge.get_products_for_comparison(product_ids, chatbot_settings=chatbot_settings)
        if products:
            rich_content = {'type': 'product_cards', 'products': products}
        for pid in product_matches:
            clean_text = clean_text.replace(f'[PRODUCT:{pid}]', '')
    clean_text = re.sub(r'\[PRODUCT:[^\]]+\]', '', clean_text)

    compare_matches = re.findall(r'\[COMPARE:([\d,]+)\]', response_text)
    if compare_matches:
        product_ids = list(dict.fromkeys(int(pid) for pid in compare_matches[0].split(',')))
        products = knowledge.get_products_for_comparison(product_ids, chatbot_settings=chatbot_settings)
        if products:
            rich_content = {'type': 'comparison', 'products': products}
        for match in compare_matches:
            clean_text = clean_text.replace(f'[COMPARE:{match}]', '')
    clean_text = re.sub(r'\[COMPARE:[^\]]+\]', '', clean_text)

    clean_text = clean_text.strip()
    clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)
    clean_text = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_text)
    clean_text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', clean_text)
    clean_text = re.sub(r'^#{1,6}\s+', '', clean_text, flags=re.MULTILINE)
    clean_text = re.sub(r'```[\s\S]*?```', '', clean_text)
    clean_text = re.sub(r'`(.+?)`', r'\1', clean_text)
    clean_text = re.sub(r'[一-鿿㐀-䶿　-〿぀-ゟ゠-ヿ가-힯ᄀ-ᇿ]+', '', clean_text)
    clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)
    clean_text = clean_text.strip()

    quick_replies = _generate_quick_replies(clean_text, rich_content, language)

    return {
        'text': clean_text,
        'rich_content': rich_content,
        'quick_replies': quick_replies,
    }


def _gather_knowledge(settings, user_message, language):
    parts = []

    qa_match = knowledge.match_custom_qa(user_message, language)
    if qa_match:
        parts.append(f"Custom Q&A match: Q: {qa_match['question']} A: {qa_match['answer']}")

    if settings.enable_product_search:
        products = knowledge.search_products(user_message, limit=3, chatbot_settings=settings)
        if products:
            product_info = []
            for p in products:
                name = p['name'] if language == 'ar' else (p.get('name_en') or p['name'])
                if settings.show_price_in_response and p.get('price'):
                    info = f"- ID:{p['id']} | {name} | {p['price']} JOD"
                else:
                    info = f"- ID:{p['id']} | {name}"
                product_info.append(info)
            parts.append("Products found:\n" + "\n".join(product_info))

    if settings.enable_blog_search:
        blogs = knowledge.search_blog(user_message, limit=2)
        if blogs:
            blog_info = [f"- {b['title']} ({b['url']})" for b in blogs]
            parts.append("Related articles:\n" + "\n".join(blog_info))

    return "\n\n".join(parts) if parts else ''


def _generate_quick_replies(text, rich_content, language):
    replies = []
    if rich_content.get('type') == 'product_cards':
        products = rich_content.get('products', [])
        if len(products) >= 2:
            ids_str = ','.join(str(p['id']) for p in products[:3])
            replies.append({
                'text': 'قارن هذه المنتجات' if language == 'ar' else 'Compare these products',
                'action': 'compare',
                'data': ids_str,
            })
        if products:
            name = products[0]['name'] if language == 'ar' else (products[0].get('name_en') or products[0]['name'])
            replies.append({
                'text': 'أخبرني المزيد عن الأول' if language == 'ar' else 'Tell me more about the first one',
                'action': 'message',
                'data': f"أخبرني المزيد عن {name}" if language == 'ar' else f"Tell me more about {name}",
            })

    if not replies:
        if language == 'ar':
            replies = [
                {'text': 'ما هي أحدث المنتجات؟', 'action': 'message', 'data': 'ما هي أحدث المنتجات؟'},
                {'text': 'هل لديكم عروض؟', 'action': 'message', 'data': 'هل لديكم عروض خاصة؟'},
            ]
        else:
            replies = [
                {'text': 'What are the latest products?', 'action': 'message', 'data': 'What are the latest products?'},
                {'text': 'Any special offers?', 'action': 'message', 'data': 'Do you have any special offers?'},
            ]

    return replies
