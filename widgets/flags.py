import math

from kivy.graphics import (
    Color, Ellipse, Line, Mesh, Rectangle,
    StencilPop, StencilPush, StencilUnUse, StencilUse,
)
from kivy.uix.widget import Widget


class _FlagBase(Widget):
    """Flags are drawn with canvas instructions (no image files needed)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *_):
        self.canvas.clear()
        with self.canvas:
            self._draw(self.x, self.y, self.width, self.height)

    def _draw(self, x, y, w, h):
        raise NotImplementedError


class FlagTR(_FlagBase):
    RED = (0.89, 0.04, 0.12, 1)

    def _draw(self, x, y, w, h):
        u = h / 2.0  # flag is 3u x 2u

        Color(*self.RED)
        Rectangle(pos=(x, y), size=(w, h))

        # crescent: white circle minus a slightly smaller, shifted red circle
        cx, cy = x + 0.75 * u, y + 1.0 * u
        Color(1, 1, 1, 1)
        Ellipse(pos=(cx - 0.5 * u, cy - 0.5 * u), size=(1.0 * u, 1.0 * u))
        Color(*self.RED)
        icx = cx + 0.125 * u
        Ellipse(pos=(icx - 0.4 * u, cy - 0.4 * u), size=(0.8 * u, 0.8 * u))

        # five-point star
        sx, sy, r_out = x + 1.4 * u, cy, 0.25 * u
        r_in = r_out * 0.382
        verts = [sx, sy, 0, 0]
        for i in range(11):
            ang = math.radians(i * 36)
            r = r_out if i % 2 == 0 else r_in
            verts += [sx + r * math.cos(ang), sy + r * math.sin(ang), 0, 0]
        Color(1, 1, 1, 1)
        Mesh(vertices=verts, indices=list(range(12)), mode="triangle_fan")


class FlagEN(_FlagBase):
    BLUE = (0.00, 0.14, 0.49, 1)
    RED = (0.81, 0.08, 0.17, 1)

    def _draw(self, x, y, w, h):
        # clip everything to the flag rectangle
        StencilPush()
        Rectangle(pos=(x, y), size=(w, h))
        StencilUse()

        Color(*self.BLUE)
        Rectangle(pos=(x, y), size=(w, h))

        # diagonals: white wide, red thin
        Color(1, 1, 1, 1)
        Line(points=[x, y, x + w, y + h], width=0.2 * h, cap="none")
        Line(points=[x, y + h, x + w, y], width=0.2 * h, cap="none")
        Color(*self.RED)
        Line(points=[x, y, x + w, y + h], width=0.07 * h, cap="none")
        Line(points=[x, y + h, x + w, y], width=0.07 * h, cap="none")

        # cross: white wide, red thin
        cx, cy = x + w / 2.0, y + h / 2.0
        Color(1, 1, 1, 1)
        Rectangle(pos=(x, cy - 0.17 * h), size=(w, 0.34 * h))
        Rectangle(pos=(cx - 0.17 * h, y), size=(0.34 * h, h))
        Color(*self.RED)
        Rectangle(pos=(x, cy - 0.1 * h), size=(w, 0.2 * h))
        Rectangle(pos=(cx - 0.1 * h, y), size=(0.2 * h, h))

        StencilUnUse()
        Rectangle(pos=(x, y), size=(w, h))
        StencilPop()
