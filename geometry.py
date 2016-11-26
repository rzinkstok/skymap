import math


class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

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
    return (center[0] + new_dx, center[1] + new_dy)


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

    ip1 = (x1, y1)
    ip2 = (x2, y2)

    return ip1, ip2

def distance(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)