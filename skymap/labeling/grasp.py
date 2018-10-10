from skymap.labeling.greedy import AdvancedGreedyLabeler
from skymap.labeling.common import local_search


class GraspLabeler(AdvancedGreedyLabeler):
    def __init__(self, points, bounding_box, iterations=5):
        AdvancedGreedyLabeler.__init__(self, points, bounding_box)
        self.iterations = iterations

    def run(self):
        AdvancedGreedyLabeler.run(self)
        local_search(self.points, self.bounding_box, self.iterations)
