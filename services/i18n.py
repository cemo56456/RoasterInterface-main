"""
Tiny translation table. Add a key to every language in STRINGS, then use it:

  KV:      text: app.t("settings", app.lang)      # re-renders when app.lang changes
  Python:  App.get_running_app().t("settings")

Missing key -> English text -> the key itself, so nothing ever crashes.
"""

DEFAULT_LANG = "en"
LANGUAGES = ("tr", "en")

STRINGS = {
    "en": {
        "back": "Back",
        "settings": "Settings",
        "apply": "Apply",

        "sec_profile": "PROFILE",
        "profile_style": "Roasting Profile Style",
        "active_in_plc": "Active in PLC: {}",
        "standard": "STANDARD",
        "dev_time": "DEV TIME",

        "sec_general": "GENERAL",
        "language": "Language",
        "language_desc": "Application interface language",

        "err_no_plc": "No PLC connection",
        "err_plc_write": "MW{reg} write FAIL: {err}",
        "err_save": "Applied, but could not save settings.json: {err}",
    },
    "tr": {
        "back": "Geri",
        "settings": "Ayarlar",
        "apply": "Uygula",

        "sec_profile": "PROFİL",
        "profile_style": "Kavurma Profil Stili",
        "active_in_plc": "PLC'de aktif: {}",
        "standard": "STANDART",
        "dev_time": "DEV SÜRESİ",

        "sec_general": "GENEL",
        "language": "Dil",
        "language_desc": "Uygulama arayüz dili",

        "err_no_plc": "PLC bağlantısı yok",
        "err_plc_write": "MW{reg} yazma HATASI: {err}",
        "err_save": "Uygulandı ancak settings.json kaydedilemedi: {err}",
    },
}


def translate(key: str, lang: str = DEFAULT_LANG) -> str:
    table = STRINGS.get(lang) or STRINGS[DEFAULT_LANG]
    if key in table:
        return table[key]
    return STRINGS[DEFAULT_LANG].get(key, key)
