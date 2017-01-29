import math
import datetime
import numpy

from skymap.geometry import SphericalPoint, HourAngle


REFERENCE_EPOCH = datetime.datetime(2000, 1, 1).date()


# Ecliptic
def obliquity_of_the_ecliptic(epoch):
    # From Astronomical Almanac 2010
    a = 23.0 + 26/60.0 + 21/3600.0
    b = 46.836769/3600.0
    c = 0.0001831/3600.0
    d = 0.00200340/3600.0
    e = 0.576e-6
    f = 4.34e-8
    t = (epoch - REFERENCE_EPOCH).days / 36525.0
    return a + b * t + c * t ** 2 + d * t ** 3 + e * t ** 4 + f * t ** 5


def ecliptic_to_equatorial(p):
    eps = math.radians(obliquity_of_the_ecliptic(REFERENCE_EPOCH))
    ceps = math.cos(eps)
    seps = math.sin(eps)

    l = math.radians(p.longitude)
    b = math.radians(p.latitude)

    longitude = math.degrees(math.atan2(math.sin(l) * ceps - math.tan(b) * seps, math.cos(l)))
    latitude = math.degrees(math.asin(math.sin(b) * ceps + math.cos(b) * seps * math.sin(l)))

    return SphericalPoint(longitude, latitude)


# Galactic coordinate system
def galactic_pole(epoch=REFERENCE_EPOCH):
    ra = HourAngle(12, 49).to_degrees()
    dec = 27.4
    p = PrecessionCalculator(datetime.datetime(1950, 1, 1).date(), epoch)
    return SphericalPoint(p.precess(ra, dec))


def galactic_to_equatorial(p, epoch=REFERENCE_EPOCH):
    l = math.radians(p.longitude)
    b = math.radians(p.latitude)

    pl = math.radians(192.25)
    pb = math.radians(27.4)
    l -= math.radians(33.0)

    longitude = math.degrees(math.atan2(math.cos(b) * math.cos(l), (math.sin(b) * math.cos(pb) - math.cos(b) * math.sin(pb) * math.sin(l))) + pl)
    latitude = math.degrees(math.asin(math.cos(b) * math.cos(pb) * math.sin(l) + math.sin(b) * math.sin(pb)))

    p = PrecessionCalculator(datetime.datetime(1950, 1, 1).date(), epoch)
    return SphericalPoint(p.precess(longitude, latitude))


# Precession
class PrecessionCalculator(object):
    def __init__(self, epoch1, epoch2):
        self.epoch1 = epoch1
        self.epoch2 = epoch2

        t1 = (epoch1 - REFERENCE_EPOCH).days / 36525.0
        m1 = self.inverse_rotation_matrix(t1)
        t2 = (epoch2 - REFERENCE_EPOCH).days / 36525.0
        m2 = self.rotation_matrix(t2)
        self.matrix = numpy.dot(m2, m1)

    def zeta(self, t):
        return 0.0007362625 + 0.6405786742 * t + 0.00008301386111 * t ** 2 + 0.000005005077778 * t ** 3 - 0.000000001658611 * t ** 4 - 8.813888889e-11 * t ** 5

    def z(self, t):
        return -0.0007362625 + 0.6405769947 * t + 0.0003035374444 * t ** 2 + 0.000005074547222 * t ** 3 - 0.000000007943333 * t ** 4 - 8.066666667e-11 * t ** 5

    def theta(self, t):
        return 0.5567199731 * t - 0.0001193037222 * t ** 2 - 0.0000116174 * t ** 3 - 0.000000001969167 * t ** 4 - 3.538888889E-11 * t ** 5

    def direction_sines_and_cosines(self, t):
        zeta = math.radians(self.zeta(t))
        z = math.radians(self.z(t))
        theta = math.radians(self.theta(t))

        cx = math.cos(zeta)
        sx = math.sin(zeta)
        cz = math.cos(z)
        sz = math.sin(z)
        ct = math.cos(theta)
        st = math.sin(theta)

        return cx, sx, cz, sz, ct, st

    def inverse_rotation_matrix(self, t):
        cx, sx, cz, sz, ct, st = self.direction_sines_and_cosines(t)
        m = numpy.array([
            [cx * ct * cz - sx * sz, cx * ct * sz + sx * cz, cx * st],
            [-sx * ct * cz - cx * sz, -sx * ct * sz + cx * cz, -sx * st],
            [-st * cz, -st * sz, ct]
        ])
        return m

    def rotation_matrix(self, t):
        cx, sx, cz, sz, ct, st = self.direction_sines_and_cosines(t)
        m = numpy.array([
            [cx * ct * cz - sx * sz, -sx * ct * cz - cx * sz, -st * cz],
            [cx * ct * sz + sx * cz, -sx * ct * sz + cx * cz, -st * sz],
            [cx * st, -sx * st, ct]
        ])
        return m

    def precess(self, ra, dec):
        ra = math.radians(ra)
        dec = math.radians(dec)
        cd = math.cos(dec)
        v1 = numpy.array([math.cos(ra) * cd, math.sin(ra) * cd, math.sin(dec)])

        v2 = numpy.dot(self.matrix, v1)

        ra2 = math.atan2(v2[1], v2[0])
        if ra2 < 0:
            ra2 += 2 * math.pi
        dec2 = math.asin(v2[2])

        return math.degrees(ra2), math.degrees(dec2)
