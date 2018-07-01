import time
import numpy as np
from PIL import Image, ImageDraw

from skymap.labeling.labeledpoint import Point, evaluate_labels
from skymap.labeling.greedy import GreedyLabeler, AdvancedGreedyLabeler
from skymap.labeling.grasp import GraspLabeler
from skymap.labeling.genetic import GeneticLabeler


class BoundingBox(tuple):
    def __new__(self, x1, y1, x2, y2):
        return tuple.__new__(BoundingBox, (x1, y1, x2, y2))

    @property
    def box(self):
        return self



def evaluate(points, bounding_box):
    labels = [p.label for p in points if p.label]
    penalties = evaluate_labels(labels, points, bounding_box, include_position=False)

    total_penalty = 0

    for p in points:
        if p.label is None:
            continue
        p.label.penalty = penalties[p.label.index]
        total_penalty += p.label.penalty

    return total_penalty


def draw(points, width, height):
    SCALE = 4
    im = Image.new("RGB", (SCALE * width, SCALE * height), (255, 255, 255))
    d = ImageDraw.Draw(im)

    for p in points:
        x = p.x * SCALE
        y = (height - p.y) * SCALE
        r = p.radius * SCALE

        if p.label is None:
            color = (200, 200, 200)
        else:
            color = "black"
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)

        if p.label:
            x1 = p.label.minx * SCALE
            x2 = p.label.maxx * SCALE
            y1 = (height - p.label.miny) * SCALE
            y2 = (height - p.label.maxy) * SCALE
            if p.label.penalty > 0:
                color = (256, 0, 0)
            else:
                color = (200, 200, 200)
            d.rectangle((x1, y1, x2, y2), outline=color)

    im.show()


if __name__ == "__main__":
    np.random.seed(1)

    npoints = 60
    mapwidth = 200
    mapheight = 200
    bounding_box = BoundingBox(0, 0, mapwidth, mapheight)

    points1 = np.zeros((npoints, 2), dtype=float)
    points1[:, 0] = mapwidth * np.random.random((npoints,))
    points1[:, 1] = mapheight * np.random.random((npoints,))

    points = [Point(p[0], p[1], 1, "Label for point {}".format(i), 0) for i, p in enumerate(points1)]

    npoints *= 1
    points2 = np.zeros((npoints, 2), dtype=float)
    points2[:, 0] = mapwidth * np.random.random((npoints,))
    points2[:, 1] = mapheight * np.random.random((npoints,))
    points.extend([Point(p[0], p[1], 1) for p in points2])

    method = 3
    if method == 1:
        g = GreedyLabeler(points, bounding_box)
    elif method == 2:
        g = AdvancedGreedyLabeler(points, bounding_box)
    elif method == 3:
        g = GraspLabeler(points, bounding_box)
    elif method == 4:
        g = GeneticLabeler(labeled_points, points, bounding_box)

    g.run()
    penalty = evaluate(g.points, g.bounding_box)
    print "Penalty:", penalty

    #draw(points, mapwidth, mapheight)