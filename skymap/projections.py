import math
import numpy
from operator import xor
from skymap.geometry import Point, SphericalPoint, Line, Circle, Arc, ensure_angle_range

# LONGITUDE: EAST-WEST, LINE OF CONSTANT LONGITUDE IS MERIDIAN
# LATITUDE: NORTH-SOUTH, LINE OF CONSTANT LATITUDE IS PARALLEL


class ProjectionError(Exception):
    pass


class UnitProjection(object):
    def __init__(self):
        pass

    def __call__(self, point, inverse=False):
        if inverse:
            return self.inverse_project(point)
        return self.project(point)

    def project(self, spherical_point):
        return Point(spherical_point)

    def inverse_project(self, point):
        return SphericalPoint(point)


class AzimuthalEquidistantProjection(object):
    def __init__(self, north=True, reference_longitude=0, reference_scale=45, celestial=False):
        """
        :param north: whether to plot the north pole
        :param reference_longitude: the longitude that points to the right
        :param reference_scale: degrees of latitude per unit distance
        :param celestial: longitude increases clockwise around north pole
        """

        self.origin = SphericalPoint(0, 0)
        self._north = north
        self.reference_longitude = reference_longitude
        self.reference_scale = reference_scale
        self._celestial = celestial

        if self._north:
            if self.reference_scale >= 90:
                raise ProjectionError("Invalid reference scale {} for north pole".format(self.reference_scale))
            self.origin_latitude = 90
        else:
            self.reference_scale = -self.reference_scale
            if self.reference_scale <= -90:
                raise ProjectionError("Invalid reference scale {} for south pole".format(self.reference_scale))
            self.origin_latitude = -90

        self.reverse_polar_direction = not xor(self._north, self._celestial)

    def __call__(self, point, inverse=False):
        if inverse:
            return self.inverse_project(point)
        return self.project(point)

    @property
    def celestial(self):
        return self._celestial

    @celestial.setter
    def celestial(self, celestial):
        self._celestial = celestial
        self.reverse_polar_direction = not xor(self._north, self._celestial)

    @property
    def north(self):
        return self._north

    @north.setter
    def north(self, north):
        self.north = north
        self.reverse_polar_direction = not xor(self._north, self._celestial)

    def project(self, spherical_point):
        rho = (self.origin_latitude - spherical_point.latitude) / float(self.reference_scale)
        if self.reverse_polar_direction:
            theta = -self.reduce_longitude(spherical_point.longitude) + 90 + self.reference_longitude
        else:
            theta = self.reduce_longitude(spherical_point.longitude) + 90 - self.reference_longitude
        return Point(rho * math.sin(math.radians(theta)), -rho * math.cos(math.radians(theta)))

    def inverse_project(self, point):
        rho = self.origin.distance(point)
        theta = ensure_angle_range(math.degrees(math.atan2(point.y, point.x)))

        if self.reverse_polar_direction:
            longitude = ensure_angle_range(-theta + self.reference_longitude)
        else:
            longitude = ensure_angle_range(theta + self.reference_longitude)

        return SphericalPoint(longitude, -rho * self.reference_scale + self.origin_latitude)

    def reduce_longitude(self, longitude):
        return ensure_angle_range(longitude, self.reference_longitude)


class EquidistantCylindricalProjection(object):
    def __init__(self, center_longitude, standard_parallel, reference_scale, lateral_scale=1.0, celestial=False):
        self.center_longitude = center_longitude
        self.standard_parallel = standard_parallel
        self.reference_scale = float(reference_scale)
        self.celestial = celestial
        self.lateral_scale = lateral_scale

    def __call__(self, point, inverse=False):
        if inverse:
            return self.inverse_project(point)
        return self.project(point)

    def project(self, spherical_point):
        if self.celestial:
            x = - self.lateral_scale * (self.reduce_longitude(spherical_point.longitude) - self.center_longitude) / self.reference_scale
        else:
            x = self.lateral_scale * (self.reduce_longitude(spherical_point.longitude) - self.center_longitude) / self.reference_scale
        y = spherical_point.latitude / self.reference_scale
        return Point(x, y)

    def inverse_project(self, point):
        if self.celestial:
            longitude = - self.center_longitude - self.reference_scale * point.x / self.lateral_scale
        else:
            longitude = self.center_longitude + self.reference_scale * point.x / self.lateral_scale
        latitude = point.y * self.reference_scale
        return SphericalPoint(longitude, latitude)

    def reduce_longitude(self, longitude):
        return ensure_angle_range(longitude, self.center_longitude)


class EquidistantConicProjection(object):
    def __init__(self, center, standard_parallel1, standard_parallel2, reference_scale=50, celestial=False):
        self.celestial = celestial

        self.reference_longitude = center[0]
        self.reference_latitude = center[1]
        self.standard_parallel1 = standard_parallel1
        self.standard_parallel2 = standard_parallel2
        self.reference_scale = abs(math.radians(reference_scale))
        self.cone_angle = 90 - 0.5*abs(self.standard_parallel1 + self.standard_parallel2)

        # Calculate projection parameters
        phi_1 = math.radians(self.standard_parallel1)
        phi_2 = math.radians(self.standard_parallel2)
        self.n = (math.cos(phi_1) - math.cos(phi_2)) / (phi_2 - phi_1)
        self.G = math.cos(phi_1) / self.n + phi_1
        self.rho_0 = (self.G - math.radians(self.reference_latitude))/self.reference_scale
        self.parallel_circle_center = SphericalPoint(0, math.degrees(self.G))

    def __call__(self, point, inverse=False):
        if inverse:
            return self.inverse_project(point)
        return self.project(point)

    def project(self, spherical_point):
        rho = (self.G - math.radians(spherical_point.latitude))/self.reference_scale
        theta = math.radians(self.n * (self.reduce_longitude(spherical_point.longitude) - self.reference_longitude))

        if self.celestial:
            x = -rho * math.sin(theta)
        else:
            x = rho * math.sin(theta)
        y = self.rho_0 - rho * math.cos(theta)

        return Point(x, y)

    def inverse_project(self, point):
        rho = self.reference_scale * numpy.sign(self.n) * math.sqrt(point.x**2 + (self.rho_0 - point.y)**2)
        theta = math.degrees(math.atan2(point.x, self.rho_0 - point.y))

        if self.celestial:
            longitude = self.reference_longitude - theta / self.n
        else:
            longitude = self.reference_longitude + theta / self.n
        latitude = math.degrees(self.G - rho)

        return SphericalPoint(longitude, latitude)

    def reduce_longitude(self, longitude):
        return ensure_angle_range(longitude, self.reference_longitude)


def calculate_reference_parallels(angle, delta_latitude, central_longitude):
    full_angle = 360.0*angle/float(delta_latitude)
    print full_angle
    fraction_angle = full_angle/360.0
    print fraction_angle
    cone_angle = math.degrees(math.asin(fraction_angle))
    print cone_angle



def circle(x, r=1.0):
    return math.sqrt(r**2 - x**2)


def crossing(val, r=1.0):
    return math.sqrt(r**2 - val**2)


def error(val, xrange):
    n = 1000
    sqsum = 0
    for i in range(n):
        x = -0.5*xrange + i * xrange/(n-1)
        y = circle(x)
        sqsum += (y-val)**2

    c = crossing(val)

    print val, c, math.sqrt(sqsum), math.degrees(math.asin(c)), math.degrees(math.asin(0.5*xrange))

# for i in range(100):
#     val = 0.999 + i/100000.0
#    error(val, 0.1)