import unittest
import math
from skymap.projections import AzimuthalEquidistantProjection, EquidistantCylindricalProjection, EquidistantConicProjection
from skymap.geometry import Point, SphericalPoint


class TestAzimuthalEquidistantProjection(unittest.TestCase):
    def setUp(self):
        self.origin = Point(0, 0)
        self.p = AzimuthalEquidistantProjection(reference_longitude=0, reference_scale=40)

    def test_pole(self):
        self.assertEqual(self.p.project(SphericalPoint(0, 90)), self.origin)

    def test_latitude(self):
        self.assertEqual(self.p.project(SphericalPoint(0, 50)), Point(1, 0))
        self.assertEqual(self.p.project(SphericalPoint(90, 50)), Point(0, 1))
        self.assertEqual(self.p.project(SphericalPoint(180, 50)), Point(-1, 0))
        self.assertEqual(self.p.project(SphericalPoint(270, 50)), Point(0, -1))
        self.p.celestial = True
        self.assertEqual(self.p.project(SphericalPoint(0, 50)), Point(1, 0))
        self.assertEqual(self.p.project(SphericalPoint(90, 50)), Point(0, -1))
        self.assertEqual(self.p.project(SphericalPoint(180, 50)), Point(-1, 0))
        self.assertEqual(self.p.project(SphericalPoint(270, 50)), Point(0, 1))

    def test_inverse_project(self):
        self.assertEqual(self.p.inverse_project(Point(1, 0)), SphericalPoint(0, 50))
        self.assertEqual(self.p.inverse_project(Point(0, 1)), SphericalPoint(90, 50))
        self.assertEqual(self.p.inverse_project(Point(-1, 0)), SphericalPoint(180, 50))
        self.assertEqual(self.p.inverse_project(Point(0, -1)), SphericalPoint(270, 50))

        p = SphericalPoint(225, 76)
        pp = self.p.project(p)
        ppp = self.p.inverse_project(pp)
        self.assertEqual(p, ppp)

        self.p.celestial = True
        self.assertEqual(self.p.inverse_project(Point(1, 0)), SphericalPoint(0, 50))
        self.assertEqual(self.p.inverse_project(Point(0, 1)), SphericalPoint(270, 50))
        self.assertEqual(self.p.inverse_project(Point(-1, 0)), SphericalPoint(180, 50))
        self.assertEqual(self.p.inverse_project(Point(0, -1)), SphericalPoint(90, 50))

        p = SphericalPoint(225, 76)
        pp = self.p.project(p)
        ppp = self.p.inverse_project(pp)
        self.assertEqual(p, ppp)

    def test_reference_longitude(self):
        self.p.reference_longitude = 40

        self.assertEqual(self.origin.distance(self.p.project(SphericalPoint(0, 50))), 1.0)
        self.assertEqual(self.p.project(SphericalPoint(40, 50)), Point(1, 0))
        self.assertEqual(self.p.project(SphericalPoint(130, 50)), Point(0, 1))
        self.assertEqual(self.p.project(SphericalPoint(220, 50)), Point(-1, 0))
        self.assertEqual(self.p.project(SphericalPoint(310, 50)), Point(0, -1))

        p = SphericalPoint(225, 76)
        pp = self.p.project(p)
        ppp = self.p.inverse_project(pp)
        self.assertEqual(p, ppp)

        self.p.celestial = True
        self.assertEqual(self.p.project(SphericalPoint(40, 50)), Point(1, 0))
        self.assertEqual(self.p.project(SphericalPoint(130, 50)), Point(0, -1))
        self.assertEqual(self.p.project(SphericalPoint(220, 50)), Point(-1, 0))
        self.assertEqual(self.p.project(SphericalPoint(310, 50)), Point(0, 1))

        p = SphericalPoint(225, 76)
        pp = self.p.project(p)
        ppp = self.p.inverse_project(pp)
        self.assertEqual(p, ppp)

        self.p.celestial = False
        self.p.reference_longitude = -40
        self.assertEqual(self.p.project(SphericalPoint(-40, 50)), Point(1, 0))
        self.assertEqual(self.p.project(SphericalPoint(50, 50)), Point(0, 1))
        self.assertEqual(self.p.project(SphericalPoint(140, 50)), Point(-1, 0))
        self.assertEqual(self.p.project(SphericalPoint(230, 50)), Point(0, -1))

    def test_south_pole(self):
        self.p = AzimuthalEquidistantProjection(north=False, reference_longitude=0, reference_scale=40)

        # Pole
        self.assertEqual(self.p.project(SphericalPoint(0, -90)), self.origin)

        # Project
        self.assertEqual(self.p.project(SphericalPoint(0, -50)), Point(1, 0))
        self.assertEqual(self.p.project(SphericalPoint(90, -50)), Point(0, -1))
        self.assertEqual(self.p.project(SphericalPoint(180, -50)), Point(-1, 0))
        self.assertEqual(self.p.project(SphericalPoint(270, -50)), Point(0, 1))
        self.p.celestial = True
        self.assertEqual(self.p.project(SphericalPoint(0, -50)), Point(1, 0))
        self.assertEqual(self.p.project(SphericalPoint(90, -50)), Point(0, 1))
        self.assertEqual(self.p.project(SphericalPoint(180, -50)), Point(-1, 0))
        self.assertEqual(self.p.project(SphericalPoint(270, -50)), Point(0, -1))

        # Inverse project
        self.p.celestial = False
        self.assertEqual(self.p.inverse_project(Point(1, 0)), SphericalPoint(0, -50))
        self.assertEqual(self.p.inverse_project(Point(0, -1)), SphericalPoint(90, -50))
        self.assertEqual(self.p.inverse_project(Point(-1, 0)), SphericalPoint(180, -50))
        self.assertEqual(self.p.inverse_project(Point(0, 1)), SphericalPoint(270, -50))
        p = SphericalPoint(225, -76)
        pp = self.p.project(p)
        ppp = self.p.inverse_project(pp)
        self.assertEqual(p, ppp)

        self.p.celestial = True
        self.assertEqual(self.p.inverse_project(Point(1, 0)), SphericalPoint(0, -50))
        self.assertEqual(self.p.inverse_project(Point(0, 1)), SphericalPoint(90, -50))
        self.assertEqual(self.p.inverse_project(Point(-1, 0)), SphericalPoint(180, -50))
        self.assertEqual(self.p.inverse_project(Point(0, -1)), SphericalPoint(270, -50))
        p = SphericalPoint(225, -76)
        pp = self.p.project(p)
        ppp = self.p.inverse_project(pp)
        self.assertEqual(p, ppp)

    def test_other_scale(self):
        self.p = AzimuthalEquidistantProjection(reference_longitude=0, reference_scale=80.0/190.0)
        self.assertEqual(self.p.project(SphericalPoint(0, 50)), Point(95, 0))


