SUPPORTED_LANGUAGES = [
    {"code": "pt-PT", "label": "Portuguese", "region": "Europe", "speech_locale": "pt-PT"},
    {"code": "en-GB", "label": "English", "region": "Europe", "speech_locale": "en-GB"},
    {"code": "fr-FR", "label": "French", "region": "Europe", "speech_locale": "fr-FR"},
    {"code": "es-ES", "label": "Spanish", "region": "Europe", "speech_locale": "es-ES"},
    {"code": "de-DE", "label": "German", "region": "Europe", "speech_locale": "de-DE"},
    {"code": "it-IT", "label": "Italian", "region": "Europe", "speech_locale": "it-IT"},
    {"code": "uk-UA", "label": "Ukrainian", "region": "Europe", "speech_locale": "uk-UA"},
    {"code": "ar", "label": "Arabic", "region": "Africa / Middle East", "speech_locale": "ar"},
    {"code": "hi-IN", "label": "Hindi", "region": "Asia", "speech_locale": "hi-IN"},
    {"code": "bn-BD", "label": "Bengali", "region": "Asia", "speech_locale": "bn-BD"},
    {"code": "ur-PK", "label": "Urdu", "region": "Asia", "speech_locale": "ur-PK"},
    {"code": "zh-CN", "label": "Mandarin Chinese", "region": "Asia", "speech_locale": "zh-CN"},
]

SUPPORTED_LANGUAGE_CODES = {language["code"] for language in SUPPORTED_LANGUAGES}
