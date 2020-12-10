import unittest
from skymap.tikz import Tikz, PaperSize, PaperMargin
from skymap.geometry import Point, Label, Line
from skymap.map import MapArea, MapLegend


LEFT_MARGIN = 12
RIGHT_MARGIN = 12
BOTTOM_MARGIN = 14
TOP_MARGIN = 20


class MapInterfaceTest(unittest.TestCase):
    def test_interface(self):
        t = Tikz(
            "map_test1",
            PaperSize(width=304, height=228),
            PaperMargin(left=12, bottom=14, right=12, top=20),
            normalsize=10,
        )

        chart_number = 5

        m = MapLegend(t, t.llcorner + Point(264, 0), t.urcorner)

        m.draw_label(Label(Point(8, 189), text="Epoch", fontsize="tiny"))
        m.draw_label(
            Label(Point(8, 185), text="2000.0", fontsize="normalsize", bold=True)
        )

        m.draw_line(Line(Point(2, 183.5), Point(14, 183.5)))

        m.draw_line(Line(Point(2, 15), Point(14, 15)))
        m.draw_label(Label(Point(8, 11), text="Chart number", fontsize="tiny"))
        m.draw_label(Label(Point(8, 2), f"{chart_number}", bold=True, fontsize="Huge"))

        t.render()
