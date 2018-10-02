import time
import random

from skymap.labeling.common import Point, BoundingBox


import numpy
from deap import base, tools, algorithms, creator
from rtree.index import Index
import matplotlib.pyplot as plt
from scoop import futures

from skymap.labeling.common import POSITION_WEIGHT, BoundingBoxBorder, Label, local_search, evaluate

npoints = 1000
nlabels = 200
mapwidth = 500
mapheight = 500

# DEAP parameters
ngenerations = 300
nindividuals = 400
mutation_prob = 0.35
crossover_prob = 0.9

random.seed(1)

bounding_box = BoundingBox(0, 0, mapwidth, mapheight)

points = []
for i in range(npoints):
    x = mapwidth * random.random()
    y = mapheight * random.random()
    if random.random() < float(nlabels)/npoints:
        text = "Label for point {}".format(i)
        p = Point(x, y, 1, text, 0)
    else:
        p = Point(x, y, 1)
    points.append(p)

labeled_points = [p for p in points if p.text]
for i, lp in enumerate(labeled_points):
    lp.labeled_point_index = i


def evaluate_fitness(individual):
    lcs = [labeled_points[i].label_candidates[k] for i, k in enumerate(individual)]
    indices = [lc.index for lc in lcs]
    penalty = 0

    for lc in lcs:
        penalty += lc.determine_penalty(indices)
    return -penalty,


creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
toolbox.register("attr_bool", random.randint, 0, 7)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_bool, len(labeled_points))
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutUniformInt, low=0, up=7, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("map", futures.map)
toolbox.register("evaluate", evaluate_fitness)


def build_cache():
    label_candidates = []
    for p in points:
        label_candidates.extend(p.label_candidates)
    items = []
    items.extend(label_candidates)
    items.extend(points)
    items.extend(bounding_box.borders)

    idx = Index()
    for i, item in enumerate(items):
        item.index = i
        idx.insert(i, item.box)

    for lc in label_candidates:
        lc.penalty = POSITION_WEIGHT * lc.position
        lc.label_penalties = [0 for i in range(len(label_candidates))]
        intersecting_item_ids = idx.intersection(lc.box)
        bbox_counted = False

        for item_id in intersecting_item_ids:
            item = items[item_id]

            if item == lc or item == lc.point:
                continue

            if type(item) == Label:
                if lc.point == item.point:
                    continue
                else:
                    lc.label_penalties[item.index] = item.overlap(lc)
                    continue

            if type(item) == BoundingBoxBorder:
                if bbox_counted:
                    continue
                bbox_counted = True

            lc.penalty += item.overlap(lc)
build_cache()


def main():
    # Run
    pop = toolbox.population(n=nindividuals)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)

    pop, log = algorithms.eaSimple(
        pop,
        toolbox,
        cxpb=crossover_prob,
        mutpb=mutation_prob,
        ngen=ngenerations,
        stats=stats,
        halloffame=hof,
        verbose=True
    )

    return pop, log, hof


if __name__ == "__main__":
    t1 = time.clock()
    pop, log, hof = main()

    if False:
        gen = log.select("gen")
        fit_mins = log.select("min")
        fit_avgs = log.select("avg")
        fit_maxs = log.select("max")

        fig, ax1 = plt.subplots()
        line1 = ax1.plot(gen, fit_mins, "b-", label="Minimum Fitness")
        line2 = ax1.plot(gen, fit_avgs, "r-", label="Average Fitness")
        line3 = ax1.plot(gen, fit_maxs, "g-", label="Maximum Fitness")
        ax1.set_xlabel("Generation")
        ax1.set_ylabel("Fitness", color="b")
        for tl in ax1.get_yticklabels():
            tl.set_color("b")

        lns = line1 + line2 + line3
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc="center right")

        plt.show()

    for lp, i in zip(labeled_points, hof[0]):
        lp.label_candidates[i].select()

    print "Penalty:", evaluate(points, bounding_box)
    local_search(points, bounding_box, 5)
    print "Penalty after local search: ", evaluate(points, bounding_box)

    t2 = time.clock()
    print "Run time:", t2 - t1

    #draw(points, mapwidth, mapheight)