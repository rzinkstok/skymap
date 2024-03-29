import random
import numpy
from deap import base, creator, tools, algorithms
from rtree.index import Index
import matplotlib.pyplot as plt

from skymap.labeling.common import (
    evaluate_label,
    POSITION_WEIGHT,
    BoundingBoxBorder,
    Label,
    local_search,
    evaluate,
)


"""
Ideas:
* Local search
* conflict mutation (mutate only/preferentially genes that correspond to conflicting labels)
"""


def local_search_pop(population, toolbox, points, bounding_box):
    labeled_points = [p for p in points if p.text]
    offspring = [toolbox.clone(ind) for ind in population]
    sorted_fitness = sorted([x.fitness.values[0] for x in offspring], reverse=True)
    min_fitness = sorted_fitness[len(offspring) / 100]

    for individual in offspring:
        if individual.fitness.values[0] < min_fitness:
            continue

        # Select current individuals labels
        for p, lc in zip(labeled_points, individual):
            p.label_candidates[lc].select()

        local_search(points, bounding_box, 1)

        # Set new values for individual
        for pid, p in enumerate(labeled_points):
            individual[pid] = p.label_index

        del individual.fitness.values
    return offspring


def eaSimpleStop(
    population,
    toolbox,
    cxpb,
    mutpb,
    ngen,
    stopn=10,
    stats=None,
    halloffame=None,
    points=None,
    bounding_box=None,
    verbose=__debug__,
):
    """
    This algorithm reproduce the simplest evolutionary algorithm as
    presented in chapter 7 of [Back2000]_.

    Args:
        population: A list of individuals.
        toolbox: A :class:`~deap.base.Toolbox` that contains the evolution
                 operators.
        cxpb: The probability of mating two individuals.
        mutpb: The probability of mutating an individual.
        ngen: The number of generation.
        stopn: The number of no-change generations after which to stop running
        stats: A :class:`~deap.tools.Statistics` object that is updated
               inplace, optional.
        halloffame: A :class:`~deap.tools.HallOfFame` object that will
                    contain the best individuals, optional.
        verbose: Whether or not to log the statistics.

    Returns:
        The final population
        A class:`~deap.tools.Logbook` with the statistics of the
              evolution

    The algorithm takes in a population and evolves it in place using the
    :meth:`varAnd` method. It returns the optimized population and a
    :class:`~deap.tools.Logbook` with the statistics of the evolution. The
    logbook will contain the generation number, the number of evalutions for
    each generation and the statistics if a :class:`~deap.tools.Statistics` is
    given as argument. The *cxpb* and *mutpb* arguments are passed to the
    :func:`varAnd` function. The pseudocode goes as follow ::

        evaluate(population)
        for g in range(ngen):
            population = select(population, len(population))
            offspring = varAnd(population, toolbox, cxpb, mutpb)
            evaluate(offspring)
            population = offspring

    As stated in the pseudocode above, the algorithm goes as follow. First, it
    evaluates the individuals with an invalid fitness. Second, it enters the
    generational loop where the selection procedure is applied to entirely
    replace the parental population. The 1:1 replacement ratio of this
    algorithm **requires** the selection procedure to be stochastic and to
    select multiple times the same individual, for example,
    :func:`~deap.tools.selTournament` and :func:`~deap.tools.selRoulette`.
    Third, it applies the :func:`varAnd` function to produce the next
    generation population. Fourth, it evaluates the new individuals and
    compute the statistics on this population. Finally, when *ngen*
    generations are done, the algorithm returns a tuple with the final
    population and a :class:`~deap.tools.Logbook` of the evolution.

    .. note::

        Using a non-stochastic selection method will result in no selection as
        the operator selects *n* individuals from a pool of *n*.

    This function expects the :meth:`toolbox.mate`, :meth:`toolbox.mutate`,
    :meth:`toolbox.select` and :meth:`toolbox.evaluate` aliases to be
    registered in the toolbox.

    .. [Back2000] Back, Fogel and Michalewicz, "Evolutionary Computation 1 :
       Basic Algorithms and Operators", 2000.
    """
    logbook = tools.Logbook()
    logbook.header = ["gen", "nevals"] + (stats.fields if stats else [])

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    if halloffame is not None:
        halloffame.update(population)

    record = stats.compile(population) if stats else {}
    logbook.record(gen=0, nevals=len(invalid_ind), **record)
    if verbose:
        print(logbook.stream)

    # Begin the generational process
    for gen in range(1, ngen + 1):
        # Select the next generation individuals
        offspring = toolbox.select(population, len(population))

        # Vary the pool of individuals
        offspring = algorithms.varAnd(offspring, toolbox, cxpb, mutpb)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # if points and gen%10 == 0:
        #     offspring = local_search_pop(offspring, toolbox, points, bounding_box)
        #
        #     # Evaluate the individuals with an invalid fitness
        #     invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        #     fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        #     for ind, fit in zip(invalid_ind, fitnesses):
        #         ind.fitness.values = fit

        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(offspring)

        # Replace the current population by the offspring
        population[:] = offspring

        # Append the current generation statistics to the logbook
        record = stats.compile(population) if stats else {}
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)
        if verbose:
            print(logbook.stream)

        # Stopping rule
        last_gens = numpy.array(logbook.select("max")[-stopn:])
        maxdiff = numpy.max(numpy.abs(last_gens[1:] - last_gens[:-1]))
        if maxdiff < 1e-3:
            break

    return population, logbook


