import math
import datetime
import numpy

#from skymap.geometry import SphericalPoint, HourAngle


REFERENCE_EPOCH = datetime.datetime(2000, 1, 1).date()


def julian_year_difference(date1, date2):
    """
    Returns the difference date1 - date2 in Julian years

    :param date1: date to be subtracted from (datetime)
    :param date2: date to be subtracted (datetime)
    :return: the difference in Julian years
    """
    tds = (date1 - date2).total_seconds()
    return tds/(365.25 * 86400)







