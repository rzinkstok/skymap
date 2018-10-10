import math
import time
from rtree.index import Index


AVG_POINT_PER_CHAR = 0.3
POINTSIZE = 11
MM_PER_POINT = 0.352_778
AVG_CHAR_WIDTH = AVG_POINT_PER_CHAR * POINTSIZE * MM_PER_POINT
CHAR_HEIGHT = 1.5 * MM_PER_POINT * POINTSIZE

POINT_PENALTY = 10
BBOX_PENALTY = 20
POSITION_WEIGHT = 0.1


def create_bounding_box_borders(bounding_box):
    border_boxes = [
        (
            bounding_box[0] - 1,
            bounding_box[1] - 1,
            bounding_box[0],
            bounding_box[3] + 1,
        ),
        (
            bounding_box[2],
            bounding_box[1] - 1,
            bounding_box[2] + 1,
            bounding_box[3] + 1,
        ),
        (
            bounding_box[0] - 1,
            bounding_box[1] - 1,
            bounding_box[2] + 1,
            bounding_box[1],
        ),
        (
            bounding_box[0] - 1,
            bounding_box[3],
            bounding_box[2] + 1,
            bounding_box[3] + 1,
        ),
    ]
    return [BoundingBoxBorder(b) for b in border_boxes]


def evaluate_label(label, items, idx, selected_only=False):
    penalty = POSITION_WEIGHT * label.position
    intersecting_item_ids = idx.intersection(label.box)
    bbox_counted = False
    for item_id in intersecting_item_ids:
        item = items[item_id]

        if item == label or item == label.point:
            continue

        if isinstance(item, Label):
            if label.point == item.point:
                continue
            if selected_only and not item.selected:
                continue

        if isinstance(item, BoundingBoxBorder):
            if bbox_counted:
                continue
            bbox_counted = True

        penalty += item.overlap(label, True)
    label.penalty = penalty
    return penalty


def evaluate_labels(labels, points, bounding_box):
    items = []
    items.extend(labels)
    items.extend(points)
    items.extend(bounding_box.borders)

    t1 = time.clock()
    idx = Index()

    for i, item in enumerate(items):
        item.index = i
        idx.insert(i, item.box)

    t2 = time.clock()
    # print(f"Index creation: {t2-t1}")

    # Update penalties for overlap with other objects
    penalties = [evaluate_label(l, items, idx) for l in labels]

    t3 = time.clock()
    # print(f"Overlap checking: {t3 - t2}")

    print(f"Total time: {t3 - t1}")
    return penalties


def evaluate(points, bounding_box):
    labels = [p.label for p in points if p.label]
    penalties = evaluate_labels(labels, points, bounding_box)

    total_penalty = sum(penalties)

    return total_penalty


def local_search(points, bounding_box, iterations):
    labeled_points = [p for p in points if p.text]

    items = []
    items.extend([p.label for p in labeled_points])
    items.extend(points)
    items.extend(bounding_box.borders)

    idx = Index()
    for i, item in enumerate(items):
        item.index = i
        idx.insert(item.index, item.box)

    for i in range(iterations):
        for lp in labeled_points:
            best_candidate = None
            min_penalty = None
            for lc1 in lp.label_candidates:
                penalty = POSITION_WEIGHT * lc1.position

                # Check overlap with other labels and points
                intersecting_item_ids = idx.intersection(lc1.box)
                for item_id in intersecting_item_ids:
                    item = items[item_id]
                    if hasattr(item, "point") and lc1.point == item.point:
                        continue
                    penalty += item.overlap(lc1)

                if min_penalty is None or penalty < min_penalty:
                    min_penalty = penalty
                    best_candidate = lc1

            # Remove the old label from the index
            idx.delete(lp.label.index, lp.label.box)

            # Select the new label
            best_candidate.select()

            # Add the new label to the index and item list
            idx.insert(len(items), lp.label.box)
            items.append(lp.label)


