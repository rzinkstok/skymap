import math
import time
from rtree.index import Index


AVG_POINT_PER_CHAR = 0.3
POINTSIZE = 11
MM_PER_POINT = 0.352778
AVG_CHAR_WIDTH = AVG_POINT_PER_CHAR * POINTSIZE * MM_PER_POINT
CHAR_HEIGHT = 1.5 * MM_PER_POINT * POINTSIZE

POINT_PENALTY = 100
BBOX_PENALTY = 500


def evaluate_labels(labels, points, bounding_box, include_position=True):
    # print "Labels:", len(labels)
    # print "Points:", len(points)
    # print "Bounding box:", bounding_box

    t1 = time.clock()
    idx = Index()
    label_penalties = {}

    t1a = time.clock()
    for i, label in enumerate(labels):
        label.index = i
        idx.insert(i, label.box)
        if include_position:
            label_penalties[i] = label.position
        else:
            label_penalties[i] = 0
    t1b = time.clock()
    #print "Index creation:", t1b-t1a

    # Update penalties for overlap with other candidates
    for l1 in labels:
        intersecting_label_ids = idx.intersection(l1.box)
        for l2i in intersecting_label_ids:
            l2 = labels[l2i]
            if l2i == l1.index:
                continue
            if l1.point == l2.point:
                continue
            penalty = l1.overlap(l2, True)
            label_penalties[l1.index] += penalty
            label_penalties[l2.index] += penalty
    t1c = time.clock()
    #print "Label - label overlap:", t1c - t1b

    # Update penalties for overlap with points
    for p in points:
        intersecting_label_ids = idx.intersection(p.box)
        for li in intersecting_label_ids:
            l = labels[li]
            penalty = l.overlap_point(p)
            if penalty > 0:
                label_penalties[l.index] += POINT_PENALTY
    t1d = time.clock()
    #print "Label - point overlap:", t1d - t1c

    # Update penalties for bounding box
    borders = [
        (bounding_box[0] - 1, bounding_box[1] - 1, bounding_box[0], bounding_box[3] + 1),
        (bounding_box[2], bounding_box[1] - 1, bounding_box[2] + 1, bounding_box[3] + 1),
        (bounding_box[0] - 1, bounding_box[1] - 1, bounding_box[2] + 1, bounding_box[1]),
        (bounding_box[0] - 1, bounding_box[3], bounding_box[2] + 1, bounding_box[3] + 1)
    ]
    for b in borders:
        intersecting_label_ids = idx.intersection(b)
        for li in intersecting_label_ids:
            l = labels[li]
            label_penalties[l.index] += BBOX_PENALTY

    t2 = time.clock()
    #print "Label - border overlap:", t2 - t1d
    print "Total time:", t2 - t1
    return label_penalties




class Label(object):
    def __init__(self, point, text, position, offset):
        self.index = None
        self.point = point
        self.text = text
        self.position = position
        self.width = AVG_CHAR_WIDTH * len(text)
        self.height = CHAR_HEIGHT
        self.offset = offset
        self.angle_offset = offset/math.sqrt(2)
        self.penalty = position
        self.overlapping = []

        if position == 0:
            self.minx = self.point.x + self.point.radius + self.offset
            self.maxx = self.point.x + self.point.radius + self.offset + self.width
            self.miny = self.point.y - 0.5 * self.height
            self.maxy = self.point.y + 0.5 * self.height
        elif position == 1:
            self.minx = self.point.x + self.point.radius + self.angle_offset
            self.maxx = self.point.x + self.point.radius + self.angle_offset + self.width
            self.miny = self.point.y + self.point.radius + self.angle_offset
            self.maxy = self.point.y + self.point.radius + self.angle_offset + self.height
        elif position == 2:
            self.minx = self.point.x - 0.5 * self.width
            self.maxx = self.point.x + 0.5 * self.width
            self.miny = self.point.y + self.point.radius + self.offset
            self.maxy = self.point.y + self.point.radius + self.offset + self.height
        elif position == 3:
            self.minx = self.point.x - self.point.radius - self.angle_offset - self.width
            self.maxx = self.point.x - self.point.radius - self.angle_offset
            self.miny = self.point.y + self.point.radius + self.angle_offset
            self.maxy = self.point.y + self.point.radius + self.angle_offset + self.height
        elif position == 4:
            self.minx = self.point.x - self.point.radius - self.offset - self.width
            self.maxx = self.point.x - self.point.radius - self.offset
            self.miny = self.point.y - 0.5 * self.height
            self.maxy = self.point.y + 0.5 * self.height
        elif position == 5:
            self.minx = self.point.x - self.point.radius - self.angle_offset - self.width
            self.maxx = self.point.x - self.point.radius - self.angle_offset
            self.miny = self.point.y - self.point.radius - self.angle_offset - self.height
            self.maxy = self.point.y - self.point.radius - self.angle_offset
        elif position == 6:
            self.minx = self.point.x - 0.5 * self.width
            self.maxx = self.point.x + 0.5 * self.width
            self.miny = self.point.y - self.point.radius - offset - self.height
            self.maxy = self.point.y - self.point.radius - offset
        elif position == 7:
            self.minx = self.point.x + self.point.radius + self.angle_offset
            self.maxx = self.point.x + self.point.radius + self.angle_offset + self.width
            self.miny = self.point.y - self.point.radius - self.angle_offset - self.height
            self.maxy = self.point.y - self.point.radius - self.angle_offset

    def overlap(self, other, record=False):
        left = max(self.minx, other.box[0])
        right = min(self.maxx, other.box[2])
        bottom = max(self.miny, other.box[1])
        top = min(self.maxy, other.box[3])

        if left < right:
            w = right - left
        else:
            return 0
        if bottom < top:
            h = top - bottom
        else:
            return 0

        if record:
            if other not in self.overlapping:
                self.overlapping.append(other)
            if self not in other.overlapping:
                other.overlapping.append(other)

        return w * h

    def overlap_point(self, point):
        return self.overlap(point)

    def area(self):
        return (self.maxx - self.minx) * (self.maxy - self.miny)

    def select(self):
        self.point.label_index = self.position

    @property
    def box(self):
        return self.minx, self.miny, self.maxx, self.maxy


