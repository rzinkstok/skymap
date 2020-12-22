import time
import random
from PIL import Image, ImageDraw

from skymap.labeling.common import Point, BoundingBox, evaluate, POSITION_WEIGHT
from skymap.labeling.greedy import GreedyLabeler, AdvancedGreedyLabeler
from skymap.labeling.grasp import GraspLabeler
from skymap.labeling.genetic import GeneticLabeler, CachedGeneticLabeler

from deap import creator, base


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
            if p.label.penalty > POSITION_WEIGHT * p.label.position:
                color = (256, 0, 0)
            else:
                color = (200, 200, 200)
            d.rectangle((x1, y1, x2, y2), outline=color)

    im.show()


if __name__ == "__main__":
    print("Starting")
    random.seed(1)

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    npoints = 1000
    nlabels = 200
    mapwidth = 500
    mapheight = 500
    bounding_box = BoundingBox(0, 0, mapwidth, mapheight)

    points = []
    for i in range(npoints):
        x = mapwidth * random.random()
        y = mapheight * random.random()
        if random.random() < float(nlabels) / npoints:
            text = f"Label for point {i}"
            p = Point(x, y, 1, text, 0)
        else:
            p = Point(x, y, 1)
        points.append(p)

    method = 5
    if method == 1:
        g = GreedyLabeler(points, bounding_box)
    elif method == 2:
        g = AdvancedGreedyLabeler(points, bounding_box)
    elif method == 3:
        g = GraspLabeler(points, bounding_box)
    elif method == 4:
        g = GeneticLabeler(points, bounding_box)
    elif method == 5:
        g = CachedGeneticLabeler(creator, points, bounding_box)

    t1 = time.clock()

    g.run()
    t2 = time.clock()
    print(f"Run time: {t2 - t1}")
    penalty = evaluate(g.points, g.bounding_box)
    print(f"Penalty: {penalty}")

    # draw(points, mapwidth, mapheight)
