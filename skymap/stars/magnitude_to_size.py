"""The magnitude to size relation"""


def magnitude_to_size(m, start=0, stop=10, mm_per_degree=1):
    # Based on the Uranometria 2000.0 scale (1.85 cm per degree of declination
    x = 10.0*(m-start)/(stop-start)
    s = -1.86483053 + (4.35447935 + 1.86483053) / pow((1 + pow((x/19.06110112), 1.30821934)), 3.25679589)
    return mm_per_degree*s/18.5


if __name__=="__main__":
    """Fit the magnitude to size data to an asymmetric sigmoidal curve"""
    from scipy.optimize import curve_fit
    import numpy as np
    import math

    def f(x, a, b, c, d, e):
        return a + (b - a) / pow((1 + pow((x / c), d)), e)

    magnitude =  [0.0,   0.5,   1.0,   1.5,   2.0,   2.5,   3.0,   3.5,   4.0,   4.5,   5.0,   5.5,   6.0,   6.5,   7.0,   7.5,   8.0,   8.5,   9.0,   9.5,   9.7]
    size_with_stroke = [4.706, 4.537, 4.297, 4.032, 3.753, 3.475, 3.196, 2.928, 2.667, 2.416, 2.187, 1.958, 1.736, 1.528, 1.341, 1.164, 1.005, 0.843, 0.692, 0.554, 0.504]
    size = [x-2*0.176 for x in size_with_stroke]

    popt, pcov = curve_fit(f, magnitude, size)

    print popt
    print np.sqrt(np.diag(pcov))

    stderr = 0

    for x, y in zip(magnitude, size):
        fval = f(x, *popt)
        stderr += pow(fval-y, 2)
        print "X: {0:.2f} Y: {1:.2f} F: {2:.2f} Delta: {3:.6f}".format(x, y, fval, fval-y)

    print
    print math.sqrt(stderr)