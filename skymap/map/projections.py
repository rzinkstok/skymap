import math
import numpy
from skymap.geometry import Point, SkyCoordDeg, Line, Circle, Arc, ensure_angle_range


class ProjectionError(Exception):
    pass


class Projection(object):
    """Abstract class for projections.

    Projections should provide a project method, converting a sky coordinate to a map coordinate,
    and a backproject method for the reverse transformation.

    The projection equations are taken from:
    Map Projections - A Working Manual, John P Snyder (U.S. Geological Survey Professional Paper 1395 (1987).
    """

    def __init__(
        self,
        center_longitude,
        center_latitude,
        standard_parallel1=None,
        standard_parallel2=None,
        reference_scale=10,
        horizontal_stretch=1.0,
        celestial=True,
    ):
        """Initialize the projection.

        Args:
            center_longitude: the central longitude for the map, in degrees
            reference_scale: degrees of latitude per unit distance on the map
            celestial: whether to use a celestial map orientation (longitude increasing to the left)
        """
        self.center_longitude = float(center_longitude)
        self.center_latitude = float(center_latitude)
        self.reference_scale = float(reference_scale)
        self.horizontal_stretch = horizontal_stretch
        self.celestial = celestial

    def project(self, skycoord):
        """Project the given sky coordinates on the map."""
        raise NotImplementedError

    def backproject(self, point):
        """Convert the given location on the map to a sky coordinate."""
        raise NotImplementedError

    def reduce_longitude(self, longitude):
        """Return the longitude within +/- 180 degrees from the center longitude."""
        return ensure_angle_range(longitude, self.center_longitude)

    def meridian(self, longitude, min_latitude, max_latitude):
        p1 = self.project(SkyCoordDeg(longitude, min_latitude))
        p2 = self.project(SkyCoordDeg(longitude, max_latitude))
        return Line(p1, p2)

    def parallel(self, latitude, min_longitude, max_longitude):
        p1 = self.project(SkyCoordDeg(min_longitude - 0.1, latitude))
        p2 = self.project(SkyCoordDeg(max_longitude + 0.1, latitude))
        return Line(p1, p2)


class UnitProjection(Projection):
    """Simple linear projection.
    """

    def project(self, skycoord):
        longitude = self.reduce_longitude(skycoord.ra.degree)
        latitude = skycoord.dec.degree
        return Point(
            self.horizontal_stretch
            * (longitude - self.center_longitude)
            / self.reference_scale,
            latitude / self.reference_scale,
        )

    def inverse_project(self, point):
        longitude = (
            self.center_longitude
            + self.reference_scale * point.x / self.horizontal_stretch
        )
        latitude = self.reference_scale * point.y
        return SkyCoordDeg(longitude, latitude)


class AzimuthalEquidistantProjection(Projection):
    def __init__(
        self,
        center_longitude=0,
        center_latitude=90,
        standard_parallel1=None,
        standard_parallel2=None,
        reference_scale=45,
        horizontal_stretch=1.0,
        celestial=False,
    ):
        """Azimuthal equidistant map projection.

        Center of projection is the pole, which gets projected to the point (0, 0).

        Args:
            center_longitude: the longitude that points to the right
            center_latitude: the
            reference_scale: degrees of latitude per unit distance
            celestial: longitude increases clockwise around north pole
            north: whether to plot the north pole (true) or the south pole (false)
        """
        Projection.__init__(
            self,
            center_longitude,
            center_latitude,
            standard_parallel1,
            standard_parallel2,
            reference_scale,
            horizontal_stretch,
            celestial,
        )
        self.north = center_latitude > 0
        self.origin = Point(0, 0)

        if self.north:
            if self.reference_scale >= 90:
                raise ProjectionError(
                    f"Invalid reference scale {self.reference_scale} for north pole"
                )
        else:
            self.reference_scale *= -1
            if self.reference_scale <= -90:
                raise ProjectionError(
                    f"Invalid reference scale {self.reference_scale} for south pole"
                )

    @property
    def reverse_polar_direction(self):
        """Whether increasing longitude is clockwise or anticlockwise."""
        return self.north == self.celestial

    def project(self, skycoord):
        longitude = self.reduce_longitude(skycoord.ra.degree)
        latitude = skycoord.dec.degree

        rho = (self.center_latitude - latitude) / self.reference_scale
        theta = math.radians(longitude - self.center_longitude)
        if self.reverse_polar_direction:
            theta *= -1

        return Point(
            self.horizontal_stretch * rho * math.cos(theta), rho * math.sin(theta)
        )

    def backproject(self, point):
        rho = self.origin.distance(point)
        theta = ensure_angle_range(math.degrees(math.atan2(point.y, point.x)))

        if self.reverse_polar_direction:
            theta *= -1

        longitude = ensure_angle_range(theta + self.center_longitude)
        latitude = (
            -rho * self.reference_scale / self.horizontal_stretch + self.center_latitude
        )
        return SkyCoordDeg(longitude, latitude)

    def parallel(self, latitude, min_longitude, max_longitude):
        p = self.project(SkyCoordDeg(0, latitude))
        return Circle(self.origin, self.origin.distance(p))