class Point(object):
    def __init__(self, x, y, radius, text=None, label_offset=0):
        self.x = x
        self.y = y
        self.radius = radius
        self.text = text
        self.label_offset = label_offset

        self.label_candidates = []
        self.label_index = None

        if text:
            self.build_labels()

    @property
    def label(self):
        if self.label_index is not None:
            return self.label_candidates[self.label_index]
        return None

    def build_labels(self):
        for i in range(8):
            self.label_candidates.append(Label(self, self.text, i, self.label_offset))

    @property
    def box(self):
        return self.x-self.radius, self.y - self.radius, self.x + self.radius, self.y + self.radius


class PointOld(object):
    def __init__(self, point, radius):
        self.point = point
        self.radius = radius


class LabeledPointOld(object):
    def __init__(self, point, radius, text, pointsize, offset):
        self.point = point
        self.radius = radius
        self.text = text
        self.pointsize = pointsize
        self.offset = offset
        self.width = self.pointsize * AVG_POINT_PER_CHAR * MM_PER_POINT * len(text)
        self.height = 1.5 * MM_PER_POINT * pointsize
        self.candidates = [CandidateOld(self, i, offset) for i in range(8)]
        self.selected_candidate = None

    def select_candidate(self, candidate):
        self.selected_candidate = candidate.position

    @property
    def label(self):
        return self.candidates[self.selected_candidate]


class CandidateOld(object):
    def __init__(self, labeled_point, position, offset):
        self.labeled_point = labeled_point
        self.position = position
        self.offset = offset
        self.penalty = self.position
        self.overlapping = []

        if position == 0:
            self.minx = self.labeled_point.point[0] + self.labeled_point.radius + offset
            self.maxx = self.labeled_point.point[0] + self.labeled_point.radius + offset + self.labeled_point.width
            self.miny = self.labeled_point.point[1] - 0.5 * self.height
            self.maxy = self.labeled_point.point[1] + 0.5 * self.height
        elif position == 1:
            o = self.offset/math.sqrt(2)
            self.minx = self.labeled_point.point[0] + self.labeled_point.radius + o
            self.maxx = self.labeled_point.point[0] + self.labeled_point.radius + o + self.labeled_point.width
            self.miny = self.labeled_point.point[1] + self.labeled_point.radius + o
            self.maxy = self.labeled_point.point[1] + self.labeled_point.radius + o + self.height
        elif position == 2:
            self.minx = self.labeled_point.point[0] - 0.5 * self.labeled_point.width
            self.maxx = self.labeled_point.point[0] + 0.5 * self.labeled_point.width
            self.miny = self.labeled_point.point[1] + self.labeled_point.radius + offset
            self.maxy = self.labeled_point.point[1] + self.labeled_point.radius + offset + self.height
        elif position == 3:
            o = self.offset / math.sqrt(2)
            self.minx = self.labeled_point.point[0] - self.labeled_point.radius - o - self.labeled_point.width
            self.maxx = self.labeled_point.point[0] - self.labeled_point.radius - o
            self.miny = self.labeled_point.point[1] + self.labeled_point.radius + o
            self.maxy = self.labeled_point.point[1] + self.labeled_point.radius + o + self.height
        elif position == 4:
            self.minx = self.labeled_point.point[0] - self.labeled_point.radius - offset - self.labeled_point.width
            self.maxx = self.labeled_point.point[0] - self.labeled_point.radius - offset
            self.miny = self.labeled_point.point[1] - 0.5 * self.height
            self.maxy = self.labeled_point.point[1] + 0.5 * self.height
        elif position == 5:
            o = self.offset / math.sqrt(2)
            self.minx = self.labeled_point.point[0] - self.labeled_point.radius - o - self.labeled_point.width
            self.maxx = self.labeled_point.point[0] - self.labeled_point.radius - o
            self.miny = self.labeled_point.point[1] - self.labeled_point.radius - o - self.height
            self.maxy = self.labeled_point.point[1] - self.labeled_point.radius - o
        elif position == 6:
            self.minx = self.labeled_point.point[0] - 0.5 * self.labeled_point.width
            self.maxx = self.labeled_point.point[0] + 0.5 * self.labeled_point.width
            self.miny = self.labeled_point.point[1] - self.labeled_point.radius - offset - self.height
            self.maxy = self.labeled_point.point[1] - self.labeled_point.radius - offset
        elif position == 7:
            o = self.offset / math.sqrt(2)
            self.minx = self.labeled_point.point[0] + self.labeled_point.radius + o
            self.maxx = self.labeled_point.point[0] + self.labeled_point.radius + o + self.labeled_point.width
            self.miny = self.labeled_point.point[1] - self.labeled_point.radius - o - self.height
            self.maxy = self.labeled_point.point[1] - self.labeled_point.radius - o

    def intersection_rectangle(self, other, record_overlap=True):
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
        return POINT_PENALTY

    def area(self):
        return (self.maxx - self.minx) * (self.maxy - self.miny)
