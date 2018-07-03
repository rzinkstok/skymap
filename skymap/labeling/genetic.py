import random
import numpy
from deap import base, creator, tools, algorithms
from rtree.index import Index
import matplotlib.pyplot as plt

from skymap.labeling.common import evaluate_label


class GeneticLabeler(object):
    def __init__(self, points, bounding_box):
        self.points = points
        self.bounding_box = bounding_box
        self.labeled_points = [p for p in self.points if p.text]
        for i, lp in enumerate(self.labeled_points):
            lp.labeled_point_index = i

        self.build_index()

        # DEAP parameters
        self.ngenerations = 150
        self.nindividuals = 400
        self.mutation_prob = 0.4
        self.crossover_prob = 0.8

        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        self.toolbox = base.Toolbox()
        self.toolbox.register("attr_bool", random.randint, 0, 7)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual, self. toolbox.attr_bool, len(self.labeled_points))
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)

        self.toolbox.register("evaluate", self.evaluate_fitness)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutUniformInt, low=0, up=7, indpb=0.05)
        self.toolbox.register("select", tools.selTournament, tournsize=5)

    def evaluate_fitness(self, individual):
        penalty = 0
        for lpid, pos in enumerate(individual):
            self.labeled_points[lpid].label_candidates[pos].select()

        for lpid, lcid in enumerate(individual):
            lp = self.labeled_points[lpid]
            lc = lp.label_candidates[lcid]

            penalty += evaluate_label(lc, self.items, self.idx, selected_only=True)
        return -penalty,

    def build_index(self):
        label_candidates = []
        for p in self.points:
            label_candidates.extend(p.label_candidates)
        self.items = []
        self.items.extend(label_candidates)
        self.items.extend(self.points)
        self.items.extend(self.bounding_box.borders)

        self.idx = Index()
        for i, item in enumerate(self.items):
            item.index = i
            self.idx.insert(i, item.box)

    def run(self):
        pop = self.toolbox.population(n=self.nindividuals)
        hof = tools.HallOfFame(1)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", numpy.mean)
        stats.register("std", numpy.std)
        stats.register("min", numpy.min)
        stats.register("max", numpy.max)

        pop, log = algorithms.eaSimple(
            pop,
            self.toolbox,
            cxpb=self.crossover_prob,
            mutpb=self.mutation_prob,
            ngen=self.ngenerations,
            stats=stats,
            halloffame=hof,
            verbose=True
        )

        self.plot(log)

        for lp, i in zip(self.labeled_points, hof[0]):
            lp.label_candidates[i].select()

    def plot(self, logbook):
        gen = logbook.select("gen")
        fit_mins = logbook.select("min")
        fit_avgs = logbook.select("avg")
        fit_maxs = logbook.select("max")

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