import unittest
import numpy as np
from skymap.labeling.labeledpoint import LabeledPoint, Candidate, Point
from skymap.labeling.runner import BoundingBox


class CandidateTest(unittest.TestCase):
    def test_overlap(self):
        bb = BoundingBox(0, 0, 1, 1)
        p = np.array((0.75, 0.5))
        lp = LabeledPoint(p, 0, "Bla", 12, 0)
        lp.width = 1.0
        lp.height = 0.5
        c = Candidate(lp, 0, 0)
        self.assertEquals(c.minx, 0.75)
        self.assertEquals(c.maxx, 1.75)
        self.assertEquals(c.miny, 0.25)
        self.assertEquals(c.maxy, 0.75)

        self.assertEquals(c.intersection_rectangle(bb, False), 0.125)
        self.assertEquals(c.area(), 0.5)

        p2 = Point(np.array((0.25, 0.75)), 0.25)
        self.assertEquals(c.intersection_point(p2), 0)
