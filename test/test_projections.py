import unittest
from skymap.projections import AzimuthalEquidistantProjection, EquidistantCylindricalProjection, EquidistantConicProjection
from skymap.geometry import Point, SkyCoordDeg


class TestAzimuthalEquidistantProjection(unittest.TestCase):
    def setUp(self):
        self.origin = Point(0, 0)
        self.p = AzimuthalEquidistantProjection(reference_longitude=0, reference_scale=40)

    def test_pole(self):
        self.assertEqual(self.p.project(SkyCoordDeg(0, 90)), self.origin)

    def test_latitude(self):
        self.assertEqual(self.p.project(SkyCoordDeg(0, 50)), Point(0, -1))
        self.assertEqual(self.p.project(SkyCoordDeg(90, 50)), Point(1, 0))
        self.assertEqual(self.p.project(SkyCoordDeg(180, 50)), Point(0, 1))
        self.assertEqual(self.p.project(SkyCoordDeg(270, 50)), Point(-1, 0))
        self.p.celestial = True
        self.assertEqual(self.p.project(SkyCoordDeg(0, 50)), Point(0, -1))
        self.assertEqual(self.p.project(SkyCoordDeg(90, 50)), Point(-1, 0))
        self.assertEqual(self.p.project(SkyCoordDeg(180, 50)), Point(0, 1))
        self.assertEqual(self.p.project(SkyCoordDeg(270, 50)), Point(1, 0))

    def test_inverse_project(self):
        self.assertEqual(self.p.backproject(Point(1, 0)), SkyCoordDeg(90, 50))
        self.assertEqual(self.p.backproject(Point(0, 1)), SkyCoordDeg(180, 50))
        self.assertEqual(self.p.backproject(Point(-1, 0)), SkyCoordDeg(270, 50))
        self.assertEqual(self.p.backproject(Point(0, -1)), SkyCoordDeg(0, 50))

        p = SkyCoordDeg(225, 76)
        pp = self.p.project(p)
        ppp = self.p.backproject(pp)
        self.assertEqual(p, ppp)

        self.p.celestial = True
        self.assertEqual(self.p.backproject(Point(1, 0)), SkyCoordDeg(270, 50))
        self.assertEqual(self.p.backproject(Point(0, 1)), SkyCoordDeg(180, 50))
        self.assertEqual(self.p.backproject(Point(-1, 0)), SkyCoordDeg(90, 50))
        self.assertEqual(self.p.backproject(Point(0, -1)), SkyCoordDeg(0, 50))

        p = SkyCoordDeg(225, 76)
        pp = self.p.project(p)
        ppp = self.p.backproject(pp)
        self.assertEqual(p, ppp)

    def test_reference_longitude(self):
        self.p.reference_longitude = 40

        self.assertEqual(self.origin.distance(self.p.project(SkyCoordDeg(0, 50))), 1.0)
        self.assertEqual(self.p.project(SkyCoordDeg(40, 50)), Point(0, -1))
        self.assertEqual(self.p.project(SkyCoordDeg(130, 50)), Point(1, 0))
        self.assertEqual(self.p.project(SkyCoordDeg(220, 50)), Point(0, 1))
        self.assertEqual(self.p.project(SkyCoordDeg(310, 50)), Point(-1, 0))

        p = SkyCoordDeg(225, 76)
        pp = self.p.project(p)
        ppp = self.p.backproject(pp)
        self.assertEqual(p, ppp)

        self.p.celestial = True
        self.assertEqual(self.p.project(SkyCoordDeg(40, 50)), Point(0, -1))
        self.assertEqual(self.p.project(SkyCoordDeg(130, 50)), Point(-1, 0))
        self.assertEqual(self.p.project(SkyCoordDeg(220, 50)), Point(0, 1))
        self.assertEqual(self.p.project(SkyCoordDeg(310, 50)), Point(1, 0))

        p = SkyCoordDeg(225, 76)
        pp = self.p.project(p)
        ppp = self.p.backproject(pp)
        self.assertEqual(p, ppp)

        self.p.celestial = False
        self.p.reference_longitude = -40
        self.assertEqual(self.p.project(SkyCoordDeg(-40, 50)), Point(0, -1))
        self.assertEqual(self.p.project(SkyCoordDeg(50, 50)), Point(1, 0))
        self.assertEqual(self.p.project(SkyCoordDeg(140, 50)), Point(0, 1))
        self.assertEqual(self.p.project(SkyCoordDeg(230, 50)), Point(-1, 0))

    def test_south_pole(self):
        self.p = AzimuthalEquidistantProjection(reference_longitude=0, reference_scale=40, north=False)

        # Pole
        self.assertEqual(self.p.project(SkyCoordDeg(0, -90)), self.origin)

        # Project
        self.assertEqual(self.p.project(SkyCoordDeg(0, -50)), Point(0, -1))
        self.assertEqual(self.p.project(SkyCoordDeg(90, -50)), Point(-1, 0))
        self.assertEqual(self.p.project(SkyCoordDeg(180, -50)), Point(0, 1))
        self.assertEqual(self.p.project(SkyCoordDeg(270, -50)), Point(1, 0))
        self.p.celestial = True
        self.assertEqual(self.p.project(SkyCoordDeg(0, -50)), Point(0, -1))
        self.assertEqual(self.p.project(SkyCoordDeg(90, -50)), Point(1, 0))
        self.assertEqual(self.p.project(SkyCoordDeg(180, -50)), Point(0, 1))
        self.assertEqual(self.p.project(SkyCoordDeg(270, -50)), Point(-1, 0))

        # Inverse project
        self.p.celestial = False
        self.assertEqual(self.p.backproject(Point(1, 0)), SkyCoordDeg(270, -50))
        self.assertEqual(self.p.backproject(Point(0, -1)), SkyCoordDeg(0, -50))
        self.assertEqual(self.p.backproject(Point(-1, 0)), SkyCoordDeg(90, -50))
        self.assertEqual(self.p.backproject(Point(0, 1)), SkyCoordDeg(180, -50))
        p = SkyCoordDeg(225, -76)
        pp = self.p.project(p)
        ppp = self.p.backproject(pp)
        self.assertEqual(p, ppp)

        self.p.celestial = True
        self.assertEqual(self.p.backproject(Point(1, 0)), SkyCoordDeg(90, -50))
        self.assertEqual(self.p.backproject(Point(0, 1)), SkyCoordDeg(180, -50))
        self.assertEqual(self.p.backproject(Point(-1, 0)), SkyCoordDeg(270, -50))
        self.assertEqual(self.p.backproject(Point(0, -1)), SkyCoordDeg(0, -50))
        p = SkyCoordDeg(225, -76)
        pp = self.p.project(p)
        ppp = self.p.backproject(pp)
        self.assertEqual(p, ppp)

    def test_other_scale(self):
        self.p = AzimuthalEquidistantProjection(reference_longitude=0, reference_scale=80.0/190.0)
        self.assertEqual(self.p.project(SkyCoordDeg(0, 50)), Point(0, -95))


