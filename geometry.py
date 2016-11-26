import math


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

    def __repr__(self):
        return "HA {0}h {1}m {2}s".format(self.hours, self.minutes, self.seconds)

    def __str__(self):
        return self.__repr__()


class DMSAngle(object):
    def __init__(self, degrees=0, minutes=0, seconds=0):
        self.degrees = degrees
        self.minutes = minutes
        self.seconds = seconds

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
        return Point(x, y)

    def __sub__(self, other):
        x = self.x - other.x
        y = self.y - other.y
        return Point(x, y)

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
        return Point(x, y)


def rotate_point(p, center, angle):
    angle = math.radians(angle)
    dx = p[0]-center[0]
    dy = p[1]-center[1]
    new_dx = dx*math.cos(angle) - dy*math.sin(angle)
    new_dy = dx*math.sin(angle) + dy*math.cos(angle)
    return Point(center[0] + new_dx, center[1] + new_dy)


def intersection_line_line(l1p1, l1p2, l2p1, l2p2):
    a1 = l1p1.y - l1p2.y
    b1 = l1p2.x - l1p1.x
    c1 = l1p1.x * l1p2.y - l1p2.x * l1p1.y

    a2 = l2p1.y - l2p2.y
    b2 = l2p2.x - l2p1.x
    c2 = l2p1.x * l2p2.y - l2p2.x * l2p1.y

    den = (a1*b2 - a2*b1)
    if abs(den) == 0.0:
        return None

    y = (c1*a2 - c2*a1)/den
    x = (b1*c2 - c1*b2)/den
    return Point(x, y)


def intersection_line_circle(p1, p2, center, r):
    # ax+by+c = 0
    a = p1[1]-p2[1]
    b = p2[0]-p1[0]
    c = - p1[0]*p2[1] + p2[0]*p1[1]
    cp = c - a*center[0] - b*center[1]

    absq = (a**2 + b**2)

    if absq * r**2 - cp**2 <=0:
        return []

    bigroot = math.sqrt(absq * r**2 - cp**2)

    ksi1 = (a*cp + b*bigroot)/absq
    ksi2 = (a*cp - b*bigroot)/absq
    eta1 = (b*cp - a*bigroot)/absq
    eta2 = (b*cp + a*bigroot)/absq

    x1 = center[0] + ksi1
    x2 = center[0] + ksi2
    y1 = center[1] + eta1
    y2 = center[1] + eta2

    ip1 = Point(x1, y1)
    ip2 = Point(x2, y2)

    return ip1, ip2

def distance(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)