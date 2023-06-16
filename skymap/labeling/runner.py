import time
import random
from PIL import Image, ImageDraw

from skymap.labeling.common import Point, BoundingBox, RandomLabeler, evaluate, POSITION_WEIGHT, POINT_RADIUS
from skymap.labeling.greedy import GreedyLabeler, AdvancedGreedyLabeler
from skymap.labeling.grasp import GraspLabeler
from skymap.labeling.genetic import CachedGeneticLabeler

from deap import creator, base


def draw(points, width, height):
    im = Image.new("RGB", (width, height), (255, 255, 255))
    d = ImageDraw.Draw(im)

    for p in points:
        x = p.x
        y = (height - p.y)
        r = p.radius

        if p.label is None:
            color = (200, 200, 200)
        else:
            color = "black"
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)

        if p.label:
            x1 = p.label.minx
            x2 = p.label.maxx
            y1 = (height - p.label.maxy)
            y2 = (height - p.label.miny)
            if p.label.penalty > POSITION_WEIGHT * p.label.position:
                color = (256, 0, 0)
            else:
                color = (200, 200, 200)
            d.rectangle((x1, y1, x2, y2), outline=color)

    im.show()


if __name__ == "__main__":
    print("Starting")
    random.seed(1)

    #creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    #creator.create("Individual", list, fitness=creator.FitnessMax)

    npoints = 1000
    nlabels = 200
    mapwidth = 2000
    mapheight = 2000
    bounding_box = BoundingBox(0, 0, mapwidth, mapheight)

    points = []
    for i in range(npoints):
        x = mapwidth * random.random()
        y = mapheight * random.random()
        if random.random() < float(nlabels) / npoints:
            text = f"Label for point {i}"
            p = Point(x, y, POINT_RADIUS, text, 0)
        else:
            p = Point(x, y, POINT_RADIUS)
        points.append(p)

    method = 4
    if method == 1:
        g = GreedyLabeler(points, bounding_box)
    elif method == 2:
        g = AdvancedGreedyLabeler(points, bounding_box)
    elif method == 3:
        g = GraspLabeler(points, bounding_box)
    # elif method == 4:
    #     g = GeneticLabeler(points, bounding_box)
    elif method == 4:
        g = CachedGeneticLabeler(points, bounding_box)
    else:
        g = RandomLabeler(points, bounding_box)

    t1 = time.perf_counter()

    g.run()
    t2 = time.perf_counter()
    print(f"Run time: {t2 - t1}")
    penalty = evaluate(g.points, g.bounding_box)
    print(f"Penalty: {penalty}")

    draw(points, mapwidth, mapheight)
