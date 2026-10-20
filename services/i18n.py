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
        "standard": "STANDARD TYPE",
        "dev_time": "DEVELOPMENT TYPE",

        "sec_general": "GENERAL",
        "language": "Language",
        "language_desc": "Application interface language",

        "err_no_plc": "No PLC connection",
        "err_plc_write": "MW{reg} write FAIL: {err}",
        "err_save": "Applied, but could not save settings.json: {err}",

        # ---- Manual Control ----
        "manual_control": "Manual Control",
        "set_value": "SET VALUE",
        "exhaust_temp": "Exhaust Temp",
        "drum_temp": "Drum Temp",
        "burner_pct": "Burner %",
        "exhaust_pct": "Exhaust %",
        "drum_pct": "Drum %",
        "cooling_time": "Cooling Time",
        "mixer_on": "Mixer ON",
        "mixer_off": "Mixer OFF",
        "tap_to_edit": "Tap to edit",
        "sec": "sec",

        "drum": "Drum",
        "burner": "Burner",
        "mixer": "Mixer",
        "cooler": "Cooler",
        "destoner": "Destoner",
        "cooling": "Cooling",
        "shut_down": "Shut Down",
        "start": "START",
        "stop": "STOP",

        "edit_set_value": "Set Value (°C)",
        "edit_burner": "Burner (%)",
        "edit_exhaust": "Exhaust (%)",
        "edit_drum": "Drum (%)",
        "edit_cooling_time": "Cooling Time (sec)",
        "edit_mixer_on": "Mixer ON Time (sec)",
        "edit_mixer_off": "Mixer OFF Time (sec)",

        "msg_client_ok": "Connection ready",
        "msg_no_client": "No connection",

        # ---- Live Roast (top tabs + left panel) ----
        "tab_make_profile": "Make Profile",
        "tab_profile": "Profile",
        "live_set_value": "Set Value",
        "live_bean_temp": "Bean Temp",
        "live_exhaust_temp": "Exhaust TEMP",
        "live_exhaust": "Exhaust",
        "live_burner": "Burner",
        "live_airflow": "Airflow",

        # ---- Home ----
        "touch_to_start": "Touch to start",
    },
    "tr": {
        "back": "Geri",
        "settings": "Ayarlar",
        "apply": "Uygula",

        "sec_profile": "PROFİL",
        "profile_style": "Kavurma Profil Stili",
        "active_in_plc": "PLC'de aktif: {}",
        "standard": "STANDART TİP",
        "dev_time": "DEVELOPMENT TİPİ",

        "sec_general": "GENEL",
        "language": "Dil",
        "language_desc": "Uygulama arayüz dili",

        "err_no_plc": "PLC bağlantısı yok",
        "err_plc_write": "MW{reg} yazma HATASI: {err}",
        "err_save": "Uygulandı ancak settings.json kaydedilemedi: {err}",

        # ---- Manual Control ----
        "manual_control": "Manuel Kontrol",
        "set_value": "AYAR DEĞERİ",
        "exhaust_temp": "Egzoz Sıcaklığı",
        "drum_temp": "Tambur Sıcaklığı",
        "burner_pct": "Brülör %",
        "exhaust_pct": "Egzoz %",
        "drum_pct": "Tambur %",
        "cooling_time": "Soğutma Süresi",
        "mixer_on": "Karıştırıcı AÇIK",
        "mixer_off": "Karıştırıcı KAPALI",
        "tap_to_edit": "Düzenlemek için dokun",
        "sec": "sn",

        "drum": "Tambur",
        "burner": "Brülör",
        "mixer": "Karıştırıcı",
        "cooler": "Soğutucu",
        "destoner": "Taş Ayırıcı",
        "cooling": "Soğutma",
        "shut_down": "Kapatma",
        "start": "BAŞLAT",
        "stop": "DURDUR",

        "edit_set_value": "Ayar Değeri (°C)",
        "edit_burner": "Brülör (%)",
        "edit_exhaust": "Egzoz (%)",
        "edit_drum": "Tambur (%)",
        "edit_cooling_time": "Soğutma Süresi (sn)",
        "edit_mixer_on": "Karıştırıcı AÇIK Süresi (sn)",
        "edit_mixer_off": "Karıştırıcı KAPALI Süresi (sn)",

        "msg_client_ok": "Bağlantı hazır",
        "msg_no_client": "Bağlantı yok",

        # ---- Live Roast (top tabs + left panel) ----
        "tab_make_profile": "Profil Oluştur",
        "tab_profile": "Profil",
        "live_set_value": "Ayar Değeri",
        "live_bean_temp": "Çekirdek Sıcaklığı",
        "live_exhaust_temp": "Egzoz Sıcaklığı",
        "live_exhaust": "Egzoz",
        "live_burner": "Brülör",
        "live_airflow": "Hava Akışı",

        # ---- Home ----
        "touch_to_start": "Başlamak için dokunun",
    },
}


def translate(key: str, lang: str = DEFAULT_LANG) -> str:
    table = STRINGS.get(lang) or STRINGS[DEFAULT_LANG]
    if key in table:
        return table[key]
    return STRINGS[DEFAULT_LANG].get(key, key)
