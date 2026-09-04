import sys
from pathlib import Path

from kivy.app import App
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.graphics import Color, RoundedRectangle


class BaseRoasterScreen(Screen):
    """
    Shared behavior for every screen: which tab lights up on entry, how
    the current Modbus client is found, safe PLC read/write wrappers,
    the project root, and the toast popup. Change it once here instead
    of in every screen that needs it.
    """

    # Subclasses override this with their own tab name ("live", "manual", ...)
    active_tab_name = "home"

    def on_enter(self, *args):
        try:
            App.get_running_app().active_tab = self.active_tab_name
        except Exception:
            pass

    # ---------------------------------------------------------
    # Modbus client lookup
    # ---------------------------------------------------------
    def _get_modbus_client(self):
        try:
            if self.manager and self.manager.has_screen("live"):
                live = self.manager.get_screen("live")
                c = getattr(live, "client", None)
                if c:
                    return c
        except Exception:
            pass

        app = App.get_running_app()
        for attr in ("modbus_client", "modbus", "client"):
            c = getattr(app, attr, None)
            if c:
                return c
        return None

    # ---------------------------------------------------------
    # Safe PLC read/write wrappers
    # ---------------------------------------------------------
    def _read_n_safe(self, client, start_reg: int, qty: int):
        try:
            r = client.read_holding_n(start_reg, qty)
            if isinstance(r, tuple) and len(r) == 2:
                values, err = r
                if err:
                    return None
                return values
            return r
        except Exception:
            return None

    def _read_one_safe(self, client, reg: int):
        vals = self._read_n_safe(client, int(reg), 1)
        if vals and isinstance(vals, (list, tuple)) and len(vals) >= 1:
            return vals[0]
        return None

    def _write_reg_safe(self, client, reg: int, value: int):
        try:
            r = client.write_single_register(int(reg), int(value))
            if isinstance(r, tuple) and len(r) == 2:
                ok, err = r
                return bool(ok), err
            return bool(r), None
        except Exception as e:
            return False, str(e)

    def _write_coil_safe(self, client, coil: int, value: int):
        try:
            r = client.write_single_coil(int(coil), int(value))
            if isinstance(r, tuple) and len(r) == 2:
                ok, err = r
                return bool(ok), err
            return bool(r), None
        except Exception as e:
            return False, str(e)

    # ---------------------------------------------------------
    # Filesystem
    # ---------------------------------------------------------
    def _project_root(self) -> Path:
        try:
            if getattr(sys, "frozen", False):
                return Path(sys.executable).resolve().parent
            return Path(__file__).resolve().parents[1]
        except Exception:
            return Path(".").resolve()

    # ---------------------------------------------------------
    # Toast
    # ---------------------------------------------------------
    def _toast(self, msg: str):
        inner = BoxLayout(orientation="vertical", spacing=dp(14), padding=(dp(16), dp(14)))

        lbl = Label(
            text=msg,
            font_size="20sp",
            bold=True,
            color=(1, 1, 1, 1),
            halign="center",
            valign="top",
        )
        lbl.bind(size=lambda w, *_: setattr(w, "text_size", (w.width, None)))
        lbl.bind(texture_size=lambda w, *_: setattr(w, "height", w.texture_size[1] + dp(10)))
        inner.add_widget(lbl)

        btn = Factory.RoundedPopupButton(text="OK")
        inner.add_widget(btn)

        card = BoxLayout(orientation="vertical", padding=dp(16))
        card.add_widget(inner)

        def _redraw(*_):
            card.canvas.before.clear()
            with card.canvas.before:
                Color(0.12, 0.13, 0.16, 1)
                RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(22)] * 4)

        card.bind(pos=_redraw, size=_redraw)
        _redraw()

        pop = Popup(
            title="",
            content=card,
            size_hint=(None, None),
            size=(dp(520), dp(240)),
            auto_dismiss=False,
            separator_height=0,
            background="",
            background_color=(0, 0, 0, 0),
        )

        btn.bind(on_release=lambda *_: pop.dismiss())
        pop.open()
