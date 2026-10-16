from kivy.properties import StringProperty, BooleanProperty

from screens.base_screen import BaseRoasterScreen
from services.app_settings import save_settings


class SettingsScreen(BaseRoasterScreen):
    """
    Settings list. Opened by long-pressing the plot on the Live screen.

    Layout lives in ui/settings.kv as a vertical list of SettingRow items
    grouped under SettingSection headers. To add a setting: add a row in
    the KV, add its pending/current properties here, extend
    _update_can_apply() and apply().

    Current rows:
      - Roasting Profile Style (STD / DEV) -> MW615
    """

    active_tab_name = "live"

    REG_PROFILE_MODE_WRITE = 615

    # ---- Roasting Profile Style ----
    current_mode = StringProperty("standard")   # what the PLC has now
    selected_mode = StringProperty("standard")  # what the user picked

    last_msg = StringProperty("")
    can_apply = BooleanProperty(False)

    # ---------------------------------------------------------
    # lifecycle
    # ---------------------------------------------------------
    def on_enter(self, *args):
        super().on_enter(*args)
        self.current_mode = self._read_current_mode()
        self.selected_mode = self.current_mode
        self.last_msg = ""
        self._update_can_apply()

    def on_selected_mode(self, *_):
        self._update_can_apply()

    def _update_can_apply(self):
        self.can_apply = self.selected_mode != self.current_mode

    def go_back(self):
        try:
            if self.manager:
                self.manager.current = "live"
        except Exception:
            pass

    # ---------------------------------------------------------
    # helpers
    # ---------------------------------------------------------
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
    # Roasting Profile Style
    # ---------------------------------------------------------
    def select_mode(self, mode: str):
        self.selected_mode = "dev" if mode == "dev" else "standard"

    # ---------------------------------------------------------
    # Apply (writes every changed setting, then returns to Live)
    # ---------------------------------------------------------
    def apply(self):
        if not self.can_apply:
            return

        client = self._get_modbus_client()
        if client is None:
            self.last_msg = "No PLC connection"
            return

        if self.selected_mode != self.current_mode:
            target = 1 if self.selected_mode == "dev" else 0
            ok, err = self._write_reg_safe(client, self.REG_PROFILE_MODE_WRITE, target)
            if not ok:
                self.last_msg = f"MW{self.REG_PROFILE_MODE_WRITE} write FAIL: {err}"
                return

            live = self._live()
            if live is not None:
                live.profile_mode = self.selected_mode
                live.last_read = f"MW{self.REG_PROFILE_MODE_WRITE} <= {target}"

            self.current_mode = self.selected_mode

        # PLC'ye yazılanı diske de kaydet (uygulama yeniden açılınca geri yüklenir)
        ok, err = save_settings({"profile_mode": self.current_mode})
        if not ok:
            self.last_msg = f"Applied, but could not save settings.json: {err}"
            self._update_can_apply()
            return

        self._update_can_apply()
        self.go_back()