class Label(object):
    def __init__(self, point, text, position, offset):
        self.index = None
        self.point = point
        self.text = text
        self.position = position
        self.penalty = position
        self.overlapping = []
        self.label_penalties = None

        width = AVG_CHAR_WIDTH * len(text)
        height = CHAR_HEIGHT
        angle_offset = offset / math.sqrt(2)

        if position == 0:
            self.minx = self.point.x + self.point.radius + offset
            self.maxx = self.point.x + self.point.radius + offset + width
            self.miny = self.point.y - 0.5 * height
            self.maxy = self.point.y + 0.5 * height
        elif position == 1:
            self.minx = self.point.x + self.point.radius + angle_offset
            self.maxx = self.point.x + self.point.radius + angle_offset + width
            self.miny = self.point.y + self.point.radius + angle_offset
            self.maxy = self.point.y + self.point.radius + angle_offset + height
        elif position == 2:
            self.minx = self.point.x - 0.5 * width
            self.maxx = self.point.x + 0.5 * width
            self.miny = self.point.y + self.point.radius + offset
            self.maxy = self.point.y + self.point.radius + offset + height
        elif position == 3:
            self.minx = self.point.x - self.point.radius - angle_offset - width
            self.maxx = self.point.x - self.point.radius - angle_offset
            self.miny = self.point.y + self.point.radius + angle_offset
            self.maxy = self.point.y + self.point.radius + angle_offset + height
        elif position == 4:
            self.minx = self.point.x - self.point.radius - offset - width
            self.maxx = self.point.x - self.point.radius - offset
            self.miny = self.point.y - 0.5 * height
            self.maxy = self.point.y + 0.5 * height
        elif position == 5:
            self.minx = self.point.x - self.point.radius - angle_offset - width
            self.maxx = self.point.x - self.point.radius - angle_offset
            self.miny = self.point.y - self.point.radius - angle_offset - height
            self.maxy = self.point.y - self.point.radius - angle_offset
        elif position == 6:
            self.minx = self.point.x - 0.5 * width
            self.maxx = self.point.x + 0.5 * width
            self.miny = self.point.y - self.point.radius - offset - height
            self.maxy = self.point.y - self.point.radius - offset
        elif position == 7:
            self.minx = self.point.x + self.point.radius + angle_offset
            self.maxx = self.point.x + self.point.radius + angle_offset + width
            self.miny = self.point.y - self.point.radius - angle_offset - height
            self.maxy = self.point.y - self.point.radius - angle_offset

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

    def overlap_point(self, p):
        return self.overlap(p)

    def area(self):
        return (self.maxx - self.minx) * (self.maxy - self.miny)

    def select(self):
        self.point.label_index = self.position

    @property
    def selected(self):
        return self.point.label_index == self.position

    @property
    def box(self):
        return self.minx, self.miny, self.maxx, self.maxy

    def determine_penalty(self, selected_label_candidates):
        penalty = self.penalty
        penalty += sum([self.label_penalties[i] for i in selected_label_candidates])
        return penalty


class LabelableObject(object):
    def __init__(self, text=None, label_offset=0):
        self.index = None
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


class Point(LabelableObject):
    def __init__(self, x, y, radius, text=None, label_offset=0):
        self.x = x
        self.y = y
        self.radius = radius

        LabelableObject.__init__(self, text, label_offset)

    @property
    def box(self):
        return (
            self.x - self.radius,
            self.y - self.radius,
            self.x + self.radius,
            self.y + self.radius,
        )

    def overlaps(self, label):
        dx = self.x - max(label.box[0], min(self.x, label.box[2]))
        dy = self.y - max(label.box[1], min(self.y, label.box[3]))
        return (dx * dx + dy * dy) < (self.radius * self.radius)

    def overlap(self, label, record=False):
        if self.overlaps(label):
            return POINT_PENALTY
        return 0

    def distance(self, other):
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class Ellipse(object):
    def __init__(
        self,
        x,
        y,
        semi_major_axis,
        semi_minor_axis,
        position_angle,
        text=None,
        label_offset=0,
    ):
        self.x = x
        self.y = y
        self.semi_major_axis = semi_major_axis
        self.semi_minor_axis = semi_minor_axis
        self.position_angle = position_angle

    def overlap(self, label, record=False):
        pass


class BoundingBox(tuple):
    def __new__(self, x1, y1, x2, y2):
        return tuple.__new__(BoundingBox, (x1, y1, x2, y2))

    @property
    def box(self):
        return self

    @property
    def borders(self):
        border_boxes = [
            (self[0] - 1, self[1] - 1, self[0], self[3] + 1),
            (self[2], self[1] - 1, self[2] + 1, self[3] + 1),
            (self[0] - 1, self[1] - 1, self[2] + 1, self[1]),
            (self[0] - 1, self[3], self[2] + 1, self[3] + 1),
        ]
        return [BoundingBoxBorder(b) for b in border_boxes]


class BoundingBoxBorder(object):
    def __init__(self, border_box):
        self.box = border_box

    def overlap(self, label, record=False):
        o = label.overlap(self)
        if o > 0:
            return BBOX_PENALTY
        return 0
