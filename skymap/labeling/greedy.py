from operator import attrgetter


class GreedyLabeler(object):
    def __init__(self, labeled_points, points, bounding_box):
        self.labeled_points = labeled_points
        self.points = points
        self.bounding_box = bounding_box

        self.candidates = []
        for lp in self.labeled_points:
            self.candidates.extend(lp.candidates)

        # Update penalties for overlap with other candidates
        for i, c1 in enumerate(self.candidates):
            for c2 in self.candidates[i+1:]:
                if c1.labeled_point == c2.labeled_point:
                    continue
                penalty = c1.intersection_candidate(c2)
                c1.penalty += penalty
                c2.penalty += penalty

        # Update penalties for overlap with other labeled points
        for l in self.labeled_points:
            for c in self.candidates:
                if c.labeled_point == l:
                    continue
                c.penalty += c.intersection_point(l)

        # Update penalties for overlap with other points
        for p in self.points:
            for c in self.candidates:
                c.penalty += c.intersection_point(p)

        # Update penalties for bounding box
        for c in self.candidates:
            if c.intersection_candidate(self.bounding_box, False) < c.area():
                c.penalty += 10000

    def run(self):
        sorted_candidates = sorted(self.candidates, key=attrgetter("penalty"))
        for s in sorted_candidates:
            lp = s.labeled_point
            if lp.selected_candidate < 0:
                lp.select_candidate(s)


class AdvancedGreedyLabeler(GreedyLabeler):
    def __init__(self, labeled_points, points, bounding_box):
        GreedyLabeler.__init__(self, labeled_points, points, bounding_box)

    def run(self):
        unassigned_labeled_points = [lp for lp in self.labeled_points]

        while unassigned_labeled_points:
            best_candidate = None
            for c in self.candidates:
                if c.labeled_point not in unassigned_labeled_points:
                    continue
                if not best_candidate or c.penalty < best_candidate.penalty:
                    best_candidate = c

            labeled_point = best_candidate.labeled_point
            unassigned_labeled_points.remove(labeled_point)
            labeled_point.select_candidate(best_candidate)
            for c in labeled_point.candidates:
                if c == best_candidate:
                    continue
                for cc in c.overlapping:
                    cc.penalty -= c.intersection_candidate(c)

