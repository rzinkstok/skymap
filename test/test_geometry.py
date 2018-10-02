import unittest
import numpy as np
from skymap.geometry import *


class RotationTest(unittest.TestCase):
    def test_rotation(self):
        r = rotation_matrix((1, 0, 0), np.pi/2)
        p = (0, 1, 0)
        self.assertTrue(np.allclose(np.dot(r, p), (0, 0, 1)))

    def test_sky2cartesian(self):
        r = np.array(((0, 0),))
        self.assertTrue(np.allclose(sky2cartesian(r), (1, 0, 0)))


class RectangleTest(unittest.TestCase):
    def test_center(self):
        r = Rectangle(Point(1, 2), Point(5, 3))
        p = Point(3.0, 2.5)
        self.assertEqual(r.center, p)

    def test_overlap(self):
        r1 = Rectangle(Point(0, 0), Point(1,1))
        r2 = Rectangle(Point(0.5, 0), Point(1.5, 1))
        self.assertEqual(r1.overlap(r2), 0.5)

        c1 = Circle(Point(1, 0.5), 0.5)
        self.assertEqual(r1.overlap(c1), 0.5)

        c2 = Circle(Point(4, 0), 0.5)
        self.assertEqual(r1.overlap(c2), 0)

        r3 = Rectangle(Point(-44.1658022222, 1.05834038889), Point(44.1658022222, 4.97850936111))
        c3 = Circle(Point(-1, 0), 0.5)
        c4 = Circle(Point(1, 0), 0.5)
        c5 = Circle(Point(1, 1), 0.5)

        self.assertEqual(r3.overlap(c3), 0)
        self.assertEqual(r3.overlap(c4), 0)
        self.assertEqual(r3.overlap(c5), 0.44165961110999996)