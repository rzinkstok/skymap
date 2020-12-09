import unittest
from skymap.tikz import Tikz, PaperSize, PaperMargin
from skymap.geometry import Point, Label
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
            PaperMargin(12, 14, 12, 20),
            normalsize=10,
        )
        m = MapLegend(t, t.llcorner + Point(264, 0), t.urcorner)

        m.draw_label(Label(Point(8, 189), text="Epoch", fontsize="tiny"))
        m.draw_label(
            Label(Point(8, 185), text="2000.0", fontsize="normalsize", bold=True)
        )

        # l.draw_label(GridLineLabel(Point(8, 189), "Epoch", 90, "tiny"))
        # l.draw_label(GridLineLabel(Point(8, 185), "\\textbf{2000.0}", 90, "normalsize"))
        # l.draw_line(Line(Point(2, 183.5), Point(14, 183.5)))
        # l.draw_line(Line(Point(2, 15), Point(14, 15)))
        # l.draw_label(GridLineLabel(Point(8, 11), "Chart number", 90, "tiny"))
        # l.draw_label(
        #     GridLineLabel(
        #         Point(8, 2), "\\textbf{{{}}}".format(chart_number), 90, "Huge"
        #     )
        # )
        t.render()