class BaseGeneticLabeler(object):
    def __init__(self, points, bounding_box):
        self.points = points
        self.bounding_box = bounding_box
        self.labeled_points = [p for p in self.points if p.text]
        for i, lp in enumerate(self.labeled_points):
            lp.labeled_point_index = i

        # DEAP parameters
        self.ngenerations = 300
        self.stopn = 10
        self.nindividuals = 400
        self.mutation_prob = 0.35
        self.crossover_prob = 0.9

        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        self.toolbox = base.Toolbox()
        self.toolbox.register("attr_bool", random.randint, 0, 7)
        self.toolbox.register(
            "individual",
            tools.initRepeat,
            creator.Individual,
            self.toolbox.attr_bool,
            len(self.labeled_points),
        )
        self.toolbox.register(
            "population", tools.initRepeat, list, self.toolbox.individual
        )

        self.toolbox.register("evaluate", self.evaluate_fitness)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutUniformInt, low=0, up=7, indpb=0.05)
        self.toolbox.register("select", tools.selTournament, tournsize=3)

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
            # stopn=self.stopn,
            stats=stats,
            halloffame=hof,
            # points=self.points,
            # bounding_box=self.bounding_box,
            verbose=True,
        )

        # self.plot(log)

        for lp, i in zip(self.labeled_points, hof[0]):
            lp.label_candidates[i].select()

        print("Penalty:", evaluate(self.points, self.bounding_box))
        local_search(self.points, self.bounding_box, 5)
        print("Penalty after local search: ", evaluate(self.points, self.bounding_box))

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


# class GeneticLabeler(BaseGeneticLabeler):
#     def __init__(self, points, bounding_box):
#         BaseGeneticLabeler.__init__(self, None, points, bounding_box)
#         self.build_index()
#
#     def build_index(self):
#         label_candidates = []
#         for p in self.points:
#             label_candidates.extend(p.label_candidates)
#         self.items = []
#         self.items.extend(label_candidates)
#         self.items.extend(self.points)
#         self.items.extend(self.bounding_box.border_config)
#
#         self.idx = Index()
#         for i, item in enumerate(self.items):
#             item.index = i
#             self.idx.insert(i, item.box)
#
#     def evaluate_fitness(self, individual):
#         penalty = 0
#         for lpid, pos in enumerate(individual):
#             self.labeled_points[lpid].label_candidates[pos].select()
#
#         for lpid, lcid in enumerate(individual):
#             lp = self.labeled_points[lpid]
#             lc = lp.label_candidates[lcid]
#
#             penalty += evaluate_label(lc, self.items, self.idx, selected_only=True)
#         return (-penalty,)


class CachedGeneticLabeler(BaseGeneticLabeler):
    def __init__(self, points, bounding_box):
        BaseGeneticLabeler.__init__(self, points, bounding_box)
        self.build_cache()

    def build_cache(self):
        label_candidates = []
        for p in self.points:
            label_candidates.extend(p.label_candidates)
        items = []
        items.extend(label_candidates)
        items.extend(self.points)
        items.extend(self.bounding_box.borders)

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

                if isinstance(item, Label):
                    if lc.point == item.point:
                        continue
                    else:
                        lc.label_penalties[item.index] = item.overlap(lc)
                        continue

                if isinstance(item, BoundingBoxBorder):
                    if bbox_counted:
                        continue
                    bbox_counted = True

                lc.penalty += item.overlap(lc)

    def evaluate_fitness(self, individual):
        lcs = [
            self.labeled_points[i].label_candidates[k] for i, k in enumerate(individual)
        ]
        indices = [lc.index for lc in lcs]
        penalty = 0

        for lc in lcs:
            penalty += lc.determine_penalty(indices)
        return (-penalty,)
