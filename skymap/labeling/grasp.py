from rtree.index import Index

from skymap.labeling.greedy import AdvancedGreedyLabeler
from skymap.labeling.common import POSITION_WEIGHT, local_search


class GraspLabeler(AdvancedGreedyLabeler):
    def __init__(self, points, bounding_box, iterations=5):
        AdvancedGreedyLabeler.__init__(self, points, bounding_box)
        self.iterations = iterations

    def run(self):
        AdvancedGreedyLabeler.run(self)
        local_search(self.points, self.bounding_box, self.iterations)
        # labeled_points = [p for p in self.points if p.text]
        #
        # items = []
        # items.extend([p.label for p in labeled_points])
        # items.extend(self.points)
        # items.extend(self.bounding_box.borders)
        #
        # idx = Index()
        # for i, item in enumerate(items):
        #     item.index = i
        #     idx.insert(item.index, item.box)
        #
        # for i in range(self.iterations):
        #     for lp in labeled_points:
        #         best_candidate = None
        #         min_penalty = None
        #         for lc1 in lp.label_candidates:
        #             penalty = POSITION_WEIGHT * lc1.position
        #
        #             # Check overlap with other labels and points
        #             intersecting_item_ids = idx.intersection(lc1.box)
        #             for item_id in intersecting_item_ids:
        #                 item = items[item_id]
        #                 if hasattr(item, "point") and lc1.point == item.point:
        #                     continue
        #                 penalty += item.overlap(lc1)
        #
        #             if min_penalty is None or penalty < min_penalty:
        #                 min_penalty = penalty
        #                 best_candidate = lc1
        #
        #         # Remove the old label from the index
        #         idx.delete(lp.label.index, lp.label.box)
        #
        #         # Select the new label
        #         best_candidate.select()
        #
        #         # Add the new label to the index and item list
        #         idx.insert(len(items), lp.label.box)
        #         items.append(lp.label)
