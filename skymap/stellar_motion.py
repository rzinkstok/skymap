import math
import numpy as np
from astropy.time import Time
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
    dt = (Time(to_epoch) - Time(from_epoch)).value / 365.25

    # Convert proper motions to degrees
    pm_deg = proper_motion_array/(1000 * 60 * 60)

    # Convert declination to rad
    dec_rad = np.deg2rad(ra_dec_array[:, 1])

    # Propagate the positions; the right ascension is corrected for the cos(dec) factor
    result = np.zeros(ra_dec_array.shape)
    result[:, 0] = ra_dec_array[:, 0] + dt * pm_deg[:, 0] / np.cos(dec_rad)
    result[:, 1] = ra_dec_array[:, 1] + dt * pm_deg[:, 1]
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
    npoints = ra_dec_parallax_array.shape[0]

    # Compute dt in Julian years
    dt = (Time(to_epoch) - Time(from_epoch)).value / 365.25

    # Convert pm_RA and pm_DE to linear velocity in parsec/year
    velocity_array[:, :2] = velocity_array[:, :2] * MAS_TO_RAD / ra_dec_parallax_array[:, 2].reshape((npoints, 1))

    # Convert radial velocity to parsec/year
    velocity_array[:, 2] = velocity_array[:, 2] * KM_PER_S_TO_PARSEC_PER_YEAR

    # Convert spherical to cartesian in parsecs
    r0 = sky2cartesian_with_parallax(ra_dec_parallax_array)

    # Compute normal triad
    z = np.array((0, 0, 1))
    r = r0/np.linalg.norm(r0, axis=1).reshape((npoints, 1))
    p = np.cross(z, r)
    q = np.cross(r, p)

    # Compute space velocity
    vp = p * velocity_array[:, 0].reshape((npoints, 1))
    vq = q * velocity_array[:, 1].reshape((npoints, 1))
    vr = r * velocity_array[:, 2].reshape((npoints, 1))
    v = vp + vq + vr

    # Propagate
    rt = r0 + v * dt

    # Convert to spherical
    result = cartesian2sky_with_parallax(rt)
    return result
