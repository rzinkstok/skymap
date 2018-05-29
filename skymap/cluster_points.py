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


"""
Forget the pairs, just add points that are close to another in 1 dimension to the set
Then create the intersection, and do a double loop over this set
"""


def distance(p1, p2):
    return np.linalg.norm(p1[:2] - p2[:2])


def cluster_points2(points, threshold):
    sorted_points_x = points[points[:, 0].argsort()]
    xdiffs = np.abs(np.diff(sorted_points_x[:,0]))
    xindices1 = np.where(xdiffs < threshold)[0]
    xindices2 = xindices1 + 1
    xindices = np.union1d(xindices1, xindices2)

    xset = sorted_points_x[xindices, :]

    sorted_points_y = xset[xset[:, 1].argsort()]
    ydiffs = np.abs(np.diff(sorted_points_y[:, 1]))

    yindices1 = np.where(ydiffs < threshold)[0]
    yindices2 = yindices1 + 1
    yindices = np.union1d(yindices1, yindices2)

    yset = sorted_points_y[yindices, :]

    #print yset[:, :2]
    print yset.shape
    dm = distance_matrix(yset, yset)
    mask = 2*threshold*np.tril(np.ones(dm.shape))
    dm1 = np.argwhere((mask+dm)<threshold)
    print dm1
    print dm1.shape[0]


def brute_cluster(points, threshold):
    #pairs = np.zeros((points.shape[0], 2), dtype=int)
    #pairs = np.zeros((points.shape[0],))
    pairs = []
    #npairs = 0
    for i in range(points.shape[0]):
        for j in range(i+1, points.shape[0]):
            p1 = points[i,:]
            p2 = points[j,:]
            d = distance(p1, p2)
            if d < threshold:
                pair = sorted((int(p1[2]), int(p2[2])))
                pairs.append("{} {}".format(*pair))
                #npairs += 1
    #return pairs[:npairs, :]
    return pairs


def strip_cluster(points, threshold):
    # pairs = np.zeros((points.shape[0], 2), dtype=int)
    # npairs = 0
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
                # pairs[npairs, :] = pair
                # npairs += 1
                pairs.append("{} {}".format(*pair))
    # return pairs[:npairs, :]
    return pairs


def cluster(points, threshold):
    # pairs = np.zeros((points.shape[0], 2), dtype=int)
    # npairs = 0
    pairs = set()

    if points.shape[0] <= 3:
        return brute_cluster(points, threshold)

    sorted_points = points[points[:, 0].argsort()]

    mid = sorted_points.shape[0]/2
    midx = 0.5*(sorted_points[mid-1, 0] + sorted_points[mid, 0])

    pairs1 = cluster(sorted_points[:mid, :], threshold)
    pairs = pairs.union(pairs1)
    # np1 = pairs1.shape[0]
    # pairs[npairs:npairs + np1, :] = pairs1
    # npairs += np1

    pairs2 = cluster(sorted_points[mid:, :], threshold)
    pairs = pairs.union(pairs2)
    # np2 = pairs2.shape[0]
    # pairs[npairs:npairs + np2, :] = pairs2
    # npairs += np2

    strip = np.zeros(sorted_points.shape)

    j = 0
    for i in range(sorted_points.shape[0]):
        p = points[i, :]
        if abs(p[0] - midx) < threshold:
            strip[j, :] = sorted_points[i, :]
            j += 1
    pairs3 = strip_cluster(strip[:j, :], threshold)
    pairs = pairs.union(pairs3)
    # np3 = pairs3.shape[0]
    # pairs[npairs:npairs + np3, :] = pairs3
    # npairs += np3

    return list(pairs)


def generate_random_points(npoints):
    points = np.zeros((npoints, 3))
    points[:, :2] = np.random.random((npoints, 2))
    points[:, 2] = np.arange(npoints)
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




if __name__ == "__main__":
    import time

    pseudo = True
    brute = False
    npoints = 100000
    threshold = 2*1.0/npoints
    print "Threshold:", threshold
    if pseudo:
        np.random.seed(1)

    t0 = time.clock()

    points = generate_random_points(npoints)
    #print points


    t1 = time.clock()
    print "Generation time: {} s".format(t1-t0)

    if brute:
        print brute_cluster(points, threshold)
    else:
        pairs = cluster(points, threshold)
        for p in pairs:
            pid1, pid2 = (int(x) for x in p.split())
            p1 = points[pid1, :]
            p2 = points[pid2, :]
            print pid1, pid2, distance(p1, p2)

    print
    #print closest_pair(points)


    print "Clustering time: {} s".format(time.clock()-t1)



