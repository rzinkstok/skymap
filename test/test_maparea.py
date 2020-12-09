import unittest
from skymap.tikz import Tikz
from skymap.geometry import Point
from skymap.map import MapArea


class MapAreaTest(unittest.TestCase):
    def test_picture(self):
        t = Tikz("maparea_test1")
        m = MapArea(t, Point(20, 20), Point(190, 277))
        t.render()
