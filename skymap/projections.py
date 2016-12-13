import math
from operator import xor
from skymap.geometry import Point, SphericalPoint, Line, Circle, Arc, ensure_angle_range

# LONGITUDE: EAST-WEST, LINE OF CONSTANT LONGITUDE IS MERIDIAN
# LATITUDE: NORTH-SOUTH, LINE OF CONSTANT LATITUDE IS PARALLEL


class ProjectionError(Exception):
    pass


class UnitProjection(object):
    def __init__(self):
        pass

    def project(self, spherical_point):
        return Point(spherical_point)


class AzimuthalEquidistantProjection(object):
    def __init__(self, north=True, reference_longitude=0, reference_scale=45, celestial=False):
        """
        :param north: whether to plot the north pole
        :param reference_longitude: the longitude that points to the right
        :param reference_range: the latitude that is projected at distance 1 from the origin
        :param celestial: longitude increases clockwise around north pole
        """

        self.origin = SphericalPoint(0, 0)
        self._north = north
        self.reference_longitude = reference_longitude
        self.reference_scale = abs(reference_scale)
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
        while longitude >= 360:
            longitude -= 360
        while longitude < 0:
            longitude += 360
        return longitude


class EquidistantCylindricalProjection(object):
    def __init__(self, center_longitude, standard_parallel, reference_scale, celestial=False):
        self.center_longitude = center_longitude
        self.standard_parallel = standard_parallel
        self.reference_scale = float(reference_scale)
        self.celestial = celestial

    def project(self, spherical_point):
        if self.celestial:
            x = - (self.reduce_longitude(spherical_point.longitude) - self.center_longitude) / self.reference_scale
        else:
            x = (self.reduce_longitude(spherical_point.longitude) - self.center_longitude) / self.reference_scale
        y = spherical_point.latitude / self.reference_scale
        return Point(x, y)

    def inverse_project(self, point):
        pass

    def reduce_longitude(self, longitude):
        while longitude >= self.center_longitude + 180:
            longitude -= 360
        while longitude < self.center_longitude - 180:
            longitude += 360
        return longitude


class EquidistantConicProjection(object):
    def __init__(self, center, standard_parallel1, standard_parallel2, reference_scale=50, celestial=False):
        self.celestial = celestial

        self.reference_longitude = center[0]
        self.reference_latitude = center[1]
        self.standard_parallel1 = standard_parallel1
        self.standard_parallel2 = standard_parallel2
        self.reference_scale = abs(math.radians(reference_scale))

        # Calculate projection parameters
        phi_1 = math.radians(self.standard_parallel1)
        phi_2 = math.radians(self.standard_parallel2)
        self.n = (math.cos(phi_1) - math.cos(phi_2)) / (phi_2 - phi_1)
        self.G = math.cos(phi_1) / self.n + phi_1
        self.rho_0 = (self.G - math.radians(self.reference_latitude))/self.reference_scale
        self.parallel_circle_center = SphericalPoint(0, math.degrees(self.G))

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
        pass

    def reduce_longitude(self, longitude):
        while longitude >= self.reference_longitude + 180:
            longitude -= 360
        while longitude < self.reference_longitude - 180:
            longitude += 360
        return longitude