class TestEquidistantCylindricalProjection(unittest.TestCase):
    def setUp(self):
        self.p = EquidistantCylindricalProjection(center_longitude=0, reference_scale=30)

    def test_longitude(self):
        self.assertEqual(self.p.project(SkyCoordDeg(0, 0)), Point(0, 0))
        self.assertEqual(self.p.project(SkyCoordDeg(30, 0)), Point(1, 0))
        self.assertEqual(self.p.project(SkyCoordDeg(-30, 0)), Point(-1, 0))

    def test_latitude(self):
        self.assertEqual(self.p.project(SkyCoordDeg(0, 30)), Point(0, 1))
        self.assertEqual(self.p.project(SkyCoordDeg(0, -30)), Point(0, -1))

    def test_inverse_longitude(self):
        self.assertEqual(self.p.backproject(Point(0, 0)), SkyCoordDeg(0, 0))
        self.assertEqual(self.p.backproject(Point(1, 0)), SkyCoordDeg(30, 0))
        self.assertEqual(self.p.backproject(Point(-1, 0)), SkyCoordDeg(-30, 0))


class TestEquidistantConicProjection(unittest.TestCase):
    def setUp(self):
        self.p = EquidistantConicProjection(center=SkyCoordDeg(0, 45), standard_parallel1=30, standard_parallel2=60, reference_scale=10)

    def test_projection(self):
        self.assertEqual(self.p.cone_angle, 45)
        self.assertEqual(self.p.project(SkyCoordDeg(0, 45)), Point(0, 0))
        self.assertEqual(self.p.project(SkyCoordDeg(0, 50)), Point(0, 0.5))
        self.assertEqual(self.p.project(SkyCoordDeg(0, 35)), Point(0, -1))

    def test_inverse_projection(self):
        self.assertEqual(self.p.backproject(Point(0, 0)), SkyCoordDeg(0, 45))
        self.assertEqual(self.p.backproject(self.p.project(SkyCoordDeg(15, 45))), SkyCoordDeg(15, 45))
        self.assertEqual(self.p.backproject(self.p.project(SkyCoordDeg(-15, 45))), SkyCoordDeg(-15, 45))
        self.assertEqual(self.p.backproject(self.p.project(SkyCoordDeg(29, 32))), SkyCoordDeg(29, 32))

        self.p.celestial = True
        self.assertEqual(self.p.backproject(Point(0, 0)), SkyCoordDeg(0, 45))
        self.assertEqual(self.p.backproject(self.p.project(SkyCoordDeg(15, 45))), SkyCoordDeg(15, 45))
        self.assertEqual(self.p.backproject(self.p.project(SkyCoordDeg(-15, 45))), SkyCoordDeg(-15, 45))
        self.assertEqual(self.p.backproject(self.p.project(SkyCoordDeg(29, 32))), SkyCoordDeg(29, 32))