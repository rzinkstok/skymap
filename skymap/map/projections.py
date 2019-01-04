import math
import numpy
from skymap.geometry import Point, SkyCoordDeg, Line, Circle, Arc, ensure_angle_range


class ProjectionError(Exception):
    pass


class Projection(object):
    """Abstract class for projections.

    Projections should provide a project method, converting a sky coordinate to a map coordinate,
    and a backproject method for the reverse transformation."""

    def __init__(self, center_longitude, reference_scale=10, celestial=True):
        """Initialize the projection.

        Args:
            center_longitude: the central longitude for the map, in degrees
            reference_scale: degrees of latitude per unit distance on the map
            celestial: whether to use a celestial map orientation (longitude increasing to the left)
        """
        self.center_longitude = float(center_longitude)
        self.reference_scale = float(reference_scale)
        self.celestial = celestial

    def project(self, skycoord):
        """Project the given sky coordinates on the map."""
        pass

    def backproject(self, point):
        """Convert the given location on the map to a sky coordinate."""
        pass

    def reduce_longitude(self, longitude):
        """Return the longitude is within +/- 180 degrees from the center longitude."""
        return ensure_angle_range(longitude, self.center_longitude)


class UnitProjection(Projection):
    """Simple linear projection.
    """

    def project(self, skycoord):
        longitude = self.reduce_longitude(skycoord.ra.degree)
        latitude = skycoord.dec.degree
        return Point(
            (longitude - self.center_longitude) / self.reference_scale,
            latitude / self.reference_scale,
        )

    def inverse_project(self, point):
        longitude = self.center_longitude + self.reference_scale * point.x
        latitude = self.reference_scale * point.y
        return SkyCoordDeg(longitude, latitude)


class AzimuthalEquidistantProjection(Projection):
    def __init__(
        self, reference_longitude=0, reference_scale=45, celestial=False, north=True
    ):
        """Azimuthal equidistant map projection.

        Args:
            reference_longitude: the longitude that points to the right
            reference_scale: degrees of latitude per unit distance
            celestial: longitude increases clockwise around north pole
            north: whether to plot the north pole (true) or the south pole (false)
        """
        Projection.__init__(self, reference_longitude, reference_scale, celestial)
        self.north = north
        self.origin = Point(0, 0)

        if self.north:
            if self.reference_scale >= 90:
                raise ProjectionError(
                    "Invalid reference scale {} for north pole".format(
                        self.reference_scale
                    )
                )
            self.origin_latitude = 90
        else:
            self.reference_scale *= -1
            if self.reference_scale <= -90:
                raise ProjectionError(
                    "Invalid reference scale {} for south pole".format(
                        self.reference_scale
                    )
                )
            self.origin_latitude = -90

    @property
    def reference_longitude(self):
        """Alias for the center longitude."""
        return self.center_longitude

    @reference_longitude.setter
    def reference_longitude(self, value):
        """Alias for the center longitude."""
        self.center_longitude = value

    @property
    def reverse_polar_direction(self):
        """Whether increasing longitude is clockwise or anticlockwise."""
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
    def __init__(
        self, center_longitude, reference_scale, lateral_scale=1.0, celestial=False
    ):
        """Equidistant cylindrical map projection.

        Args:
            center_longitude: the central longitude for the map, in degrees
            reference_scale: degrees of latitude per unit distance on the map
            lateral_scale: degrees of longitude per unit distance on the map
            celestial: whether to use a celestial map orientation (longitude increasing to the left)
        """
        Projection.__init__(self, center_longitude, reference_scale, celestial)
        self.lateral_scale = lateral_scale

    def project(self, skycoord):
        longitude = self.reduce_longitude(skycoord.ra.degree)
        latitude = skycoord.dec.degree

        x = (
            self.lateral_scale
            * (longitude - self.center_longitude)
            / self.reference_scale
        )
        if self.celestial:
            x *= -1
        y = latitude / self.reference_scale
        return Point(x, y)

    def backproject(self, point):
        longitude = (
            self.center_longitude + self.reference_scale * point.x / self.lateral_scale
        )

        if self.celestial:
            longitude *= -1
        latitude = point.y * self.reference_scale

        return SkyCoordDeg(longitude, latitude)


class EquidistantConicProjection(Projection):
    def __init__(
        self,
        center,
        standard_parallel1,
        standard_parallel2,
        reference_scale=50,
        celestial=False,
    ):
        """Equidistant conic map projection.

        Args:
            center: the central longitude for the map, in degrees
            standard_parallel1: the first standard parallel
            standard_parallel2: the second standard parallel
            reference_scale: degrees of latitude per unit distance on the map
            celestial: whether to use a celestial map orientation (longitude increasing to the left)
        """
        Projection.__init__(self, center.ra.degree, reference_scale, celestial)

        self.center_latitude = center.dec.degree
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
        # self.parallel_circle_center = SphericalPoint(0, math.degrees(self.G))

    @property
    def center(self):
        """The center of the projection."""
        return SkyCoordDeg(self.center_longitude, self.center_latitude)

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
        theta = math.degrees(math.atan2(point.x, self.rho_0 - point.y))

        if self.celestial:
            theta *= -1

        longitude = self.center_longitude + theta / self.n
        latitude = math.degrees(self.G - rho)

        return SkyCoordDeg(longitude, latitude)
