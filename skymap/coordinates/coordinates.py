import datetime
import math
from astropy.coordinates import Longitude

from skymap.geometry import SkyCoordDeg, ensure_angle_range
from skymap.coordinates import PrecessionCalculator, REFERENCE_EPOCH


GALACTIC_NORTH_POLE = SkyCoordDeg(Longitude("12h49m").degree, 27.4)
GALACTIC_LONGITUDE_NORTH_CELESTIAL_POLE = 123
GALACTIC_NORTH_POLE_EPOCH = datetime.datetime(1950, 1, 1).date()


# Ecliptic coordinate system
def obliquity_of_the_ecliptic(epoch=REFERENCE_EPOCH):
    """Returns the obliquity of the ecliptic for the given epoch, in degrees.

    The calculation is taken from the Astronomical Almanac 2010, as given
    on https://en.wikipedia.org/wiki/Axial_tilt#Short_term.
    """
    a = 23.0 + 26 / 60.0 + 21.406 / 3600.0
    b = -46.836769 / 3600.0
    c = -0.0001831 / 3600.0
    d = 0.00200340 / 3600.0
    e = -0.576e-6 / 3600.0
    f = -0.0434e-6 / 3600.0
    t = (epoch - REFERENCE_EPOCH).days / 36525.0
    return a + b * t + c * t ** 2 + d * t ** 3 + e * t ** 4 + f * t ** 5


def ecliptic_to_equatorial(p, epoch=REFERENCE_EPOCH):
    """Returns the equatorial coordinates for the given point in ecliptic coordinates.

    Equations taken from:
    Practical Astronomy with your Calculator or Spreadsheet
    Peter Duffett-Smith and Jonathan Zwart
    Cambridge University Press, 2011
    Paragraph 27 (page 51)

    Only used to draw the ecliptic.
    """
    eps = math.radians(obliquity_of_the_ecliptic(REFERENCE_EPOCH))
    ceps = math.cos(eps)
    seps = math.sin(eps)

    l = math.radians(p.ra.degree)
    b = math.radians(p.dec.degree)

    longitude = math.degrees(
        math.atan2(math.sin(l) * ceps - math.tan(b) * seps, math.cos(l))
    )
    latitude = math.degrees(
        math.asin(math.sin(b) * ceps + math.cos(b) * seps * math.sin(l))
    )

    # Precess to the current epoch
    pc = PrecessionCalculator(REFERENCE_EPOCH, epoch)
    longitude, latitude = pc.precess(longitude, latitude)

    return SkyCoordDeg(ensure_angle_range(longitude), latitude)


# Galactic coordinate system
def galactic_pole(epoch=REFERENCE_EPOCH):
    """Returns the location of the galactic north pole at the given epoch."""
    p = PrecessionCalculator(GALACTIC_NORTH_POLE_EPOCH, epoch)
    return SkyCoordDeg(
        *p.precess(GALACTIC_NORTH_POLE.ra.degree, GALACTIC_NORTH_POLE.dec.degree)
    )


def galactic_to_equatorial(p, epoch=REFERENCE_EPOCH):
    """Returns the equatorial coordinates for the given point in galactic coordinates.

    Equations taken from:
    Practical Astronomy with your Calculator or Spreadsheet
    Peter Duffett-Smith and Jonathan Zwart
    Cambridge University Press, 2011
    Paragraph 30 (page 58)

    Only used to draw the galactic equator.
    """

    l = math.radians(p.ra.degree)
    b = math.radians(p.dec.degree)

    # Get the longitude and latitude of the north galactic pole
    ngp = galactic_pole(GALACTIC_NORTH_POLE_EPOCH)
    pl = math.radians(ngp.ra.degree)
    pb = math.radians(ngp.dec.degree)

    # Get the galactic longitude offset
    l0 = math.radians(GALACTIC_LONGITUDE_NORTH_CELESTIAL_POLE - 90.0)

    # Determine the equatorial
    longitude = math.degrees(
        math.atan2(
            math.cos(b) * math.cos(l - l0),
            (
                math.sin(b) * math.cos(pb)
                - math.cos(b) * math.sin(pb) * math.sin(l - l0)
            ),
        )
        + pl
    )

    latitude = math.degrees(
        math.asin(
            math.cos(b) * math.cos(pb) * math.sin(l - l0) + math.sin(b) * math.sin(pb)
        )
    )

    # Precess to the current epoch
    pc = PrecessionCalculator(GALACTIC_NORTH_POLE_EPOCH, epoch)
    longitude, latitude = pc.precess(longitude, latitude)

    return SkyCoordDeg(ensure_angle_range(longitude), latitude)


def to_icrs(p):
    return p.transform_to("icrs")
