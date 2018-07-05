import unittest
from rtree.index import Index
import random
import timeit

from skymap.labeling.label_size import calculate_label_sizes


class Box(object):
    def __init__(self, index):
        self.index = index
        x = random.random()
        y = random.random()
        w = 0.02
        h = 0.5 * w
        self.box = x - w / 2, y - h / 2, x + w / 2, y + h / 2


class RTreeTest(unittest.TestCase):
    def Xtest_insertion(self):
        repeat = 10
        basen = 100
        boxes = [Box(i) for i in range(basen)]
        t = timeit.Timer(lambda: self.insert_boxes(boxes), setup=lambda: self.create_index_data([]))
        print t.timeit(number=repeat) / repeat

        n = 100000
        prior_boxes = [Box(i) for i in range(n)]
        boxes = [Box(i) for i in range(n, n + basen)]
        t = timeit.Timer(lambda: self.insert_boxes(boxes), setup=lambda: self.create_index_data(prior_boxes))
        print t.timeit(number=repeat) / repeat

    def Xtest_creation(self):
        repeat = 10
        basen = 100
        boxes = [Box(i) for i in range(basen)]
        t = timeit.Timer(lambda: self.create_index_data(boxes))
        t0 = t.timeit(number=repeat) / repeat
        print basen, t0
        for i in range(6):
            m = 2 ** (i + 1)
            n = m * basen
            boxes = [Box(i) for i in range(n)]
            t = timeit.Timer(lambda: self.create_index_data(boxes))
            t1 = t.timeit(number=repeat) / repeat
            print n, m, t1, t1 / t0

    def Xtest_stream(self):
        repeat = 10
        n = 10000

        boxes = []
        for i in range(n):
            boxes.append(Box(i))

        def box_generator():
            for b in boxes:
                yield (b.index, b.box, b.index)

        t = timeit.Timer(lambda: self.create_index_data(boxes))
        print t.timeit(number=repeat) / repeat

        t = timeit.Timer(lambda: self.create_index_stream(box_generator()))
        print t.timeit(number=repeat) / repeat

    def Xtest_query(self):
        repeat = 10
        boxes = [Box(i) for i in range(100)]
        self.create_index_data(boxes)
        test_boxes = random.sample(boxes, 10)

        t = timeit.Timer(lambda: self.query_index(test_boxes))
        print t.timeit(number=repeat) / repeat

        boxes = [Box(i) for i in range(100000)]
        self.create_index_data(boxes)
        test_boxes = random.sample(boxes, 10)

        t = timeit.Timer(lambda: self.query_index(test_boxes))
        print t.timeit(number=repeat) / repeat

    def insert_boxes(self, boxes):
        for b in boxes:
            self.idx.insert(b.index, b.box)

    def create_index_data(self, data):
        self.idx = Index()
        for d in data:
            self.idx.insert(d.index, d.box, d.index)

    def create_index_stream(self, generator):
        self.idx = Index(generator)

    def query_index(self, boxes):
        for b in boxes:
            overlapping_boxes = self.idx.intersection(b.box)


class LabelSizeTest(unittest.TestCase):
    def test_label_size(self):
        star_names = {
            1: "Albireo",
            2: "Alcor",
            3: u"Proxima Centauri \u03B1"
        }
        result = calculate_label_sizes(star_names, normalsize=11, fontsize="Large")
        self.assertIn(1, result.keys())
        self.assertIn(2, result.keys())
        self.assertIn(3, result.keys())

        self.assertAlmostEqual(result[1]["label_width"], 14.15)
        self.assertAlmostEqual(result[1]["label_height"], 3.75)