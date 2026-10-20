from kivy.graphics import Color, Line
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.widget import Widget


class HomeIcon(Widget):
    """
    Simple outline house, drawn with canvas lines (no image file needed).

    The house is drawn centered inside the widget's own area, so give the
    widget the size/pos of the button it sits on and tune `scale`
    (fraction of the shorter side). `color` follows the theme.

      HomeIcon:
          pos: self.parent.pos
          size: self.parent.size
          scale: 0.42
    """

    color = ListProperty([0.86, 0.88, 0.92, 1])
    scale = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self._redraw, size=self._redraw,
            color=self._redraw, scale=self._redraw,
        )
        self._redraw()

    def _redraw(self, *_):
        self.canvas.clear()

        s = min(self.width, self.height) * self.scale
        if s <= 0:
            return

        # square drawing area centered in the widget
        x0 = self.x + (self.width - s) / 2.0
        y0 = self.y + (self.height - s) / 2.0

        def p(fx, fy):
            return (x0 + fx * s, y0 + fy * s)

        roof = [*p(0.06, 0.50), *p(0.50, 0.92), *p(0.94, 0.50)]
        body = [*p(0.18, 0.56), *p(0.18, 0.08), *p(0.82, 0.08), *p(0.82, 0.56)]
        door = [*p(0.40, 0.08), *p(0.40, 0.38), *p(0.60, 0.38), *p(0.60, 0.08)]

        with self.canvas:
            Color(*self.color)
            w = max(1.5, s * 0.07)
            for pts in (roof, body, door):
                Line(points=pts, width=w, joint="round", cap="round")
