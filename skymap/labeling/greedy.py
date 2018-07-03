from operator import attrgetter
from skymap.labeling.common import evaluate_labels


class GreedyLabeler(object):
    def __init__(self, points, bounding_box):
        self.points = points
        self.bounding_box = bounding_box

        self.label_candidates = []
        for lp in self.points:
            self.label_candidates.extend(lp.label_candidates)

        evaluate_labels(self.label_candidates, self.points, self.bounding_box)

    def run(self):
        sorted_label_candidates = sorted(self.label_candidates, key=attrgetter("penalty"))
        for label_candidate in sorted_label_candidates:
            p = label_candidate.point
            if not p.label:
                label_candidate.select()

    def result(self):
        return [p.label_index for p in self.points if p.label_index is not None]


class AdvancedGreedyLabeler(GreedyLabeler):
    def __init__(self, points, bounding_box):
        GreedyLabeler.__init__(self, points, bounding_box)

    def run(self):
        unassigned_labeled_points = [p for p in self.points if (p.text and not p.label)]

        while unassigned_labeled_points:
            best_label = None
            for l in self.label_candidates:
                if l.point not in unassigned_labeled_points:
                    continue
                if not best_label or l.penalty < best_label.penalty:
                    best_label = l

            labeled_point = best_label.point
            unassigned_labeled_points.remove(labeled_point)
            best_label.select()

            for l in labeled_point.label_candidates:
                if l == best_label:
                    continue
                for ll in l.overlapping:
                    ll.penalty -= l.overlap(ll)
