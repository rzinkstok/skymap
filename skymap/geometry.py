import math
import numpy as np
from astropy.coordinates import SkyCoord
from astropy import units

TOLERANCE = 1e-12


class SkyCoordDeg(SkyCoord):
    """Extension of AstroPy SkyCoord, using degrees as units."""

    def __init__(self, *args, **kwargs):
        if "unit" not in kwargs:
            kwargs["unit"] = units.deg
        SkyCoord.__init__(self, *args, **kwargs)

    def __eq__(self, other):
        return (abs(self.dec.degree - other.dec.degree) < TOLERANCE) and (
            abs(self.ra.degree - other.ra.degree) < TOLERANCE
        )

    def __ne__(self, other):
        return not self == other


# For tracking precession of north pole
# SkyCoord(0,90, unit="degree", frame=PrecessedGeocentric(equinox="J2100")).transform_to("icrs")
#
# For mapping the ecliptic (equinox is map equinox)
# SkyCoord(90, 0, unit="degree", frame=BarycentricTrueEcliptic(equinox="J2000")).transform_to("icrs")
#
# For mapping the galactic pole
# SkyCoord(0, 90, unit="degree", frame=Galactic).transform_to("icrs")
#
# For converting constellation boundary to ICRS
# SkyCoord(0, 0, unit="degree", frame=PrecessedGeocentric(equinox="B1875")).transform_to("icrs")


# def distance(p1, p2):
#     """Calculate the distance between the given points."""
#     return np.linalg.norm(p1[:2] - p2[:2])


def rotation_matrix(axis, angle):
    """Returns the 3x3 rotation matrix for the given angle and axis.

    Args:
        axis: the vector around which to rotate
        angle (float): the angle over which to rotate in radians
    """

    sina = math.sin(angle)
    cosa = math.cos(angle)
    direction = axis / np.linalg.norm(axis)

    rmatrix = np.diag([cosa, cosa, cosa])
    rmatrix += np.outer(direction, direction) * (1.0 - cosa)
    direction *= sina
    rmatrix += np.array(
        [
            [0.0, -direction[2], direction[1]],
            [direction[2], 0.0, -direction[0]],
            [-direction[1], direction[0], 0.0],
        ]
    )
    return rmatrix


# def sky2cartesian(points):
#     phi = np.deg2rad(points[:, 0])
#     theta = np.pi / 2 - np.deg2rad(points[:, 1])
#     result = np.zeros((points.shape[0], 3))
#     result[:, 0] = np.sin(theta) * np.cos(phi)
#     result[:, 1] = np.sin(theta) * np.sin(phi)
#     result[:, 2] = np.cos(theta)
#     return result
#
#
# def sky2cartesian_with_parallax(points_with_parallax):
#     """
#
#     Args:
#         points_with_parallax: (ra, dec, parallax) with ra and dec in degrees and parallax in mas
#
#     Returns:
#         x, y, z in parsecs
#     """
#     phi = np.deg2rad(points_with_parallax[:, 0])
#     theta = np.pi / 2 - np.deg2rad(points_with_parallax[:, 1])
#     rho = 1000.0 / points_with_parallax[:, 2]
#     result = np.zeros((points_with_parallax.shape[0], 3))
#     result[:, 0] = rho * np.sin(theta) * np.cos(phi)
#     result[:, 1] = rho * np.sin(theta) * np.sin(phi)
#     result[:, 2] = rho * np.cos(theta)
#     return result
#
#
# def cartesian2sky(points):
#     theta = np.arccos(points[:, 2])
#     phi = np.arctan2(points[:, 1], points[:, 0])
#     result = np.zeros((points.shape[0], 2))
#     result[:, 0] = np.rad2deg(phi)
#     result[:, 1] = np.rad2deg(np.pi / 2 - theta)
#     return result
#
#
# def cartesian2sky_with_parallax(points):
#     """Cartesian coordinates in parsecs to ra, dec, parallax."""
#     r = np.linalg.norm(points, axis=1)
#     theta = np.arccos(points[:, 2] / r)
#     phi = np.arctan2(points[:, 1], points[:, 0])
#     result = np.zeros((points.shape[0], 3))
#     result[:, 0] = np.rad2deg(phi)
#     result[:, 1] = np.rad2deg(np.pi / 2 - theta)
#     result[:, 2] = 1000.0 / r
#     return result


