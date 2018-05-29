"""
Idea:
- for coord in (RA, DE):
    - initialize empty set
    - sort all points by coord
    - find all point pairs that lie within a certain threshold in coord, add to set
- intersect RAset and DEset

"""

from operator import attrgetter
import numpy as np
import math
from scipy.spatial import distance_matrix
from skymap.geometry import rotation_matrix, sky2cartesian, cartesian2sky


"""
Forget the pairs, just add points that are close to another in 1 dimension to the set
Then create the intersection, and do a double loop over this set
"""


def distance(p1, p2):
    return np.linalg.norm(p1[:2] - p2[:2])


def brute_cluster(points, threshold):
    pairs = []
    for i in range(points.shape[0]):
        for j in range(i+1, points.shape[0]):
            p1 = points[i,:]
            p2 = points[j,:]
            d = distance(p1, p2)
            if d < threshold:
                pair = sorted((int(p1[2]), int(p2[2])))
                pairs.append("{} {}".format(*pair))
    return pairs


def strip_cluster(points, threshold):
    pairs = []
    sorted_points = points[points[:, 1].argsort()]
    for i in range(sorted_points.shape[0]):
        for j in range(i+1, i+7):
            try:
                p1 = sorted_points[i, :]
                p2 = sorted_points[j, :]
            except IndexError:
                break
            d = distance(p1, p2)
            if d < threshold:
                pair = sorted((int(p1[2]), int(p2[2])))
                pairs.append("{} {}".format(*pair))
    return pairs


def cluster(points, threshold):
    pairs = set()

    if points.shape[0] <= 3:
        return brute_cluster(points, threshold)

    sorted_points = points[points[:, 0].argsort()]
    mid = sorted_points.shape[0]/2
    midx = 0.5*(sorted_points[mid-1, 0] + sorted_points[mid, 0])

    pairs1 = cluster(sorted_points[:mid, :], threshold)
    pairs = pairs.union(pairs1)

    pairs2 = cluster(sorted_points[mid:, :], threshold)
    pairs = pairs.union(pairs2)

    strip = np.zeros(sorted_points.shape)
    j = 0
    for i in range(sorted_points.shape[0]):
        p = points[i, :]
        if abs(p[0] - midx) < threshold:
            strip[j, :] = sorted_points[i, :]
            j += 1
    pairs3 = strip_cluster(strip[:j, :], threshold)
    pairs = pairs.union(pairs3)

    return list(pairs)


def generate_random_points(npoints):
    points = np.zeros((npoints, 2))
    points[:, 0] = 26 * np.random.random((npoints,)) + 83
    points[:, 1] = 12 * np.random.random((npoints,)) -6 #+ 40
    return points


def brute_closest_pair(points):
    mind = None
    pair = None
    for i in range(points.shape[0]):
        for j in range(i+1, points.shape[0]):
            p1 = points[i, :]
            p2 = points[j, :]
            d = distance(p1, p2)
            if mind is None or d < mind:
                mind = d
                pair = p1, p2
    return pair, d


def strip_closest_pair(points, upper_bound):
    mind = upper_bound
    pair = None
    sorted_points = points[points[:, 1].argsort()]
    for i in range(sorted_points.shape[0]):
        for j in range(i+1, i+7):
            try:
                p1 = sorted_points[i, :]
                p2 = sorted_points[j, :]
            except IndexError:
                break
            d = distance(p1, p2)
            if d < mind:
                mind = d
                pair = p1, p2

    return pair, mind


def closest_pair(points):
    if points.shape[0] <= 3:
        return brute_closest_pair(points)

    sorted_points = points[points[:, 0].argsort()]

    mid = sorted_points.shape[0]/2
    midx = 0.5*(sorted_points[mid-1, 0] + sorted_points[mid, 0])

    pair1, d1 = closest_pair(sorted_points[:mid, :])
    pair2, d2 = closest_pair(sorted_points[mid:, :])

    if d1 < d2:
        minpair, mind = pair1, d1
    else:
        minpair, mind = pair2, d2

    strip = np.zeros(sorted_points.shape)

    j = 0
    for i in range(sorted_points.shape[0]):
        p = points[i,:]
        if abs(p[0] - midx) < mind:
            strip[j, :] = sorted_points[i, :]
            j += 1
    pair, d = strip_closest_pair(strip[:j, :], mind)

    if d < mind:
        return pair, d
    return minpair, mind


def rotate_points(points):
    # Determine center of points
    mins = np.min(points[:, :2], axis=0)
    maxs = np.max(points[:, :2], axis=0)
    center_ra = 0.5 * (mins[0] + maxs[0])
    center_de = 0.5 * (mins[1] + maxs[1])
    center = sky2cartesian(np.array([[center_ra, center_de],]))[0,:]

    # Setup rotation matrix for rotation from center to (ra, de) = (0, 0)
    target = np.array((1, 0, 0))
    axis = np.cross(center, target)
    angle = np.arccos(np.dot(center, target))
    m = rotation_matrix(axis, angle)

    # Transform points to cartesian, rotate, and transform back
    cpoints = sky2cartesian(points)
    rpoints = np.dot(m, cpoints.T).T
    result = np.zeros((points.shape[0], 3))
    result[:, :2] = cartesian2sky(rpoints)
    result[:, 2] = points[:, 2]

    # Check new center
    # mins = np.min(result[:, :2], axis=0)
    # maxs = np.max(result[:, :2], axis=0)
    # center_ra = 0.5 * (mins[0] + maxs[0])
    # center_de = 0.5 * (mins[1] + maxs[1])

    return result


def cluster_wrapper(points, threshold, brute=False):
    cpoints = np.zeros((npoints, 3))
    cpoints[:, :2] = points
    cpoints[:, 2] = np.arange(npoints)
    rpoints = rotate_points(cpoints)
    if brute:
        pairs = brute_cluster(points, threshold)
    else:
        pairs = cluster(rpoints, threshold)
    return pairs


if __name__ == "__main__":
    import time

    pseudo = True
    brute = False
    npoints = int(1e5)
    threshold = 0.0001*360*180*1.0/npoints
    print "Threshold:", threshold
    if pseudo:
        np.random.seed(1)

    t0 = time.clock()

    points = generate_random_points(npoints)

    t1 = time.clock()
    print "Generation time: {} s".format(t1-t0)


    pairs = cluster_wrapper(points, threshold, brute=brute)

    print
    print "Pairs:"
    print "--------------"
    for p in pairs:
        pid1, pid2 = (int(x) for x in p.split())
        p1 = points[pid1, :]
        p2 = points[pid2, :]
        print pid1, pid2, distance(p1, p2)
    print "--------------"
    print "Clustering time: {} s".format(time.clock()-t1)



