import unittest
from skymap.geometry import Point
from skymap.map import Map


class MapTest(unittest.TestCase):
    def setUp(self):
        self.m = Map("Test", None, 297.0, 210.0, 20, 20)

    def test_to_map_coordinates(self):
        dy = float(210 - 40) / (297 - 40)
        self.assertEqual(self.m.point_to_paper(Point(0, 0)), Point(148.5, 105.0))
        self.assertEqual(self.m.point_to_paper(Point(1, dy)), Point(277, 190))
        self.assertEqual(self.m.point_to_paper(Point(-1, dy)), Point(20, 190))
        self.assertEqual(self.m.point_to_paper(Point(-1, -dy)), Point(20, 20))
        self.assertEqual(self.m.point_to_paper(Point(1, -dy)), Point(277, 20))

    def test_inside_viewport(self):
        self.assertTrue(self.m.inside_viewport(Point(100, 100)))
        self.assertFalse(self.m.inside_viewport(Point(100, 250)))