# class Drawable(object):
#     def draw(self, tikz_picture):
#         pass
#


class Point(object):
    """A 2D point on the plane. Supports retrieval of coordinates by attributes (x and y) and by indexing.
    Supports addition, subtraction, scalar multiplication, scalar division, and equality checks.

    Args:
        a: the x coordinate, or a pair of (x, y) coordinates
        b: the optional y coordinate
    """

    def __init__(self, a, b=None):
        if b is None:
            self.x, self.y = a
        else:
            self.x = a
            self.y = b

    def __str__(self):
        return f"Point({self.x}, {self.y})"

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, item):
        return (self.x, self.y)[item]

    def __add__(self, other):
        x = self.x + other.x
        y = self.y + other.y
        return self.__class__(x, y)

    def __sub__(self, other):
        x = self.x - other.x
        y = self.y - other.y
        return self.__class__(x, y)

    def __mul__(self, other):
        return self.__class__(other * self.x, other * self.y)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        other = float(other)
        return self.__class__(self.x / other, self.y / other)

    def __eq__(self, other):
        return self.distance(other) < 1e-6

    def __ne__(self, other):
        return not self.__eq__(other)

    def distance(self, other):
        """Return the distance between the given point and this point.

        Args:
            other (skymap.geometry.Point): the other point
        """
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def rotate(self, angle, origin=None):
        """Return a copy of the point, rotated the given angle around the origin.

        Args:
            angle (float): the angle in degrees
            origin (skymap.geometry.Point): the point around which to rotate
        """
        if origin is None:
            origin = Point(0, 0)
        angle = math.radians(angle)
        dx = self.x - origin.x
        dy = self.y - origin.y
        new_dx = dx * math.cos(angle) - dy * math.sin(angle)
        new_dy = dx * math.sin(angle) + dy * math.cos(angle)
        x = origin.x + new_dx
        y = origin.y + new_dy
        return self.__class__(x, y)

    @property
    def norm(self):
        """Return the distance between the point and the origin."""
        return self.distance(Point(0, 0))

    @property
    def coordinates(self):
        """Returns the TikZ coordinate string for the point."""
        x = self.x
        y = self.y
        if abs(x) < 1e-4:
            x = 0.0
        if abs(y) < 1e-4:
            y = 0.0

        return f"({x}mm,{y}mm)"

    @property
    def angle(self):
        """Return the angle of the line from the origin to the point."""
        return math.degrees(math.atan2(self.y, self.x))


class Line(object):
    """A straight line in 2D between two points.

    Args:
        p1 (skymap.geometry.Point): the first point
        p2 (skymap.geometry.Point): the second point
    """

    def __init__(self, p1, p2):
        if p1 == p2:
            raise ValueError("Line needs two distinct points")
        self.p1 = p1
        self.p2 = p2
        self.vector = p2 - p1
        self.length = self.p1.distance(self.p2)

    def __str__(self):
        return f"Line({self.p1}, {self.p2})"

    def intersect_line(self, other):
        """Return the intersection between the given line and this line. Returns None for parallel lines.

        Args:
            other (skymap.geometry.Line): the other line
        """
        a1 = self.p1.y - self.p2.y
        b1 = self.p2.x - self.p1.x
        c1 = self.p1.x * self.p2.y - self.p2.x * self.p1.y

        a2 = other.p1.y - other.p2.y
        b2 = other.p2.x - other.p1.x
        c2 = other.p1.x * other.p2.y - other.p2.x * other.p1.y

        den = a1 * b2 - a2 * b1
        if abs(den) == 0.0:
            return None

        y = (c1 * a2 - c2 * a1) / den
        x = (b1 * c2 - c1 * b2) / den
        return Point(x, y)

    def inclusive_intersect_line(self, other):
        """Returns the intersection of two lines if the intersection lies between the end points of both lines. Returns
        the intersection as an element of a list. If both lines are parallel, an empty list is returned.

        Args:
            other (skymap.geometry.Line): the other line
        """
        p = self.intersect_line(other)
        if p is None:
            return []
        if self.point_on_line_segment(p) and other.point_on_line_segment(p):
            return [p]
        return []

    def point_on_line_segment(self, point):
        """Check whether the given point lies on the line segment.

        Args:
            point (skymap.geometry.Point): the point to check
        """
        point_vector = point - self.p1
        ip = point_vector.x * self.vector.x + point_vector.y * self.vector.y
        comp = ip / self.length
        if 0 <= comp <= self.length:
            return True
        return False

    def distance_point(self, point):
        """Returns the perpendicular distance between the given point and the line.

        Args:
            point (skymap.geometry.Point): the point to calculate the distance for
        """
        numerator = math.fabs(
            (self.p2.x - self.p1.x) * (self.p1.y - point.y)
            - (self.p1.x - point.x) * (self.p2.y - self.p1.y)
        )
        denominator = math.sqrt(
            (self.p2.x - self.p1.x) ** 2 + (self.p2.y - self.p1.y) ** 2
        )
        return numerator / denominator

    @property
    def angle(self):
        """Returns the angle between the line and the positive x axis."""
        d = self.p2 - self.p1
        return math.degrees(math.atan2(d.y, d.x))

    @property
    def path(self):
        """Returns the TikZ path string for the line."""
        return f"{self.p1.coordinates}--{self.p2.coordinates}"

    @property
    def reverse_path(self):
        """Returns the TikZ path string for the inverse line."""
        return f"{self.p2.coordinates}--{self.p1.coordinates}"

    def reverse(self):
        return Line(self.p2, self.p1)


