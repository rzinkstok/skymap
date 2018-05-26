import math
import numpy
from skymap.geometry import Point, SkyCoordDeg, Line, Circle, Arc, ensure_angle_range


class ProjectionError(Exception):
    pass


class Projection(object):
    def __init__(self, center_longitude, reference_scale, celestial):
        self.center_longitude = float(center_longitude)
        self.reference_scale = float(reference_scale)
        self.celestial = celestial

    def project(self, skycoord):
        pass

    def backproject(self, point):
        pass

    def reduce_longitude(self, longitude):
        return ensure_angle_range(longitude, self.center_longitude)

    # def __call__(self, point, inverse=False):
    #     if inverse:
    #         return self.backproject(point)
    #     return self.project(point)


class UnitProjection(object):
    def __init__(self):
        pass

    @staticmethod
    def project(skycoord):
        return Point(skycoord.ra.deg, skycoord.dec.deg)

    @staticmethod
    def inverse_project(point):
        return SkyCoordDeg(point.x, point.y)


class AzimuthalEquidistantProjection(Projection):
    def __init__(self, reference_longitude=0, reference_scale=45, celestial=False, north=True):
        """
        :param north: whether to plot the north pole
        :param reference_longitude: the longitude that points to the right
        :param reference_scale: degrees of latitude per unit distance
        :param celestial: longitude increases clockwise around north pole
        """

        Projection.__init__(self, reference_longitude, reference_scale, celestial)
        self.north = north
        self.origin = Point(0, 0)

        if self.north:
            if self.reference_scale >= 90:
                raise ProjectionError("Invalid reference scale {} for north pole".format(self.reference_scale))
            self.origin_latitude = 90
        else:
            self.reference_scale *= -1
            if self.reference_scale <= -90:
                raise ProjectionError("Invalid reference scale {} for south pole".format(self.reference_scale))
            self.origin_latitude = -90

    @property
    def reference_longitude(self):
        return self.center_longitude

    @reference_longitude.setter
    def reference_longitude(self, value):
        self.center_longitude = value

    @property
    def reverse_polar_direction(self):
        return self.north == self.celestial

    def project(self, skycoord):
        longitude = self.reduce_longitude(skycoord.ra.degree)
        latitude = skycoord.dec.degree

        rho = (self.origin_latitude - latitude) / self.reference_scale
        theta = math.radians(longitude - self.reference_longitude)
        if self.reverse_polar_direction:
            theta *= -1

        return Point(rho * math.sin(theta), -rho * math.cos(theta))

    def backproject(self, point):
        rho = self.origin.distance(point)
        theta = ensure_angle_range(math.degrees(math.atan2(point.y, point.x))) + 90

        if self.reverse_polar_direction:
            theta *= -1

        longitude = ensure_angle_range(theta + self.reference_longitude)
        latitude = -rho * self.reference_scale + self.origin_latitude
        return SkyCoordDeg(longitude, latitude)


class EquidistantCylindricalProjection(Projection):
    def __init__(self, center_longitude, reference_scale, lateral_scale=1.0, celestial=False):
        Projection.__init__(self, center_longitude, reference_scale, celestial)
        self.lateral_scale = lateral_scale

    def project(self, skycoord):
        longitude = self.reduce_longitude(skycoord.ra.degree)
        latitude = skycoord.dec.degree

        x = self.lateral_scale * (longitude - self.center_longitude) / self.reference_scale
        if self.celestial:
            x *= -1
        y = latitude / self.reference_scale
        return Point(x, y)

    def backproject(self, point):
        longitude = self.center_longitude + self.reference_scale * point.x / self.lateral_scale

        if self.celestial:
            longitude *= -1
        latitude = point.y * self.reference_scale

        return SkyCoordDeg(longitude, latitude)


class EquidistantConicProjection(Projection):
    def __init__(self, center, standard_parallel1, standard_parallel2, reference_scale=50, celestial=False):
        Projection.__init__(self, center.ra.degree, reference_scale, celestial)

        self.center_latitude = center.dec.degree
        self.standard_parallel1 = standard_parallel1
        self.standard_parallel2 = standard_parallel2

        # Calculate projection parameters
        self.cone_angle = 90 - 0.5 * abs(self.standard_parallel1 + self.standard_parallel2)
        phi_1 = math.radians(self.standard_parallel1)
        phi_2 = math.radians(self.standard_parallel2)
        self.n = (math.cos(phi_1) - math.cos(phi_2)) / (phi_2 - phi_1)
        self.G = math.cos(phi_1) / self.n + phi_1
        self.rho_0 = (self.G - math.radians(self.center_latitude))/math.radians(self.reference_scale)
        # self.parallel_circle_center = SphericalPoint(0, math.degrees(self.G))

    @property
    def center(self):
        return SkyCoordDeg(self.center_longitude, self.center_latitude)

    def project(self, skycoord):
        longitude = self.reduce_longitude(skycoord.ra.degree)
        latitude = skycoord.dec.degree

        rho = (self.G - math.radians(latitude))/math.radians(self.reference_scale)
        theta = math.radians(self.n * (longitude - self.center_longitude))

        if self.celestial:
            theta *= -1

        x = rho * math.sin(theta)
        y = self.rho_0 - rho * math.cos(theta)

        return Point(x, y)

    def backproject(self, point):
        sign_n = numpy.sign(self.n)
        rho = math.radians(self.reference_scale) * sign_n * math.sqrt(point.x**2 + (self.rho_0 - point.y)**2)
        theta = math.degrees(math.atan2(point.x, self.rho_0 - point.y))

        if self.celestial:
            theta *= -1

        longitude = self.center_longitude + theta / self.n
        latitude = math.degrees(self.G - rho)

        return SkyCoordDeg(longitude, latitude)


#
#
# def calculate_reference_parallels(angle, delta_latitude, central_longitude):
#     full_angle = 360.0*angle/float(delta_latitude)
#     print full_angle
#     fraction_angle = full_angle/360.0
#     print fraction_angle
#     cone_angle = math.degrees(math.asin(fraction_angle))
#     print cone_angle
#
#
#
# def circle(x, r=1.0):
#     return math.sqrt(r**2 - x**2)
#
#
# def crossing(val, r=1.0):
#     return math.sqrt(r**2 - val**2)
#
#
# def error(val, xrange):
#     n = 1000
#     sqsum = 0
#     for i in range(n):
#         x = -0.5*xrange + i * xrange/(n-1)
#         y = circle(x)
#         sqsum += (y-val)**2
#
#     c = crossing(val)
#
#     print val, c, math.sqrt(sqsum), math.degrees(math.asin(c)), math.degrees(math.asin(0.5*xrange))

# for i in range(100):
#     val = 0.999 + i/100000.0
#    error(val, 0.1)
