import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSLATIONS_DIR = os.path.join(BASE_DIR, "translations")

# Human-readable names for language codes
LANGUAGES = {
    "en": "English",
    "hi": "हिंदी (Hindi)",
    "mr": "मराठी (Marathi)",
    "es": "Español (Spanish)",
    "fr": "Français (French)",
    "de": "Deutsch (German)",
    "gu": "ગુજરાતી (Gujarati)",
    "bn": "বাংলা (Bengali)",
    "ta": "தமிழ் (Tamil)",
    "kn": "ಕನ್ನಡ (Kannada)"
}

_cache = {}

def load_translations(lang):
    if lang in _cache:
        return _cache[lang]
        
    file_path = os.path.join(TRANSLATIONS_DIR, f"{lang}.json")
    if not os.path.exists(file_path):
        # Fallback to English
        file_path = os.path.join(TRANSLATIONS_DIR, "en.json")
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            translations = json.load(f)
            _cache[lang] = translations
            return translations
    except Exception as e:
        print(f"[TRANSLATION ERROR] Failed to load translations for {lang}: {e}", flush=True)
        return {}

def translate(lang, key, default=None):
    if not lang:
        lang = "en"
    lang = lang.lower().strip()
    if lang not in LANGUAGES:
        lang = "en"
        
    translations = load_translations(lang)
    val = translations.get(key)
    if val is not None:
        return val
        
    # Fallback to English if translation is missing in the chosen language
    if lang != "en":
        en_translations = load_translations("en")
        en_val = en_translations.get(key)
        if en_val is not None:
            return en_val
            
    return default if default is not None else key
