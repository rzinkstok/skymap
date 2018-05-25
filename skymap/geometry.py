import math
from astropy.coordinates import SkyCoord
from astropy import units


TOLERANCE = 1e-12


class SkyCoordDeg(SkyCoord):
    def __init__(self, *args, **kwargs):
        if "unit" not in kwargs:
            kwargs["unit"] = units.deg
        SkyCoord.__init__(self, *args, **kwargs)

    def __eq__(self, other):
        return (abs(self.dec.degree - other.dec.degree) < TOLERANCE) and (abs(self.ra.degree - other.ra.degree) < TOLERANCE)

    def __ne__(self, other):
        return not self == other



def point_to_coordinates(point):
    x = point.x
    y = point.y
    if abs(x) < 1e-4:
        x = 0.0
    if abs(y) < 1e-4:
        y = 0.0

    return "({0}mm,{1}mm)".format(x, y)


class HourAngle(object):
    def __init__(self, hours=0, minutes=0, seconds=0):
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

    def to_degrees(self):
        return 15.0*self.hours + 0.25*self.minutes + 0.25*self.seconds/60.0

    def from_degrees(self, degrees):
        while degrees < 0:
            degrees += 360.0

        hours, rest = divmod(degrees, 15.0)
        minutes, rest = divmod(60.0*rest/15.0, 1)
        self.hours = int(round(hours))
        self.minutes = int(round(minutes))
        self.seconds = 60*rest

    def from_fractional_hours(self, fractional_hours):
        self.hours= int(fractional_hours)
        fractional_minutes = (fractional_hours - self.hours) * 60.0
        self.minutes = int(fractional_minutes)
        self.seconds = (fractional_minutes - self.minutes) * 60.0

    def to_fractional_hours(self):
        return self.hours + self.minutes/60.0 + self.seconds/3600.0

    def __repr__(self):
        return "HA {0}h {1}m {2}s".format(self.hours, self.minutes, self.seconds)

    def __str__(self):
        return self.__repr__()


class DMSAngle(object):
    def __init__(self, degrees=0, minutes=0, seconds=0, sign=1):
        self.degrees = degrees
        self.minutes = minutes
        self.seconds = seconds
        self.sign = sign

    def from_degrees(self, degrees):
        sign = degrees>=0
        degrees = abs(degrees)
        degrees, rest = divmod(degrees, 1)
        minutes, rest = divmod(60.0*rest, 1)
        seconds = 60.0*rest
        if sign:
            self.sign = 1
        else:
            self.sign = -1
        self.degrees = int(degrees)
        self.minutes = int(minutes)
        self.seconds = seconds

    def to_degrees(self):
        degrees = self.sign * self.degrees
        degrees += self.sign * self.minutes/60.0
        degrees += self.sign * self.seconds/3600.0
        return degrees

    def __repr__(self):
        result =  "{0}d {1}' {2}\"".format(self.degrees, self.minutes, self.seconds)
        if self.sign < 0:
            result = "-" + result
        return result

    def __str__(self):
        return self.__repr__()


class Point(object):
    def __init__(self, a, b=None):
        if b is None:
            self.x, self.y = a
        else:
            self.x = a
            self.y = b

    def __str__(self):
        return "Point({0}, {1})".format(self.x, self.y)

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

    def __div__(self, other):
        other = float(other)
        return self.__class__(self.x/other, self.y/other)

    def __eq__(self, other):
        return self.distance(other) < 1e-6

    def __ne__(self, other):
        return not self.__eq__(other)

    def distance(self, other):
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def rotate(self, angle, origin=None):
        if origin is None:
            origin = Point(0,0)
        angle = math.radians(angle)
        dx = self.x - origin.x
        dy = self.y - origin.y
        new_dx = dx*math.cos(angle) - dy*math.sin(angle)
        new_dy = dx*math.sin(angle) + dy*math.cos(angle)
        x = origin.x + new_dx
        y = origin.y + new_dy
        return self.__class__(x, y)

    @property
    def norm(self):
        return self.distance(Point(0,0))


class SphericalPoint(Point):
    """
    A point on the sphere specified by a longitude and a latitude.
    """
    def __init__(self, a, b=None):
        """
        Initialize the point from a tuple or two numbers
        :param a: longitude or tuple (longitude, latitude)
        :param b: latitude or None
        """
        Point.__init__(self, a, b)

    def __str__(self):
        return "SphericalPoint({}, {})".format(self.longitude, self.latitude)

    @property
    def longitude(self):
        return self.x

    @longitude.setter
    def longitude(self, longitude):
        self.x = longitude

    @property
    def latitude(self):
        return self.y

    @latitude.setter
    def latitude(self, latitude):
        self.y = latitude

    @property
    def ra(self):
        return self.x

    @ra.setter
    def ra(self, ra):
        self.x = ra

    @property
    def dec(self):
        return self.y

    @dec.setter
    def dec(self, dec):
        self.y = dec

    def reduce(self):
        while self.longitude < 0:
            self.longitude += 360.0
        while self.longitude >= 360.0:
            self.longitude -= 360

    def __eq__(self, other):
        p1 = SphericalPoint(self)
        p2 = SphericalPoint(other)
        p1.reduce()
        p2.reduce()
        return Point(p1) == Point(p2)


