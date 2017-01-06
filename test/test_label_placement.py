import unittest
from skymap.geometry import Point, Circle
from skymap.labels import LabelManager


class test_simple_label(unittest.TestCase):
    def test_label_director(self):
        ld = LabelManager()
        ld.add_object(Circle(Point(-1, 0), 0.5))
        ld.add_object(Circle(Point(1, 0), 0.5))
        ld.add_object(Circle(Point(1, 1), 0.5))
        ld.add_object(Circle(Point(0, -1), 0.5))
        #l = ld.add_label(Point(0, 0), "Testing an impossibly long label between two dots", 'normal')
        #self.assertEqual(l.optimal_position, "lrt")
