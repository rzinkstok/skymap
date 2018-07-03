import random
from deap import base, creator, tools
from rtree.index import Index

from skymap.labeling.common import BBOX_PENALTY, POSITION_WEIGHT, evaluate_label


class GeneticLabeler(object):
    def __init__(self, points, bounding_box):
        self.points = points
        self.bounding_box = bounding_box
        self.labeled_points = [p for p in self.points if p.text]
        for i, lp in enumerate(self.labeled_points):
            lp.labeled_point_index = i

        self.build_index()

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

    def evaluate_fitness_old(self, individual):
        penalty = 0

        for i, lp1 in enumerate(self.labeled_points):
            c1 = lp1.label_candidates[individual[i]]
            penalty += POSITION_WEIGHT * c1.position
            for j, lp2 in enumerate(self.labeled_points):
                if j <= i:
                    continue
                c2 = lp2.label_candidates[individual[j]]
                penalty += 2 * c1.overlap(c2, False)

            for j, p in enumerate(self.points):
                penalty += p.overlap(c1)

            if c1.overlap(self.bounding_box, False) < c1.area():
                penalty += BBOX_PENALTY

        return -penalty,

    def evaluate_fitness(self, individual):
        penalty = 0
        for lpid, pos in enumerate(individual):
            self.labeled_points[lpid].label_candidates[pos].select()

        for lpid, lcid in enumerate(individual):
            lp = self.labeled_points[lpid]
            lc = lp.label_candidates[lcid]

            penalty += evaluate_label(lc, self.items, self.idx, selected_only=True)
        return -penalty,

    def evaluate_fitness_population(self, pop):
        penalties = [0 for ind in pop]

        for i, ind in enumerate(pop):
            for lpid, pos in enumerate(ind):
                self.labeled_points[lpid].label_candidates[pos].select()

            for lpid, lcid in enumerate(ind):
                lp = self.labeled_points[lpid]
                lc = lp.label_candidates[lcid]

                penalties[i] += evaluate_label(lc, self.items, self.idx, selected_only=True)

        return [(-penalty,) for penalty in penalties]

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
        pop = self.toolbox.population(n=400)

        old = True

        if old:
            fitnesses = list(map(self.toolbox.evaluate, pop))
        else:
            fitnesses = self.evaluate_fitness_population(pop)

        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit

        g = 0
        no_change_g = 0
        prev_max = None

        # Begin the evolution
        while g < 1000 and no_change_g < 15 and prev_max < 0.0:
            # A new generation
            g = g + 1
            print("-- Generation %i --" % g)

            # Select the next generation individuals
            offspring = self.toolbox.select(pop, len(pop))

            # Clone the selected individuals
            offspring = list(map(self.toolbox.clone, offspring))

            # Apply crossover and mutation on the offspring
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < self.crossover_prob:
                    self.toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            for mutant in offspring:
                if random.random() < self.mutation_prob:
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]

            if old:
                fitnesses = map(self.toolbox.evaluate, invalid_ind)
            else:
                fitnesses = self.evaluate_fitness_population(invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            pop[:] = offspring

            # Gather all the fitnesses in one list and print the stats
            fits = [ind.fitness.values[0] for ind in pop]

            length = len(pop)
            mean = sum(fits) / length
            sum2 = sum(x * x for x in fits)
            std = abs(sum2 / length - mean ** 2) ** 0.5

            m = max(fits)
            if prev_max is not None:
                deltamax = m - prev_max
            else:
                deltamax = None

            if deltamax is None or abs(deltamax) > 0:
                prev_max = m
                no_change_g = 0
            else:
                no_change_g += 1

            #print("  Min %s" % min(fits))
            print("   Max %s" % max(fits))
            #print("  Avg %s" % mean)
            #print("  Std %s" % std)
            #print("  No change %s" % no_change_g)
            #print("  Delta %s" % deltamax)

        bestind = pop[0]
        for ind in pop:
            f = ind.fitness.values[0]
            if f > bestind.fitness.values[0]:
                bestind = ind

        for lp, i in zip(self.labeled_points, bestind):
            lp.label_candidates[i].select()
