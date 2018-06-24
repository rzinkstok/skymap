import numpy as np
from skymap.geometry import rotation_matrix, sky2cartesian, cartesian2sky, distance


# Brute force clustering
def brute_cluster(points, threshold):
    """Naive method for clustering points that are closer than the given threshold.

    Args:
        points (numpy.ndarray): a (Nx2) array containing the (x, y) coordinates of the input points
        threshold (float): the distance between points below which they are considered a pair

    Returns:
        numpy.ndarray: a (Mx2) array containing the pairs of indices for all paired points
    """
    brute_pairs = []
    for i in range(points.shape[0]):
        for j in range(i+1, points.shape[0]):
            p1 = points[i, :]
            p2 = points[j, :]
            d = distance(p1, p2)
            if d < threshold:
                pair = sorted((int(p1[2]), int(p2[2])))
                brute_pairs.append("{} {}".format(*pair))
    return brute_pairs


def strip_cluster(points, threshold):
    """Function that handles the area connecting both halves of the plane in the divide and conquer approach.

    Args:
        points (numpy.ndarray): a (Px2) array containing all points in the strip connecting both halves of the plane
        threshold (float): the distance between points below which they are considered a pair

    Returns:
        numpy.ndarray: a (Qx2) array containing the pairs of indices for all paired points
    """
    strip_pairs = []
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
                strip_pairs.append("{} {}".format(*pair))
    return strip_pairs


def cluster(points, threshold):
    """A divide and conquer recursive strategy for point clustering.

    Adapted from the similar strategy to find the closest pair in a set of points.

    Args:
        points (numpy.ndarray): a (Nx2) array containing the (x, y) coordinates of the input points
        threshold (float): the distance between points below which they are considered a pair

    Returns:
        numpy.ndarray: a (Mx2) array containing the pairs of indices for all paired points
    """
    all_pairs = set()

    if points.shape[0] <= 3:
        return brute_cluster(points, threshold)

    sorted_points = points[points[:, 0].argsort()]
    mid = sorted_points.shape[0]/2
    midx = 0.5*(sorted_points[mid-1, 0] + sorted_points[mid, 0])

    pairs1 = cluster(sorted_points[:mid, :], threshold)
    all_pairs = all_pairs.union(pairs1)

    pairs2 = cluster(sorted_points[mid:, :], threshold)
    all_pairs = all_pairs.union(pairs2)

    strip = np.zeros(sorted_points.shape)
    j = 0
    for i in range(sorted_points.shape[0]):
        p = points[i, :]
        if abs(p[0] - midx) < threshold:
            strip[j, :] = sorted_points[i, :]
            j += 1
    pairs3 = strip_cluster(strip[:j, :], threshold)
    all_pairs = all_pairs.union(pairs3)

    return list(all_pairs)


def generate_random_points(npoints):
    points = np.zeros((npoints, 2))
    points[:, 0] = 26 * np.random.random((npoints,)) + 83
    points[:, 1] = 12 * np.random.random((npoints,)) - 6
    # scs = SkyCoordDeg(points[:, 0], points[:, 1])
    return points


def rotate_points(points):
    """
    Rotates the given point set on the sphere such that the center of the set is positioned at 0 latitude and longitude.

    Args:
        points: the point set

    Returns:
        the rotated point set
    """
    # Determine center of points
    mins = np.min(points[:, :2], axis=0)
    maxs = np.max(points[:, :2], axis=0)
    center_ra = 0.5 * (mins[0] + maxs[0])
    center_de = 0.5 * (mins[1] + maxs[1])
    center = sky2cartesian(np.array([[center_ra, center_de], ]))[0, :]

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

    return result


def cluster_wrapper(points, threshold, brute=False):
    npoints = points.shape[0]
    cpoints = np.zeros((npoints, 3))
    cpoints[:, :2] = points
    cpoints[:, 2] = np.arange(npoints)
    rpoints = rotate_points(cpoints)
    if brute:
        point_pairs = brute_cluster(points, threshold)
    else:
        point_pairs = cluster(rpoints, threshold)
    return point_pairs


if __name__ == "__main__":
    import time

    use_pseudo = True
    use_brute = False
    number_of_points = int(1e5)
    cluster_threshold = 0.0001*360*180*1.0/number_of_points
    print "Threshold:", cluster_threshold
    if use_pseudo:
        np.random.seed(1)

    t0 = time.clock()

    input_points = generate_random_points(number_of_points)

    t1 = time.clock()
    print "Generation time: {} s".format(t1-t0)

    pairs = cluster_wrapper(input_points, cluster_threshold, brute=use_brute)

    print
    print "Pairs:"
    print "--------------"
    for pp in pairs:
        pid1, pid2 = (int(x) for x in pp.split())
        pp1 = input_points[pid1, :]
        pp2 = input_points[pid2, :]
        print pid1, pid2, distance(pp1, pp2)
    print "--------------"
    print "Clustering time: {} s".format(time.clock()-t1)
