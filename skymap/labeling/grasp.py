from skymap.labeling.greedy import AdvancedGreedyLabeler


class GraspLabeler(AdvancedGreedyLabeler):
    def __init__(self, labeled_points, points, bounding_box, iterations=5):
        AdvancedGreedyLabeler.__init__(self, labeled_points, points, bounding_box)
        self.iterations = iterations

    def run(self):
        AdvancedGreedyLabeler.run(self)

        for i in range(self.iterations):
            for lp in self.labeled_points:
                best_candidate = None
                for c1 in lp.candidates:
                    c1.penalty = 0
                    for lp2 in self.labeled_points:
                        if lp2 == lp:
                            continue
                        c2 = lp2.candidates[lp2.selected_candidate]
                        c1.penalty += c1.intersection_candidate(c2)

                    for p in self.points:
                        c1.penalty += c1.intersection_point(p)

                    if c1.intersection_candidate(self.bounding_box, False) < c1.area():
                        c1.penalty += 10000

                    if best_candidate is None or c1.penalty < best_candidate.penalty:
                        best_candidate = c1
                lp.select_candidate(best_candidate)
