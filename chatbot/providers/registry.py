from django.utils.module_loading import import_string

PROVIDER_MAP = {
    'openrouter': 'chatbot.providers.openrouter.OpenRouterProvider',
    'openai': 'chatbot.providers.openai_provider.OpenAIProvider',
    'anthropic': 'chatbot.providers.anthropic_provider.AnthropicProvider',
    'google': 'chatbot.providers.google_provider.GoogleProvider',
}


def get_provider(chatbot_settings):
    provider_path = PROVIDER_MAP.get(chatbot_settings.provider, PROVIDER_MAP['openrouter'])
    provider_class = import_string(provider_path)
    api_key = chatbot_settings.api_key or ''
    return provider_class(
        api_key=api_key,
        model=chatbot_settings.model_name,
        temperature=float(chatbot_settings.temperature),
        max_tokens=min(chatbot_settings.max_tokens, 512),
    )


def get_all_providers_models():
    result = {}
    for key, path in PROVIDER_MAP.items():
        cls = import_string(path)
        result[key] = cls.get_available_models()
    return result
