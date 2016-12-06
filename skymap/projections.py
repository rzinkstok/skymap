import math
from operator import xor
from skymap.geometry import Point, SphericalPoint, Line, Circle, Arc, ensure_angle_range

# LONGITUDE: EAST-WEST, LINE OF CONSTANT LONGITUDE IS MERIDIAN
# LATITUDE: NORTH-SOUTH, LINE OF CONSTANT LATITUDE IS PARALLEL


class ProjectionError(Exception):
    pass


class AzimuthalEquidistantProjection(object):
    def __init__(self, north=True, reference_longitude=0, reference_scale=None, celestial=False):
        """
        :param pole: the pole to plot (north or south)
        :param reference_longitude: the latitude that points to the right
        :param reference_scale: the longitude that specifies the scale distance
        :param scale: the distance between the origin and the reference latitude
        :param celestial: longitude increases clockwise around north pole
        """

        self.origin = Point(0, 0)
        self._north = north
        self.reference_scale = reference_scale
        self.reference_longitude = reference_longitude
        self._celestial = celestial

        if self._north:
            if self.reference_scale is None:
                self.reference_scale = 45
            if self.reference_scale < 0 or self.reference_scale >= 90:
                raise ProjectionError("Invalid reference latitude {} for north pole".format(self.reference_scale))
            self.origin_latitude = 90
        else:
            if self.reference_scale is None:
                self.reference_scale = -45
            if self.reference_scale > 0 or self.reference_scale <= -90:
                raise ProjectionError("Invalid reference latitude {} for south pole".format(self.reference_scale))
            self.origin_latitude = -90

        self.reference_radius = 1.0 / (self.origin_latitude - self.reference_scale)
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
        rho = (self.origin_latitude - spherical_point.latitude) * self.reference_radius
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

        return SphericalPoint(longitude, -rho / self.reference_radius + self.origin_latitude)

    def project_line(self, line):
        if line.p1.longitude == line.p2.longitude:
            # Part of meridian, return line
            p1 = self.project(line.p1)
            p2 = self.project(line.p2)
            return Line(p1, p2)

        if line.p1.latitude == line.p2.latitude:
            # Part of parallel, return arc
            radius = (self.origin_latitude - line.p1.latitude) * self.reference_radius
            if self.reverse_polar_direction:
                angle1 = -line.p1.longitude + self.reference_longitude
                angle2 = -line.p2.longitude + self.reference_longitude
            else:
                angle1 = line.p1.longitude - self.reference_longitude
                angle2 = line.p2.longitude - self.reference_longitude
            return Arc(self.origin, radius, angle1, angle2)

        # TODO: Interpolate line and project segments

    def reduce_longitude(self, longitude):
        while longitude >= 360:
            longitude -= 360
        while longitude < 0:
            longitude += 360
        return longitude

    def parallel(self, latitude):
        # Circle around origin
        radius = (self.origin_latitude - latitude) * self.reference_radius
        return Circle(self.origin, radius)

    def meridian(self, longitude):
        if longitude%90 == 0.0:
            p1 = self.origin
        elif longitude%45 == 0.0:
            if self.north:
                p1 = self.project(SphericalPoint(longitude, 89))
            else:
                p1 = self.project(SphericalPoint(longitude, -89))
        else:
            if self.north:
                p1 = self.project(SphericalPoint(longitude, 80))
            else:
                p1 = self.project(SphericalPoint(longitude, -80))
        p2 = self.project(SphericalPoint(longitude, 0))

        return Line(p1, p2)


class EquidistantCylindricalProjection(object):
    def __init__(self, reference_longitude, standard_parallel, reference_scale, celestial=False):
        self.reference_longitude = reference_longitude
        self.standard_parallel = standard_parallel
        self.reference_scale = float(reference_scale)
        self.celestial = celestial

    def project(self, spherical_point):
        if self.celestial:
            x = - (self.reduce_longitude(spherical_point.longitude) - self.reference_longitude) / self.reference_scale
        else:
            x = (self.reduce_longitude(spherical_point.longitude) - self.reference_longitude) / self.reference_scale
        y = spherical_point.latitude / self.reference_scale
        return Point(x, y)

    def inverse_project(self, point):
        pass

    def reduce_longitude(self, longitude):
        while longitude >= self.reference_longitude + 180:
            longitude -= 360
        while longitude < self.reference_longitude - 180:
            longitude += 360
        return longitude

    def parallel(self, latitude):
        p1 = self.project(SphericalPoint(self.reference_longitude - self.reference_scale, latitude))
        p2 = self.project(SphericalPoint(self.reference_longitude + self.reference_scale, latitude))
        return Line(p1, p2)

    def meridian(self, longitude):
        p1 = self.project(SphericalPoint(longitude, -90))
        p2 = self.project(SphericalPoint(longitude, +90))
        return Line(p1, p2)


class EquidistantConicProjection(object):
    def __init__(self, reference_longitude, standard_parallel1, standard_parallel2, celestial=False):
        self.celestial = celestial

        self.reference_longitude = reference_longitude
        self.standard_parallel1 = standard_parallel1
        self.standard_parallel2 = standard_parallel2
        self.reference_latitude = 0.5*(self.standard_parallel1 + self.standard_parallel2)

        # Calculate projection parameters
        phi_1 = math.radians(self.standard_parallel1)
        phi_2 = math.radians(self.standard_parallel2)
        self.n = (math.cos(phi_1) - math.cos(phi_2)) / (phi_2 - phi_1)
        self.G = math.cos(phi_1) / self.n + phi_1
        self.rho_0 = self.G - math.radians(self.reference_latitude)

        self.projection_origin = Point(0, self.rho_0)

    def project(self, spherical_point):
        rho = self.G - math.radians(spherical_point.latitude)
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

    def parallel(self, latitude):
        # Circle around origin
        p = self.project(SphericalPoint(0, latitude))
        radius = p.distance(self.projection_origin)
        return Circle(self.projection_origin, radius)

    def meridian(self, longitude):
        # Line from origin
        if self.reference_latitude > 0:
            p = self.project(SphericalPoint(longitude, -30))
        else:
            p = self.project(SphericalPoint(longitude, 30))
        return Line(self.projection_origin, p)