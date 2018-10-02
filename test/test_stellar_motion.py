import unittest
import numpy as np

from skymap.stars.stellar_motion import simplified_propagation, rigorous_propagation


class TesttellarMotion(unittest.TestCase):
    def setUp(self):
        self.npoints = int(1e6)
        np.random.seed(1)

    def test_simple_propagation(self):
        positions = np.zeros((self.npoints, 2))
        positions[:, 0] = 360 * np.random.random(self.npoints)
        positions[:, 1] = 180 * np.random.random(self.npoints) - 90.0

        proper_motions = np.zeros((self.npoints, 2))
        proper_motions[:, 0] = 1000 * 60 * 60 * np.ones(self.npoints)
        proper_motions[:, 1] = 1000 * 60 * 60 * np.ones(self.npoints)

        res = simplified_propagation(positions, proper_motions, "J1991.25", "J2000.0")

    def test_rigorous_propagation(self):
        positions = np.zeros((self.npoints, 3))
        positions[:, 0] = 360 * np.random.random(self.npoints)
        positions[:, 1] = 180 * np.random.random(self.npoints) - 90.0
        positions[:, 2] = 700 * np.random.random(self.npoints) + 0.1

        proper_motions = np.zeros((self.npoints, 3))
        proper_motions[:, 0] = 1000 * 60 * 60 * np.ones(self.npoints)
        proper_motions[:, 1] = 1000 * 60 * 60 * np.ones(self.npoints)
        proper_motions[:, 1] = 20 * np.ones(self.npoints)

        res = rigorous_propagation(positions, proper_motions, "J1991.25", "J2000.0")

    def test_barnards_star(self):
        position = np.array((269.45402305, 4.66828815, 549.01)).reshape((1,3))
        motion = np.array((-797.84, 10326.93, -110.6)).reshape(1,3)
        rigorous_propagation(position, motion, "J1991.25", "J2100.0")
        simplified_propagation(position, motion, "J1991.25", "J2000.0")