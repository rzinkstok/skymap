import unittest
import numpy as np

from skymap.stellar_motion import simplified_propagation, rigorous_propagation


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