class Polygon(object):
    """A 2D polygon.

    The points and the connections between the points are stored in the points and lines attributes.

    Args:
        points (list): a list of points defining the polygon
        closed (bool): whether the last point is to be connected to the first
    """

    def __init__(self, points=None, closed=True):
        self.points = []
        self.lines = []
        self.closed = closed
        if points:
            for p in points:
                self.add_point(p)
        if closed:
            self.close()

    def add_point(self, point):
        """Add a point to the polygon's point list.

        Args:
            point (skymap.geometry.Point): the point to add
        """
        self.points.append(point)
        if len(self.points) > 1:
            self.lines.append(Line(self.points[-2], self.points[-1]))

    def close(self):
        """Close the polygon by adding a line connecting the last and the first point."""
        if not self.closed:
            self.closed = True
        self.lines.append(Line(self.points[-1], self.points[0]))

    @property
    def path(self):
        """Returns the TikZ path string for the polygon."""
        if not self.points:
            return ""
        s = f"{self.points[0].coordinates}"
        for p in self.points[1:]:
            s += f"--{p.coordinates}"
        if self.closed:
            s += "--cycle"
        return s


class Circle(object):
    """A circle in the 2D plane.

    Args:
        center (skymap.geometry.Point): the center of the circle
        radius (float): the radius of the circle
    """

    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

    def __str__(self):
        return f"Circle({self.center}, {self.radius})"

    def __repr__(self):
        return self.__str__()

    def intersect_line(self, line):
        """Calculates the points of intersection of the given line with the circle.

        Returns a list containing zero or two intersection points: a line touching the
        circle is not counted as intersecting.

        Args:
            line (skymap.geometry.Line): the line to intersect
        """
        # ax+by+c = 0
        a = line.p1.y - line.p2.y
        b = line.p2.x - line.p1.x
        c = -line.p1.x * line.p2.y + line.p2.x * line.p1.y
        cp = c - a * self.center.x - b * self.center.y

        absq = a ** 2 + b ** 2

        # If line does not intersect circle, or touches circle: no intersection
        if absq * self.radius ** 2 - cp ** 2 <= 0:
            return []

        bigroot = math.sqrt(absq * self.radius ** 2 - cp ** 2)

        ksi1 = (a * cp + b * bigroot) / absq
        ksi2 = (a * cp - b * bigroot) / absq
        eta1 = (b * cp - a * bigroot) / absq
        eta2 = (b * cp + a * bigroot) / absq

        x1 = self.center.x + ksi1
        x2 = self.center.x + ksi2
        y1 = self.center.y + eta1
        y2 = self.center.y + eta2

        ip1 = Point(x1, y1)
        ip2 = Point(x2, y2)

        return ip1, ip2

    def inclusive_intersect_line(self, line):
        """Calculates the points of intersection of the given line with the circle that fall between
        both points defining the line.

        Args:
            line (skymap.geometry.Line): the line to intersect
        """
        intersections = self.intersect_line(line)
        inclusive_intersections = []
        for i in intersections:
            if line.point_on_line_segment(i):
                inclusive_intersections.append(i)
        return inclusive_intersections

    @property
    def path(self):
        """Returns the TikZ path string for the circle."""
        return f"{self.center.coordinates} circle ({self.radius}mm)"


