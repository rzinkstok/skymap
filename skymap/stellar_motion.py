import math
import numpy as np
from skymap.geometry import sky2cartesian_with_parallax, cartesian2sky_with_parallax

KM_PER_S_TO_PARSEC_PER_YEAR = 1.0/977780.0
MAS_TO_RAD = 2 * math.pi / 360*60*60*1000


def simplified_propagation(ra_dec_array, proper_motion_array, from_epoch, to_epoch):
    """Propagates stellar positions using a simplified treatment.

    See the Hipparcos and Tycho catalog, paragraph 1.5.4.

    Args:
        ra_dec_array: ra, dec in degrees
        proper_motion_array: pmRA, pmDE in mas/y
        from_epoch: the epoch of the input data
        to_epoch: the epoch of the output data

    Returns:
        numpy.array: the propagated positions ra and dec in degrees
    """
    # Compute dt in Julian years
    dt = (to_epoch - from_epoch).value / 365.25

    # Propagate the positions; the right ascension is corrected for the cos(dec) factor
    result = np.zeros(ra_dec_array.shape)
    result[:, 0] = ra_dec_array[:, 0] + dt * proper_motion_array[:, 0] / np.cos(ra_dec_array[:, 1])
    result[:, 1] = ra_dec_array[:, 1] + dt * proper_motion_array[:, 0]
    return result


def rigorous_propagation(ra_dec_parallax_array, velocity_array, from_epoch, to_epoch):
    """Propagates stellar positions using a linear space motion model.

    See the Hipparcos and Tycho catalog, paragraph 1.5.5.

    Args:
        ra_dec_parallax_array: ra (degrees), dec (degrees), parallax (mas)
        velocity_array: pm_RA (mas/y), pm_DE (mas/y), radial velocity (km/s)
        from_epoch: the epoch of the input data
        to_epoch: the epoch of the output data

    Returns:
        numpy.array: the propagated positions ra and dec in degrees and parallax in mas
    """
    # Compute dt in Julian years
    dt = (to_epoch - from_epoch).value/365.25

    # Convert pm_RA and pm_DE to linear velocity in parsec/year
    velocity_array[:, :2] = velocity_array[:, :2] * ra_dec_parallax_array[:, 2] * MAS_TO_RAD

    # Convert radial velocity to parsec/year
    velocity_array[:, 2] = velocity_array[:, :2] * KM_PER_S_TO_PARSEC_PER_YEAR

    # Convert spherical to cartesian in parsecs
    r0 = sky2cartesian_with_parallax(ra_dec_parallax_array)

    # Compute normal triad
    z = np.array((0, 0, 1))
    r = r0/np.linalg.norm(r0, axis=1).reshape((r0.shape[0], 1))
    p = np.cross(z, r)
    q = np.cross(r, p)

    # Compute space velocity
    v = p * velocity_array[:, 0] + q * velocity_array[:, 1] + r * velocity_array[:, 2]

    # Propagate
    rt = r0 + v * dt

    # Convert to spherical
    result = cartesian2sky_with_parallax(rt)
    return result