class Line(object):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.vector = p2 - p1
        self.length = self.p1.distance(self.p2)

    def __str__(self):
        return "Line({}, {})".format(self.p1, self.p2)

    def intersect_line(self, other):
        a1 = self.p1.y - self.p2.y
        b1 = self.p2.x - self.p1.x
        c1 = self.p1.x * self.p2.y - self.p2.x * self.p1.y

        a2 = other.p1.y - other.p2.y
        b2 = other.p2.x - other.p1.x
        c2 = other.p1.x * other.p2.y - other.p2.x * other.p1.y

        den = (a1 * b2 - a2 * b1)
        if abs(den) == 0.0:
            return None

        y = (c1 * a2 - c2 * a1) / den
        x = (b1 * c2 - c1 * b2) / den
        return Point(x, y)

    def inclusive_intersect_line(self, other):
        p = self.intersect_line(other)
        if p is None:
            return []
        if self.point_on_line_segment(p) and other.point_on_line_segment(p):
            return [p]
        return []

    def point_on_line_segment(self, p):
        point_vector = p - self.p1
        ip = (point_vector.x * self.vector.x + point_vector.y * self.vector.y)
        comp = ip/self.length
        if comp >= 0 and comp <= self.length:
            return True
        return False

    @property
    def angle(self):
        d = self.p2 - self.p1
        return math.degrees(math.atan2(d.y, d.x))

    @property
    def path(self):
        return "{}--{}".format(point_to_coordinates(self.p1), point_to_coordinates(self.p2))

    @property
    def reverse_path(self):
        return "{}--{}".format(point_to_coordinates(self.p2), point_to_coordinates(self.p1))


class Polygon(object):
    def __init__(self, points=[], closed=True):
        self.points = []
        self.lines = []
        self.closed = closed
        for p in points:
            self.add_point(p)
        if closed:
            self.close()

    def add_point(self, p):
        self.points.append(p)
        if len(self.points) > 1:
            self.lines.append(Line(self.points[-2], self.points[-1]))

    def close(self):
        if not self.closed:
            self.closed = True
        self.lines.append(Line(self.points[-1], self.points[0]))


class Circle(object):
    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

    def __str__(self):
        return "Circle({0}, {1})".format(self.center, self.radius)

    def __repr__(self):
        return self.__str__()

    def intersect_line(self, line):
        # ax+by+c = 0
        a = line.p1.y - line.p2.y
        b = line.p2.x - line.p1.x
        c = - line.p1.x * line.p2.y + line.p2.x * line.p1.y
        cp = c - a * self.center.x - b * self.center.y

        absq = (a ** 2 + b ** 2)

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
        intersections = self.intersect_line(line)
        inclusive_intersections = []
        for i in intersections:
            if line.point_on_line_segment(i):
                inclusive_intersections.append(i)
        return inclusive_intersections

    @property
    def path(self):
        return "{} circle ({}mm)".format(point_to_coordinates(self.center), self.radius)


class Arc(Circle):
    def __init__(self, center, radius, start_angle, stop_angle):
        Circle.__init__(self, center, radius)
        self.start_angle = start_angle
        self.stop_angle = stop_angle
        self.start_mp = 8 * start_angle / 360.0
        self.stop_mp = 8 * stop_angle / 360.0
        sar = math.radians(self.start_angle)
        self.p1 = self.center + self.radius * Point(math.cos(sar), math.sin(sar))
        sar = math.radians(self.stop_angle)
        self.p2 = self.center + self.radius * Point(math.cos(sar), math.sin(sar))

    def __str__(self):
        return "Arc({}, {}, start={}, stop={})".format(self.center, self.radius, self.start_angle, self.stop_angle)

    def interpolated_points(self, npoints=100):
        points = []
        delta_angle = self.stop_angle - self.start_angle
        for i in range(npoints):
            angle = self.start_angle + i * delta_angle / float(npoints-1)
            p = self.center + self.radius * Point(math.cos(math.radians(angle)), math.sin(math.radians(angle)))
            points.append(p)
        return points

    def _path(self, reverse=False):
        if self.radius < 1000:
            if reverse:
                start = self.stop_angle
                stop = self.start_angle
            else:
                start = self.start_angle
                stop = self.stop_angle

            path = "([shift=({}:{}mm)]".format(start, self.radius)
            path += point_to_coordinates(self.center)[1:]
            path += " arc ({}:{}:{}mm)".format(start, stop, self.radius)
        else:
            path = ""
            if reverse:
                pts = reversed(self.interpolated_points())
            else:
                pts = self.interpolated_points()
            for p in pts:
                path += "{}--".format(point_to_coordinates(p))
            path = path[:-2]
        return path

    @property
    def path(self):
        return self._path()

    @property
    def reverse_path(self):
        return self._path(reverse=True)


class Rectangle(object):
    def __init__(self, p1, p2):
        self.p1 = Point(min(p1.x, p2.x), min(p1.y, p2.y))
        self.p2 = Point(max(p1.x, p2.x), max(p1.y, p2.y))

    def __str__(self):
        return "Rectangle({}, {})".format(self.p1, self.p2)

    @property
    def center(self):
        return 0.5*(self.p1 + self.p2)

    @property
    def size(self):
        return abs(self.p2.x-self.p1.x), abs(self.p2.y - self.p1.y)

    def overlap(self, other):
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
            return w*h

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
            return w*h

    @property
    def points(self):
        p1 = self.p1
        p2 = Point(self.p2.x, self.p1.y)
        p3 = self.p2
        p4 = Point(self.p1.x, self.p2.y)
        return [p1, p2, p3, p4]

    @property
    def path(self):
        path = ""
        for p in self.points:
            path += point_to_coordinates(p)
            path += "--"
        path += "cycle"
        return path


def ensure_angle_range(angle, center=180):
    while angle < center - 180.0:
        angle += 360.0
    while angle >= center + 180.0:
        angle -= 360
    return angle