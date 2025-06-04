from importlib import import_module


current_language = {"lang": "en"}

def set_language(lang):
    print(f"🔁 Установка языка: {lang}")
    current_language["lang"] = lang

def get_current_language():
    print(f"📦 Текущий язык: {current_language['lang']}")
    return current_language["lang"]


_translation_cache = {}


def get_translation(key, module="shared_translation"):
    lang = current_language["lang"]

    if module not in _translation_cache:
        mod = import_module(f"client.translation.{module}")
        _translation_cache[module] = mod.translations

    translations = _translation_cache[module]
    entry = translations.get(key)

    if not entry:
        return key  # ключ не найден вообще

    # добавляем fallback на английский, если нужный язык отсутствует
    text = entry.get(lang) or entry.get("en") or key

    if lang == "he" and isinstance(text, str):
        return " ".join(text.split()[::-1])

    return text