class Arc(Circle):
    """A circular arc.

    Args:
        center (skymap.geometry.Point): the center of the circle
        radius (float): the radius of the circle
        start_angle (float): the angle defining the start of the arc
        stop_angle (float): the angle defining the end of the arc
    """

    def __init__(self, center, radius, start_angle, stop_angle):
        Circle.__init__(self, center, radius)
        self.start_angle = start_angle
        self.stop_angle = stop_angle
        sar = math.radians(self.start_angle)
        self.p1 = self.center + self.radius * Point(math.cos(sar), math.sin(sar))
        sar = math.radians(self.stop_angle)
        self.p2 = self.center + self.radius * Point(math.cos(sar), math.sin(sar))

    def __str__(self):
        return f"Arc({self.center}, {self.radius}, start={self.start_angle}, stop={self.stop_angle})"

    def interpolated_points(self, npoints=100):
        """Calculates a sequence of points approximating the arc.

        Args:
            npoints (int): the number of interpolated points
        """
        points = []
        delta_angle = self.stop_angle - self.start_angle
        for i in range(npoints):
            angle = self.start_angle + i * delta_angle / float(npoints - 1)
            p = self.center + self.radius * Point(
                math.cos(math.radians(angle)), math.sin(math.radians(angle))
            )
            points.append(p)
        return points

    def _path(self, reverse=False):
        """Builds the TikZ path string for the arc."""
        if self.radius < 1000:
            if reverse:
                start = self.stop_angle
                stop = self.start_angle
            else:
                start = self.start_angle
                stop = self.stop_angle

            path = f"([shift=({start}:{self.radius}mm)]"
            path += self.center.coordinates[1:]
            path += f" arc ({start}:{stop}:{self.radius}mm)"
        else:
            path = ""
            if reverse:
                pts = reversed(self.interpolated_points())
            else:
                pts = self.interpolated_points()
            for p in pts:
                path += f"{p.coordinates}--"
            path = path[:-2]
        return path

    @property
    def path(self):
        """Returns the TikZ path string for the arc."""
        return self._path()

    @property
    def reverse_path(self):
        """Returns the TikZ path string for the reverse arc."""
        return self._path(reverse=True)

    def reverse(self):
        return Arc(self.center, self.radius, self.stop_angle, self.start_angle)

    @property
    def point_halfway(self):
        half_angle = 0.5 * (self.start_angle + self.stop_angle)
        return self.center + self.radius * Point(
            math.cos(half_angle), math.sin(half_angle)
        )