class TestEquidistantCylindricalProjection(unittest.TestCase):
    def setUp(self):
        self.p = EquidistantCylindricalProjection(center_longitude=0, reference_scale=30, standard_parallel=20)

    def test_longitude(self):
        self.assertEqual(self.p.project(SphericalPoint(0, 0)), Point(0, 0))
        self.assertEqual(self.p.project(SphericalPoint(30, 0)), Point(1, 0))
        self.assertEqual(self.p.project(SphericalPoint(-30, 0)), Point(-1, 0))

    def test_latitude(self):
        self.assertEqual(self.p.project(SphericalPoint(0, 30)), Point(0, 1))
        self.assertEqual(self.p.project(SphericalPoint(0, -30)), Point(0, -1))


class TestEquidistantConicProjection(unittest.TestCase):
    def setUp(self):
        self.p = EquidistantConicProjection(center=(0, 45), standard_parallel1=30, standard_parallel2=60, reference_scale=10)

    def test_projection(self):
        c = self.p(self.p.parallel_circle_center)
        self.assertEqual(self.p.cone_angle, 45)
        f = math.sin(math.radians(self.p.cone_angle))
        print f
        self.assertEqual(self.p(SphericalPoint(0, 45)), Point(0, 0))
        self.assertEqual(self.p(SphericalPoint(0, 50)), Point(0, 0.5))
        self.assertEqual(self.p(SphericalPoint(0, 35)), Point(0, -1))
        #a = 0.98861593*f*15
        a = f*15
        print a
        print c
        p = c + (Point(0, 0) - c).rotate(a)

        #self.assertEqual(self.p(SphericalPoint(15, 45)), p)

    def test_inverse_projection(self):
        self.assertEqual(self.p(Point(0, 0), inverse=True), SphericalPoint(0, 45))
        self.assertEqual(self.p(self.p(SphericalPoint(15, 45)), inverse=True), SphericalPoint(15, 45))
        self.assertEqual(self.p(self.p(SphericalPoint(-15, 45)), inverse=True), SphericalPoint(-15, 45))
        self.assertEqual(self.p(self.p(SphericalPoint(29, 32)), inverse=True), SphericalPoint(29, 32))

        self.p.celestial = True
        self.assertEqual(self.p(Point(0, 0), inverse=True), SphericalPoint(0, 45))
        self.assertEqual(self.p(self.p(SphericalPoint(15, 45)), inverse=True), SphericalPoint(15, 45))
        self.assertEqual(self.p(self.p(SphericalPoint(-15, 45)), inverse=True), SphericalPoint(-15, 45))
        self.assertEqual(self.p(self.p(SphericalPoint(29, 32)), inverse=True), SphericalPoint(29, 32))