class EquidistantCylindricalProjection(Projection):
    def __init__(
        self,
        center_longitude,
        center_latitude=0,
        standard_parallel1=None,
        standard_parallel2=None,
        reference_scale=50,
        horizontal_stretch=1.0,
        celestial=False,
    ):
        """Equidistant cylindrical map projection.

        Center of projection is the center longitude at zero latitude, which is projected to the point (0, 0).

        Args:
            center_longitude: the central longitude for the map, in degrees
            reference_scale: degrees of latitude per unit distance on the map
            horizontal_stretch: the horizontal stretch factor
            celestial: whether to use a celestial map orientation (longitude increasing to the left)
        """
        Projection.__init__(
            self,
            center_longitude,
            center_latitude,
            standard_parallel1,
            standard_parallel2,
            reference_scale,
            horizontal_stretch,
            celestial,
        )

    def project(self, skycoord):
        longitude = self.reduce_longitude(skycoord.ra.degree)
        latitude = skycoord.dec.degree

        x = (
            self.horizontal_stretch
            * (longitude - self.center_longitude)
            / self.reference_scale
        )
        if self.celestial:
            x *= -1
        y = latitude / self.reference_scale
        return Point(x, y)

    def backproject(self, point):
        if self.celestial:
            x = -point.x
        else:
            x = point.x

        longitude = (
            self.center_longitude + self.reference_scale * x / self.horizontal_stretch
        )

        latitude = point.y * self.reference_scale

        return SkyCoordDeg(longitude, latitude)


class EquidistantConicProjection(Projection):
    def __init__(
        self,
        center_longitude,
        center_latitude,
        standard_parallel1,
        standard_parallel2,
        reference_scale=50,
        celestial=False,
    ):
        """Equidistant conic map projection.

        Center of projection is center longitude at ? latitude, which is projected to the point (0, 0).

        Args:
            center: the central longitude and latitude for the map, in degrees
            standard_parallel1: the first standard parallel
            standard_parallel2: the second standard parallel
            reference_scale: degrees of latitude per unit distance on the map
            celestial: whether to use a celestial map orientation (longitude increasing to the left)
        """
        Projection.__init__(
            self,
            center_longitude,
            center_latitude,
            standard_parallel1,
            standard_parallel2,
            reference_scale,
            celestial,
        )

        self.standard_parallel1 = standard_parallel1
        self.standard_parallel2 = standard_parallel2

        # Calculate projection parameters
        self.cone_angle = 90 - 0.5 * abs(
            self.standard_parallel1 + self.standard_parallel2
        )
        phi_1 = math.radians(self.standard_parallel1)
        phi_2 = math.radians(self.standard_parallel2)
        self.n = (math.cos(phi_1) - math.cos(phi_2)) / (phi_2 - phi_1)
        self.G = math.cos(phi_1) / self.n + phi_1
        self.rho_0 = (self.G - math.radians(self.center_latitude)) / math.radians(
            self.reference_scale
        )

        self._calculate_parallel_circle_center()

    def _calculate_parallel_circle_center(self):
        """Calculates the center of the parallel circles."""
        s0 = SkyCoordDeg(self.center_longitude, 0)
        s1 = SkyCoordDeg(self.center_longitude, math.fabs(math.degrees(self.G)) - 90)
        s3 = SkyCoordDeg(self.center_longitude, numpy.sign(self.center_latitude) * 90)

        p0 = self.project(s0)
        p1 = self.project(s1)
        p3 = self.project(s3)

        delta = numpy.sign(self.center_latitude) * (p1.y - p0.y)

        self.parallel_circle_center = Point(0, p3.y + delta)

    # @property
    # def center(self):
    #     """The center of the projection."""
    #     return SkyCoordDeg(self.center_longitude, self.center_latitude)

    def project(self, skycoord):
        longitude = self.reduce_longitude(skycoord.ra.degree)
        latitude = skycoord.dec.degree

        rho = (self.G - math.radians(latitude)) / math.radians(self.reference_scale)
        theta = math.radians(self.n * (longitude - self.center_longitude))

        if self.celestial:
            theta *= -1

        x = rho * math.sin(theta)
        y = self.rho_0 - rho * math.cos(theta)

        return Point(x, y)

    def backproject(self, point):
        sign_n = numpy.sign(self.n)
        rho = (
            math.radians(self.reference_scale)
            * sign_n
            * math.sqrt(point.x ** 2 + (self.rho_0 - point.y) ** 2)
        )

        theta = math.degrees(
            math.atan2(sign_n * point.x, sign_n * (self.rho_0 - point.y))
        )

        if self.celestial:
            theta *= -1

        longitude = self.center_longitude + theta / self.n
        latitude = math.degrees(self.G - rho)

        return SkyCoordDeg(longitude, latitude)

    def parallel(self, latitude, min_longitude, max_longitude):
        p = self.project(SkyCoordDeg(self.center_longitude, latitude))
        radius = p.distance(self.parallel_circle_center)
        return Circle(self.parallel_circle_center, radius)