class Rectangle(object):
    """A rectangle in 2D.

    Args:
        p1 (skymap.geometry.Point): the lower left corner of the rectangle
        p2 (skymap.geometry.Point): the upper right corner of the rectangle
    """

    def __init__(self, p1, p2):
        self.p1 = Point(min(p1.x, p2.x), min(p1.y, p2.y))
        self.p2 = Point(max(p1.x, p2.x), max(p1.y, p2.y))

    def __str__(self):
        return f"Rectangle({self.p1}, {self.p2})"

    @property
    def center(self):
        """Returns the geometric center of the rectangle."""
        return 0.5 * (self.p1 + self.p2)

    @property
    def size(self):
        """Returns a tuple of (width, height) for the rectangle."""
        return abs(self.p2.x - self.p1.x), abs(self.p2.y - self.p1.y)

    def overlap(self, other):
        """Calculates the overlap with other objects.

        Currently only Rectangle and Circle are implemented.

        Args:
            other: the object to calculate the overlap with
        """
        if isinstance(other, Rectangle):
            left = max(self.p1.x, other.p1.x)
            right = min(self.p2.x, other.p2.x)
            bottom = max(self.p1.y, other.p1.y)
            top = min(self.p2.y, other.p2.y)

            if left < right:
                w = right - left
            else:
                return 0
            if bottom < top:
                h = top - bottom
            else:
                return 0
            return w * h

        if isinstance(other, Circle):
            left = max(self.p1.x, other.center.x - other.radius)
            right = min(self.p2.x, other.center.x + other.radius)
            bottom = max(self.p1.y, other.center.y - other.radius)
            top = min(self.p2.y, other.center.y + other.radius)
            if left < right:
                w = right - left
            else:
                return 0
            if bottom < top:
                h = top - bottom
            else:
                return 0
            return w * h

        raise NotImplementedError(f"Cannot calculate the overlap for {other.__class__}")

    @property
    def points(self):
        """Returns the four corner points of the rectangle."""
        p1 = self.p1
        p2 = Point(self.p2.x, self.p1.y)
        p3 = self.p2
        p4 = Point(self.p1.x, self.p2.y)
        return [p1, p2, p3, p4]

    @property
    def path(self):
        """Returns the TikZ path string for the rectangle."""
        path = ""
        for p in self.points:
            path += p.coordinates
            path += "--"
        path += "cycle"
        return path


class Label(object):
    """A text label on the 2D plane.

    Args:
        point (skymap.geometry.Point): the anchor point for the label
        text (string): the text of the label
        fontsize (string): the LaTeX fontsize to use
        bold (bool): whether to use a bold font for the label
        position (string): the position of the label relative to the anchor point
        distance (float): the distance from the anchor point to place the label
        angle (float): the rotation of the label, in degrees
    """

    def __init__(
        self,
        point,
        text,
        fontsize,
        bold=False,
        position="above",
        distance=0,
        angle=0,
        fill=None,
    ):
        self.point = point
        self.text = text
        self.bold = bold
        self.position = position
        self.fontsize = fontsize
        self.angle = angle
        self.distance = distance
        self.fill = fill


