from kivy.app import App
from kivy.properties import StringProperty, BooleanProperty

from screens.base_screen import BaseRoasterScreen
from services.app_settings import save_settings


class SettingsScreen(BaseRoasterScreen):
    """
    Settings list. Opened by long-pressing the plot on the Live screen.

    Layout lives in ui/settings.kv as a vertical list of SettingRow items
    grouped under SettingSection headers (PROFILE stays on top). To add a
    setting: add a row in the KV, add its current/selected properties here,
    extend _update_can_apply() and apply(), and add its texts to
    services/i18n.py.

    Current rows:
      - Roasting Profile Style (STD / DEV) -> MW615 + settings.json
      - Language (tr / en)                 -> settings.json, app.lang
    """

    active_tab_name = "live"

    REG_PROFILE_MODE_WRITE = 615

    # ---- Roasting Profile Style ----
    current_mode = StringProperty("standard")   # what the PLC has now
    selected_mode = StringProperty("standard")  # what the user picked

    # ---- Language ----
    current_lang = StringProperty("en")
    selected_lang = StringProperty("en")

    last_msg = StringProperty("")
    can_apply = BooleanProperty(False)

    # ---------------------------------------------------------
    # lifecycle
    # ---------------------------------------------------------
    def on_enter(self, *args):
        super().on_enter(*args)
        self.current_mode = self._read_current_mode()
        self.selected_mode = self.current_mode
        self.current_lang = App.get_running_app().lang
        self.selected_lang = self.current_lang
        self.last_msg = ""
        self._update_can_apply()

    def on_selected_mode(self, *_):
        self._update_can_apply()

    def on_selected_lang(self, *_):
        self._update_can_apply()

    def _update_can_apply(self):
        self.can_apply = (
            self.selected_mode != self.current_mode
            or self.selected_lang != self.current_lang
        )

    def go_back(self):
        try:
            if self.manager:
                self.manager.current = "live"
        except Exception:
            pass

    # ---------------------------------------------------------
    # helpers
    # ---------------------------------------------------------
    def _t(self, key, **kw):
        text = App.get_running_app().t(key)
        return text.format(**kw) if kw else text

    def _live(self):
        try:
            if self.manager and self.manager.has_screen("live"):
                return self.manager.get_screen("live")
        except Exception:
            pass
        return None

    def _read_current_mode(self) -> str:
        client = self._get_modbus_client()
        if client is not None:
            v = self._read_one_safe(client, self.REG_PROFILE_MODE_WRITE)
            if v is not None:
                return "dev" if int(v) == 1 else "standard"

        live = self._live()
        if live is not None:
            return "dev" if getattr(live, "profile_mode", "standard") == "dev" else "standard"
        return "standard"

    # ---------------------------------------------------------
    # selections
    # ---------------------------------------------------------
    def select_mode(self, mode: str):
        self.selected_mode = "dev" if mode == "dev" else "standard"

    def select_lang(self, lang: str):
        self.selected_lang = "tr" if lang == "tr" else "en"

    # ---------------------------------------------------------
    # Apply (writes every changed setting, then returns to Live)
    # ---------------------------------------------------------
    def apply(self):
        if not self.can_apply:
            return

        to_save = {}

        # ---- Roasting Profile Style -> PLC ----
        if self.selected_mode != self.current_mode:
            client = self._get_modbus_client()
            if client is None:
                self.last_msg = self._t("err_no_plc")
                return

            target = 1 if self.selected_mode == "dev" else 0
            ok, err = self._write_reg_safe(client, self.REG_PROFILE_MODE_WRITE, target)
            if not ok:
                self.last_msg = self._t(
                    "err_plc_write", reg=self.REG_PROFILE_MODE_WRITE, err=err
                )
                return

            live = self._live()
            if live is not None:
                live.profile_mode = self.selected_mode
                live.last_read = f"MW{self.REG_PROFILE_MODE_WRITE} <= {target}"

            self.current_mode = self.selected_mode

        to_save["profile_mode"] = self.current_mode

        # ---- Language ----
        lang_changed = self.selected_lang != self.current_lang
        to_save["language"] = self.selected_lang

        # Disk'e kaydet (uygulama yeniden açılınca geri yüklenir)
        ok, err = save_settings(to_save)

        if lang_changed:
            App.get_running_app().lang = self.selected_lang
            self.current_lang = self.selected_lang

        if not ok:
            self.last_msg = self._t("err_save", err=err)
            self._update_can_apply()
            return

        self._update_can_apply()
        self.go_back()
