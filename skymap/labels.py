import math
import sys

from skymap.metapost import MetaPostFigure
from skymap.geometry import Rectangle, Point
from skymap.database import SkyMapDatabase
from skymap.stars import Star

DEFAULT_DISTANCE1 = 1.0583403888888888  # 3 postscript points
DEFAULT_DISTANCE2 = 0.7408298055555554  # Almost


def build_label_database():
    db = SkyMapDatabase()
    db.drop_table("labels")

    # Create table
    db.commit_query("""CREATE TABLE labels (
                        label_id INT PRIMARY KEY,
                        label_text TEXT,
                        fontsize TEXT,
                        width REAL,
                        height REAL)""")

    stars = [Star(r) for r in db.query("""SELECT * FROM stars WHERE proper_name is not null""")]
    p = Point(0, 0)
    i = 0
    nstars = len(stars)
    for n, s in enumerate(stars):
        sys.stdout.write("\r{}%".format(int(round(100 * n / float(nstars)))))
        sys.stdout.flush()

        if not s.proper_name.strip() and not s.identifier_string.strip():
            continue

        if s.proper_name:
            i += 1
            if db.query_one("""SELECT * FROM labels WHERE label_text="{}" AND fontsize="{}" """.format(s.proper_name, "tiny")) is None:
                l = Label(p, s.proper_name, fontsize="tiny", render_size=True)
                size = l.size
                db.commit_query("""INSERT INTO labels VALUES ({}, "{}", "{}", {}, {})""".format(i, s.proper_name, "tiny", size[0], size[1]))

        if s.identifier_string:
            i += 1
            if db.query_one("""SELECT * FROM labels WHERE label_text="{}" AND fontsize="{}" """.format(s.identifier_string, "tiny")) is None:
                l = Label(p, s.identifier_string.strip(), fontsize="tiny", render_size=True)
                size = l.size
                db.commit_query("""INSERT INTO labels VALUES ({}, "{}", "{}", {}, {})""".format(i, s.identifier_string, "tiny", size[0], size[1]))

    db.close()


def get_label_size(text, fontsize):
    db = SkyMapDatabase()
    res = db.query_one("""SELECT * FROM labels WHERE label_text="{}" AND fontsize="{}" """.format(text, fontsize))
    db.close()
    if res is None:
        return None
    return res['width'], res['height']


class Label(object):
    def __init__(self, point, text, fontsize="large", extra_distance=0, margin=1.0, object_for=None, render_size=False):
        self.point = point
        self.text = text
        self.fontsize = fontsize
        self.margin = margin
        self._optimal_position = None
        self.object_for = object_for
        self.extra_distance = extra_distance

        if render_size:
            label = MetaPostFigure("label")
            label.draw_text(point, text, 'rt', fontsize)
            self.size = label.bounding_box_size()
        else:
            self.size = get_label_size(self.text, self.fontsize)

        self.positions = ["top", "urt", "rt", "lrt", "bot", "llft", "lft", "ulft"]
        d1 = extra_distance
        d2 = math.sqrt(0.5*extra_distance**2) - 0.2
        self.anchor_vectors = [
            Point(0, d1),
            Point(d2, d2),
            Point(d1, 0),
            Point(d2, -d2),
            Point(0, -d1),
            Point(-d2, -d2),
            Point(-d1, 0),
            Point(-d2, d2)
        ]
        d1 = DEFAULT_DISTANCE1 + extra_distance
        d2 = DEFAULT_DISTANCE2 + math.sqrt(0.5*extra_distance**2)
        self.bb_vectors = [
            Point(-0.5 * self.size[0], d1),
            Point(d2, d2),
            Point(d1, -0.5 * self.size[1]),
            Point(d2, -d2 - self.size[1]),
            Point(-0.5 * self.size[0], -d1 - self.size[1]),
            Point(-self.size[0] - d2, -d2 - self.size[1]),
            Point(-self.size[0] - d1, -0.5 * self.size[1]),
            Point(-self.size[0] - d2, d2)
        ]
        self.penalties = {}

    def bounding_box_pos(self, pos):
        index = self.positions.index(pos)
        p1 = self.point + self.bb_vectors[index]
        return Rectangle(p1, p1+Point(self.size))

    def margin_box_pos(self, pos):
        bb = self.bounding_box_pos(pos)
        return Rectangle(Point(bb.p1.x - self.margin, bb.p1.y - self.margin), Point(bb.p2.x + self.margin, bb.p2.y + self.margin))

    def anchor_point(self, pos):
        index = self.positions.index(pos)
        return self.point + self.anchor_vectors[index]

    def calculate_penalties(self, objects):
        self.penalties = {}
        self.touching_objects = {}
        for pos in self.positions:
            penalty = 0
            bb = self.bounding_box_pos(pos)
            mb = self.margin_box_pos(pos)
            # print
            # print pos, bb
            self.touching_objects[pos] = []
            for o in objects:
                # print o
                if o == self.object_for:
                    continue
                bb_overlap = bb.overlap(o)
                mb_overlap = mb.overlap(o)
                if mb_overlap > 0:
                    self.touching_objects[pos].append(o)
                penalty += 0.5*(bb_overlap + mb_overlap)
            self.penalties[pos] = penalty
            # print "Penalty:", penalty

    @property
    def optimal_position(self):
        if self._optimal_position is not None:
            return self._optimal_position

        # print self.penalties
        min_penalty = max(self.penalties.values())
        min_pos = []
        for pos, penalty in self.penalties.items():
            if penalty < min_penalty:
                min_penalty = penalty
                min_pos = [pos]
            elif penalty == min_penalty:
                min_pos.append(pos)

        # print self.text, min_pos
        for pos in ['rt', 'bot', 'top', 'lft', 'urt', 'lrt', 'ulft', 'llft']:
            if pos in min_pos:
                self._optimal_position = pos
                return self._optimal_position
        return None

    @property
    def bounding_box(self):
        return self.bounding_box_pos(self.optimal_position)

    @property
    def margin_box(self):
        bb = self.bounding_box
        return Rectangle(Point(bb.p1.x - self.margin, bb.p1.y - self.margin), Point(bb.p2.x + self.margin, bb.p2.y + self.margin))

    def draw(self, figure):
        pos = self.optimal_position
        figure.draw_text(self.anchor_point(pos), self.text, self.optimal_position, self.fontsize)
        #figure.draw_rectangle(self.bounding_box)


class LabelManager(object):
    def __init__(self):
        self.objects = []
        self.labels = []

    def add_label(self, point, text, fontsize, extra_distance=0, object_for=None):
        self.labels.append(Label(point, text, fontsize, extra_distance=extra_distance, object_for=object_for))

    def add_object(self, object):
        self.objects.append(object)

    def draw_labels(self, figure):
        nlabels = len(self.labels)
        for i, l in enumerate(self.labels):
            sys.stdout.write("\r{}%".format(int(round(100*i/float(nlabels)))))
            sys.stdout.flush()
            #print l.text
            l.calculate_penalties(self.objects)
            # if l.text == "28$\\rho$\\textsuperscript{1}":
            #     print l.text
            #     print l.object_for
            #     for pos in l.positions:
            #         print
            #         print pos
            #         print "Penalty:", l.penalties[pos]
            #         for o in l.touching_objects[pos]:
            #             print o
            l.draw(figure)
            self.objects.append(l.bounding_box)
        print "\n"


if __name__ == "__main__":
    build_label_database()