class Clipper(object):
    def __init__(self, borderdict):
        self.borderdict = borderdict
        self.minx, self.miny = self.borderdict["bottom"].p1
        self.maxx, self.maxy = self.borderdict["top"].p1

    def point_inside(self, p):
        """Check whether the given point lies within the map area"""
        if p.x < self.minx or p.x > self.maxx or p.y < self.miny or p.y > self.maxy:
            return False
        else:
            return True

    def circle_inside(self, circle):
        """Check whether the given circle lies fully inside the map area"""
        if not self.point_inside(circle.center):
            print("Circle center outside")
            return False

        for b in self.borderdict.values():
            if circle.radius > b.distance_point(circle.center) + 1e-6:
                print(
                    f"Circle radius ({circle.radius}) larger than distance to border ({b.distance_point(circle.center)})"
                )
                return False
        return True

    def line_intersect_borders(self, line):
        crossings = []
        labelpositions = []

        for bordername, border in self.borderdict.items():
            c = border.inclusive_intersect_line(line)
            if len(c) == 1:
                if c[0] not in crossings:
                    crossings.append(c[0])
                    labelpositions.append(bordername)

        return list(zip(crossings, labelpositions))

    def clip_line(self, line):
        intersections = self.line_intersect_borders(line)
        if not intersections:
            if self.point_inside(0.5 * (line.p1 + line.p2)):
                return [line], [(None, None)]
            else:
                return [None], []

        if len(intersections) == 1:
            # Check whether p1 or p2 is on the border
            if line.p1.distance(intersections[0][0]) < 1e-6:
                # p1 is on border
                p1, border1 = intersections[0]
                p2, border2 = line.p2, None
            elif line.p2.distance(intersections[0][0]) < 1e-6:
                # p2 is on border
                p1, border1 = line.p1, None
                p2, border2 = intersections[0]
            elif self.point_inside(0.5 * (line.p1 + intersections[0][0])):
                p1, border1 = line.p1, None
                p2, border2 = intersections[0]
            elif self.point_inside(0.5 * (line.p2 + intersections[0][0])):
                p1, border1 = intersections[0]
                p2, border2 = line.p2, None
            else:
                raise RuntimeError("Inconsistent intersection")
        else:
            d1 = line.p1.distance(intersections[0][0])
            d2 = line.p2.distance(intersections[0][0])
            if d1 < d2:
                p1, border1 = intersections[0]
                p2, border2 = intersections[1]
            else:
                p1, border1 = intersections[1]
                p2, border2 = intersections[0]

        if p1 == p2:
            return [], [None, None]

        line = Line(p1, p2)
        return [line], [(border1, border2)]

    def clip_polygon(self, polygon):
        new_lines = []
        border1 = None
        border2 = None

        for l in polygon.lines:
            lines, borders = self.clip_line(l)
            for nl in lines:
                if nl is not None:
                    new_lines.append(nl)
                    if border1 is None:
                        border1 = borders[0][0]
                    border2 = borders[0][1]
        if not new_lines:
            return [], []
        points = [l.p1 for l in new_lines]
        points.append(new_lines[-1].p2)
        return [Polygon(points, closed=False)], [(border1, border2)]

    def circle_intersect_borders(self, circle):
        crossings = []
        borders = []
        angles = []
        center = circle.center

        for bordername, border in self.borderdict.items():
            ccs = circle.inclusive_intersect_line(border)
            for c in ccs:
                if c not in crossings:
                    crossings.append(c)
                    borders.append(bordername)
                    angle = math.degrees(math.atan2(c.y - center.y, c.x - center.x))
                    angles.append(angle)

        ordered_crossings = sorted(zip(angles, crossings, borders))

        return ordered_crossings

    def clip_circle(self, circle):
        intersections = self.circle_intersect_borders(circle)
        if not intersections:
            # Only option to check is whether the circle lies fully inside
            if self.circle_inside(circle):
                return [circle], [(None, None)]
            else:
                return [], []
        else:
            arcs = []
            borders = []
            angles = []
            for i in range(len(intersections)):
                a1, c1, b1 = intersections[i - 1]
                a2, c2, b2 = intersections[i]
                if a1 > a2:
                    a2 += 360.0
                avg_angle = math.radians(0.5 * (a1 + a2))
                avg_point = circle.center + Point(
                    circle.radius * math.cos(avg_angle),
                    circle.radius * math.sin(avg_angle),
                )

                if self.point_inside(avg_point):
                    arcs.append(Arc(circle.center, circle.radius, a1, a2))
                    borders.append((b1, b2))
                    angles.append((a1 - 90, a2 + 90))

            return arcs, borders

    def clip(self, item):
        if isinstance(item, Line):
            return self.clip_line(item)
        elif isinstance(item, Circle):
            return self.clip_circle(item)
        elif isinstance(item, Polygon):
            return self.clip_polygon(item)
        else:
            raise NotImplementedError


class SkyClipper(object):
    def __init__(self, min_longitude, max_longitude, min_latitude, max_latitude):
        self.min_longitude = min_longitude
        self.max_longitude = max_longitude
        self.min_latitude = min_latitude
        self.max_latitude = max_latitude

        self.center_longitude = 0.5 * (self.min_longitude + self.max_longitude)
        self.center_latitude = 0.5 * (self.min_latitude + self.max_latitude)

    def point_inside(self, sp):
        longitude = ensure_angle_range(sp.ra.degree, self.center_longitude)
        latitude = sp.dec.degree
        if (
            longitude < self.min_longitude
            or longitude > self.max_longitude
            or latitude < self.min_latitude
            or latitude > self.max_latitude
        ):
            return False
        return True

    def clip_line(self, sp1, sp2):
        sp1_in = self.point_inside(sp1)
        sp2_in = self.point_inside(sp2)
        if sp1_in == sp2_in:
            if sp1_in:
                return sp1, sp2
            else:
                return None
        else:
            pass

    def clip(self, item):
        pass


def ensure_angle_range(angle, center=180.0):
    """Ensures the angle is constrained to the center +/- 180 degrees.

    Args:
        angle (float): the angle to reduce
        center (float): the center of the range
    """
    while angle < center - 180.0:
        angle += 360.0
    while angle >= center + 180.0:
        angle -= 360
    return angle
