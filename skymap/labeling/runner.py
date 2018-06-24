import time
import numpy as np
from PIL import Image, ImageDraw

from skymap.labeling.labeledpoint import Point, LabeledPoint
from skymap.labeling.greedy import GreedyLabeler, AdvancedGreedyLabeler
from skymap.labeling.grasp import GraspLabeler


class BoundingBox(object):
    def __init__(self, x1, y1, x2, y2):
        self.minx = x1
        self.maxx = x2
        self.miny = y1
        self.maxy = y2


def evaluate(labeled_points):
    penalty = 0
    for i, lp1 in enumerate(labeled_points):
        c1 = lp1.candidates[lp1.selected_candidate]

        for lp2 in labeled_points[i+1:]:
            c2 = lp2.candidates[lp2.selected_candidate]
            penalty += c1.intersection_candidate(c2)

        for lp2 in labeled_points:
            if lp1 == lp2:
                continue
            penalty += c1.intersection_point(lp2)
    return penalty


def draw(labeled_points, points, width, height, selected=True):
    SCALE = 4
    im = Image.new("RGB", (SCALE * width, SCALE * height), (255, 255, 255))
    d = ImageDraw.Draw(im)

    for p in points:
        x = p.point[0] * SCALE
        y = (height - p.point[1]) * SCALE
        r = p.radius * SCALE
        d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 200, 200))

    for lp in labeled_points:
        x = lp.point[0] * SCALE
        y = (height - lp.point[1]) * SCALE
        r = lp.radius * SCALE
        d.ellipse([x - r, y - r, x + r, y + r], fill='black')

        for c in lp.candidates:
            if selected and c.position != lp.selected_candidate:
                continue
            x1 = c.minx * SCALE
            x2 = c.maxx * SCALE
            y1 = (height - c.miny) * SCALE
            y2 = (height - c.maxy) * SCALE
            d.rectangle((x1, y1, x2, y2), outline=(200,200,200))

    im.show()



np.random.seed(1)

npoints = 100
mapwidth = 200
mapheight = 200
bounding_box = BoundingBox(0, 0, mapwidth, mapheight)

points1 = np.zeros((npoints, 2), dtype=float)
points1[:, 0] = mapwidth * np.random.random((npoints,))
points1[:, 1] = mapheight * np.random.random((npoints,))

labeled_points = [LabeledPoint(p, 1, "Label {}".format(i), 8, 0) for i, p in enumerate(points1)]

npoints *= 3
points = np.zeros((npoints, 2), dtype=float)
points[:, 0] = mapwidth * np.random.random((npoints,))
points[:, 1] = mapheight * np.random.random((npoints,))
points = [Point(p, 1) for p in points]

t1 = time.clock()
method = 3
if method == 1:
    g = GreedyLabeler(labeled_points, points, bounding_box)
elif method == 2:
    g = AdvancedGreedyLabeler(labeled_points, points, bounding_box)
elif method == 3:
    g = GraspLabeler(labeled_points, points, bounding_box)

g.run()

print
print "Penalty:", evaluate(g.labeled_points)
print "Time: ", time.clock() - t1

draw(labeled_points, points, mapwidth, mapheight)