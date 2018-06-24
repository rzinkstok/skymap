import math

MM_PER_POINT = 0.352778
AVG_POINT_PER_CHAR = 0.3
POINT_OVERLAP_PENALTY = 1000


class Point(object):
    def __init__(self, point, radius):
        self.point = point
        self.radius = radius


class LabeledPoint(object):
    def __init__(self, point, radius, text, pointsize, offset):
        self.point = point
        self.radius = radius
        self.text = text
        self.pointsize = pointsize
        self.offset = offset
        self.width = self.pointsize * AVG_POINT_PER_CHAR * MM_PER_POINT * len(text)
        self.height = 1.5 * MM_PER_POINT * pointsize
        self.candidates = [Candidate(self, i, offset) for i in range(8)]
        self.selected_candidate = -1

    def select_candidate(self, candidate):
        self.selected_candidate = candidate.position


class Candidate(object):
    def __init__(self, labeled_point, position, offset):
        self.labeled_point = labeled_point
        self.position = position
        self.offset = offset
        self.penalty = self.position
        self.overlapping = []

        if position == 0:
            self.minx = self.labeled_point.point[0] + self.labeled_point.radius + offset
            self.maxx = self.labeled_point.point[0] + self.labeled_point.radius + offset + self.labeled_point.width
            self.miny = self.labeled_point.point[1] - 0.5 * self.labeled_point.height
            self.maxy = self.labeled_point.point[1] + 0.5 * self.labeled_point.height
        elif position == 1:
            o = self.offset/math.sqrt(2)
            self.minx = self.labeled_point.point[0] + self.labeled_point.radius + o
            self.maxx = self.labeled_point.point[0] + self.labeled_point.radius + o + self.labeled_point.width
            self.miny = self.labeled_point.point[1] + self.labeled_point.radius + o
            self.maxy = self.labeled_point.point[1] + self.labeled_point.radius + o + self.labeled_point.height
        elif position == 2:
            self.minx = self.labeled_point.point[0] - 0.5 * self.labeled_point.width
            self.maxx = self.labeled_point.point[0] + 0.5 * self.labeled_point.width
            self.miny = self.labeled_point.point[1] + self.labeled_point.radius + offset
            self.maxy = self.labeled_point.point[1] + self.labeled_point.radius + offset + self.labeled_point.height
        elif position == 3:
            o = self.offset / math.sqrt(2)
            self.minx = self.labeled_point.point[0] - self.labeled_point.radius - o - self.labeled_point.width
            self.maxx = self.labeled_point.point[0] - self.labeled_point.radius - o
            self.miny = self.labeled_point.point[1] + self.labeled_point.radius + o
            self.maxy = self.labeled_point.point[1] + self.labeled_point.radius + o + self.labeled_point.height
        elif position == 4:
            self.minx = self.labeled_point.point[0] - self.labeled_point.radius - offset - self.labeled_point.width
            self.maxx = self.labeled_point.point[0] - self.labeled_point.radius - offset
            self.miny = self.labeled_point.point[1] - 0.5 * self.labeled_point.height
            self.maxy = self.labeled_point.point[1] + 0.5 * self.labeled_point.height
        elif position == 5:
            o = self.offset / math.sqrt(2)
            self.minx = self.labeled_point.point[0] - self.labeled_point.radius - o - self.labeled_point.width
            self.maxx = self.labeled_point.point[0] - self.labeled_point.radius - o
            self.miny = self.labeled_point.point[1] - self.labeled_point.radius - o - self.labeled_point.height
            self.maxy = self.labeled_point.point[1] - self.labeled_point.radius - o
        elif position == 6:
            self.minx = self.labeled_point.point[0] - 0.5 * self.labeled_point.width
            self.maxx = self.labeled_point.point[0] + 0.5 * self.labeled_point.width
            self.miny = self.labeled_point.point[1] - self.labeled_point.radius - offset - self.labeled_point.height
            self.maxy = self.labeled_point.point[1] - self.labeled_point.radius - offset
        elif position == 7:
            o = self.offset / math.sqrt(2)
            self.minx = self.labeled_point.point[0] + self.labeled_point.radius + o
            self.maxx = self.labeled_point.point[0] + self.labeled_point.radius + o + self.labeled_point.width
            self.miny = self.labeled_point.point[1] - self.labeled_point.radius - o - self.labeled_point.height
            self.maxy = self.labeled_point.point[1] - self.labeled_point.radius - o

    def intersection_candidate(self, other, record_overlap=True):
        left = max(self.minx, other.minx)
        right = min(self.maxx, other.maxx)
        bottom = max(self.miny, other.miny)
        top = min(self.maxy, other.maxy)

        if left < right:
            w = right - left
        else:
            return 0
        if bottom < top:
            h = top - bottom
        else:
            return 0

        if record_overlap and (other not in self.overlapping):
            self.overlapping.append(other)

        return w * h

    def intersection_point(self, point):
        left = max(self.minx, point.point[0] - point.radius)
        right = min(self.maxx, point.point[0] + point.radius)
        bottom = max(self.miny, point.point[1] - point.radius)
        top = min(self.maxy, point.point[1] + point.radius)

        if left >= right:
            return 0
        if bottom >= top:
            return 0
        return POINT_OVERLAP_PENALTY

    def area(self):
        return (self.maxx - self.minx) * (self.maxy - self.miny)