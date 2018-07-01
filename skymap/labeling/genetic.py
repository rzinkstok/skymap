import random
from deap import base, creator, tools
from skymap.labeling.labeledpoint import BBOX_PENALTY


class GeneticLabeler(object):
    def __init__(self, labeled_points, points, bounding_box):
        self.labeled_points = labeled_points
        self.points = points
        self.bounding_box = bounding_box
        self.npoints = len(labeled_points)
        self.mutation_prob = 0.4
        self.crossover_prob = 0.4

        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        self.toolbox = base.Toolbox()
        self.toolbox.register("attr_bool", random.randint, 0, 7)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual,self. toolbox.attr_bool, self.npoints)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)

        self.toolbox.register("evaluate", self.evaluate_fitness)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutUniformInt, low=0, up=7, indpb=0.1)
        self.toolbox.register("select", tools.selTournament, tournsize=3)

    def evaluate_fitness(self, individual):
        penalty = 0

        for i, lp1 in enumerate(self.labeled_points):
            c1 = lp1.candidates[individual[i]]

            for j, lp2 in enumerate(self.labeled_points):
                c2 = lp2.candidates[individual[j]]

                if j > i:
                    penalty += 2 * c1.intersection_rectangle(c2)

                if i != j:
                    penalty += c1.intersection_point(lp2)

            for p in self.points:
                penalty += c1.intersection_point(p)

            if c1.intersection_rectangle(self.bounding_box, False) < c1.area():
                penalty += BBOX_PENALTY

        return -penalty,

    def run(self):
        pop = self.toolbox.population(n=300)

        fitnesses = list(map(self.toolbox.evaluate, pop))
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
            fitnesses = map(self.toolbox.evaluate, invalid_ind)
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

            print("  Min %s" % min(fits))
            print("  Max %s" % max(fits))
            print("  Avg %s" % mean)
            print("  Std %s" % std)
            print("  No change %s" % no_change_g)
            print("  Delta %s" % deltamax)

        bestind = pop[0]
        for ind in pop:
            f = ind.fitness.values[0]
            if f > bestind.fitness.values[0]:
                bestind = ind

        for lp, i in zip(self.labeled_points, bestind):
            lp.select_candidate(lp.candidates[i])
