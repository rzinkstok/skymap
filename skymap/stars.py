import os
import sys
import time
import urllib
from bs4 import BeautifulSoup
from datetime import datetime

from skymap.database import SkyMapDatabase
from skymap.geometry import ensure_angle_range, SphericalPoint
from skymap.constellations import determine_constellation


J1991_TO_J2000_PM_CONVERSION_FACTOR = ((datetime(2000, 1, 1).date() - datetime(1991, 4, 1).date()).days/365.25)/3.6e6


GREEK_LETTERS = {
    "alp": "alpha",
    "bet": "beta",
    "gam": "gamma",
    "del": "delta",
    "eps": "epsilon",
    "zet": "zeta",
    "eta": "eta",
    "the": "theta",
    "iot": "iota",
    "kap": "kappa",
    "lam": "lambda",
    "mu": "mu",
    "nu": "nu",
    "xi": "xi",
    "omi": "omicron",
    "pi": "pi",
    "rho": "rho",
    "sig": "sigma",
    "tau": "tau",
    "ups": "upsilon",
    "phi": "phi",
    "chi": "chi",
    "psi": "psi",
    "ome": "omega"
}


def propagate_position(from_epoch, to_epoch, right_ascension, declination, proper_motion_ra, proper_motion_dec):
    delta = to_epoch - from_epoch
    dt = delta.days / 365.25  # dt in years

    # mas/year = 1e-3 as/year = 1e-3/60.0 amin/year = 1e-3/3600 degrees/year
    pmra = proper_motion_ra
    pmdec = proper_motion_dec
    if not pmra or not pmdec:
        return right_ascension, declination
    ra = right_ascension + dt * pmra / 3.6e6
    dec = declination + dt * pmdec / 3.6e6
    return ra, dec


class Star(object):
    def __init__(self, row):
        self.data = row

    @property
    def bayer(self):
        """Returns the Bayer designation for the star, if present"""
        return self.data['bayer']

    @property
    def flamsteed(self):
        """Returns the Flamsteed number for the star, if present"""
        return self.data['flamsteed']

    @property
    def proper_name(self):
        """Returns the proper name for the star, if present"""
        return self.data['proper_name']

    @property
    def identifier_string(self):
        return ""

    @property
    def magnitude(self):
        """Retuns the visual magnitude for the star"""
        return self.data['magnitude']

    @property
    def is_variable(self):
        """Returns true if the star is variable"""
        return (self.data['variability_type'] == "P") or (self.data['tyc_variable_flag'] == "V")

    @property
    def is_multiple(self):
        """Returns True if the star is a binary or multiple star system"""
        ncomp = self.data['number_of_components']
        if ncomp is not None and ncomp > 1:
            return True
        if self.data['tyc_multiple_flag'] == 'D':
            return True
        return False

    @property
    def min_magnitude(self):
        """Returns the minimum magnitude for variable stars"""
        return self.data['min_magnitude']

    @property
    def max_magnitude(self):
        """Returns the maximum magnitude for variable stars"""
        return self.data['max_magnitude']

    def propagate_position(self, date=None):
        """Propagates the position of the star to the given date"""
        epoch = datetime(2000, 1, 1).date()
        return propagate_position(epoch, date, self.right_ascension, self.declination, self.proper_motion_ra, self.proper_motion_dec)

    @property
    def right_ascension(self):
        """Returns the database right ascension for the catalogue epoch in degrees"""
        return self.data['right_ascension']

    @property
    def declination(self):
        """Returns the database declination for the catalogue epoch in degrees"""
        return self.data['declination']

    @property
    def position(self):
        """Returns the position of the star in degrees"""
        return SphericalPoint(self.right_ascension, self.declination)

    @property
    def constellation(self):
        """Returns the constellation the star is in"""
        return self.data['constellation']


def build_star_database():
    db = SkyMapDatabase()

    #db.drop_table("skymap_stars")

    print "Creating table"
    t1 = time.time()
    q = """CREATE TABLE skymap_stars (
                    id INT NOT NULL AUTO_INCREMENT,
                    hip INT,
                    tyc1 INT,
                    tyc2 INT,
                    tyc3 INT,
                    hd1 INT,
                    hd2 INT,
                    hr INT,
                    bd VARCHAR(64),
                    cod VARCHAR(64),
                    cpd VARCHAR(64),
                    bayer VARCHAR(128),
                    flamsteed INT,
                    proper_name VARCHAR(512),
                    constellation VARCHAR(64),

                    magnitude FLOAT,
                    vt_magnitude FLOAT,
                    bt_magnitude FLOAT,

                    right_ascension FLOAT,
                    declination FLOAT,
                    proper_motion_ra FLOAT,
                    proper_motion_dec FLOAT,

                    ccdm VARCHAR(16),
                    nhip_entries_for_ccdm INT,
                    number_of_components INT,
                    multiple_annex_flag VARCHAR(1),
                    tyc_multiple_flag VARCHAR(1),
                    component_identifiers VARCHAR(512),

                    max_magnitude FLOAT,
                    min_magnitude FLOAT,
                    variable_name VARCHAR(512),
                    variability_type VARCHAR(64),
                    tyc_variable_flag VARCHAR(1),

                    PRIMARY KEY (id)
                )"""
    #db.commit_query(q)
    t2 = time.time()
    print "{:.1f} s".format(t2 - t1)

    # Data from Tycho2 with HD from Tyc2_HD
    # Astrometry is mean position at epoch J2000 (ICRS)
    print "Inserting Tycho-2 data"
    t1 = time.time()
    q = """
            INSERT INTO skymap_stars
            (tyc1, tyc2, tyc3, hip, hd1, hd2, right_ascension, declination, proper_motion_ra, proper_motion_dec, bt_magnitude, vt_magnitude)
            SELECT t2.TYC1, t2.TYC2, t2.TYC3, t2.HIP, t2hd.HD1, t2hd.HD2, t2.RAdeg, t2.DEdeg, t2.pmRA, t2.pmDE, t2.BTmag, t2.VTmag
            FROM tyc2_tyc2 AS t2
            LEFT JOIN (
                SELECT TYC1, TYC2, TYC3, MIN(HD) AS HD1, CASE WHEN COUNT(HD)>1 THEN MAX(HD) ELSE NULL END AS HD2
                FROM tyc2hd_tyc2_hd
                WHERE Rem!='D'
                GROUP BY TYC1, TYC2, TYC3
            ) AS t2hd
            ON t2.TYC1=t2hd.TYC1 AND t2.TYC2=t2hd.TYC2 AND t2.TYC3=t2hd.TYC3
        """
    #db.commit_query(q)
    t2 = time.time()
    print "{:.1f} s".format(t2 - t1)

    # Data from Tycho2 supplement 1 with HD from Tyc2_HD
    # Astrometry is position at epoch J1991.25 (ICRS), which is converted to J2000 using the proper motion
    print "Inserting Tycho-2 supplement 1 data"
    t1 = time.time()
    q = """
            INSERT INTO skymap_stars
            (tyc1, tyc2, tyc3, hip, hd1, hd2, right_ascension, declination, proper_motion_ra, proper_motion_dec, bt_magnitude, vt_magnitude)
            SELECT
                t2.TYC1, t2.TYC2, t2.TYC3, t2.HIP, t2hd.HD1, t2hd.HD2,
                CASE WHEN t2.pmRA IS NULL THEN t2.RAdeg ELSE t2.RAdeg + t2.pmRA*{0} END,
                CASE WHEN t2.pmDE IS NULL THEN t2.DEdeg ELSE t2.DEdeg + t2.pmDE*{0} END,
                t2.pmRA, t2.pmDE,
                t2.BTmag, t2.VTmag
            FROM tyc2_suppl_1 AS t2
            LEFT JOIN (
                SELECT TYC1, TYC2, TYC3, MIN(HD) AS HD1, CASE WHEN COUNT(HD)>1 THEN MAX(HD) ELSE NULL END AS HD2
                FROM tyc2hd_tyc2_hd
                WHERE Rem!='D'
                GROUP BY TYC1, TYC2, TYC3
            ) AS t2hd
            ON t2.TYC1=t2hd.TYC1 AND t2.TYC2=t2hd.TYC2 AND t2.TYC3=t2hd.TYC3
        """.format(J1991_TO_J2000_PM_CONVERSION_FACTOR)
    #db.commit_query(q)
    t2 = time.time()
    print "{:.1f} s".format(t2 - t1)

    # Add indexes on TYC1-3, HIP, HD
    print "Adding indexes"
    t1 = time.time()
    # db.add_index("skymap_stars", "TYC1")
    # db.add_index("skymap_stars", "TYC2")
    # db.add_index("skymap_stars", "TYC3")
    # db.add_index("skymap_stars", "HIP")
    # db.add_index("skymap_stars", "HD1")
    # db.add_index("skymap_stars", "HD2")
    t2 = time.time()
    print "{:.1f} s".format(t2 - t1)

    # Overwrite photometry, add variability, multiplicity and DM ids from Tycho1
    print "Inserting Tycho data"
    t1 = time.time()

    q = """
            UPDATE skymap_stars, hiptyc_tyc_main
            SET
                skymap_stars.magnitude=hiptyc_tyc_main.Vmag,
                skymap_stars.vt_magnitude=hiptyc_tyc_main.VTmag,
                skymap_stars.bt_magnitude=hiptyc_tyc_main.BTmag,
                skymap_stars.tyc_variable_flag=hiptyc_tyc_main.VarFlag,
                skymap_stars.min_magnitude=hiptyc_tyc_main.VTmin,
                skymap_stars.max_magnitude=hiptyc_tyc_main.VTmax
            WHERE hiptyc_tyc_main.TYC1=skymap_stars.tyc1
            AND hiptyc_tyc_main.TYC2=skymap_stars.tyc2
            AND hiptyc_tyc_main.TYC3=skymap_stars.tyc3
        """
    #db.commit_query(q)
    t2 = time.time()
    print "{:.1f} s".format(t2 - t1)

    # Overwrite astrometry, photometry, add multiplicity from Hipparcos
    # Hipparcos stars that are resolved into multiple Tycho stars are excluded
    # The 263 stars that lack proper astrometry are excluded
    # Astrometry is position at J1991.25 (ICRS), which is converted to J2000 using the proper motion
    print "Inserting Hipparcos data"
    t1 = time.time()
    q = """
            UPDATE skymap_stars, hiptyc_hip_main
            SET
              skymap_stars.right_ascension=hiptyc_hip_main.RAdeg + hiptyc_hip_main.pmRA*{0},
              skymap_stars.declination=hiptyc_hip_main.DEdeg + hiptyc_hip_main.pmDE*{0},
              skymap_stars.proper_motion_ra=hiptyc_hip_main.pmRA,
              skymap_stars.proper_motion_dec=hiptyc_hip_main.pmDE,
              skymap_stars.magnitude=hiptyc_hip_main.Hpmag,
              skymap_stars.ccdm=hiptyc_hip_main.CCDM,
              skymap_stars.nhip_entries_for_ccdm=hiptyc_hip_main.Nsys,
              skymap_stars.number_of_components=hiptyc_hip_main.Ncomp,
              skymap_stars.component_identifiers=hiptyc_hip_main.m_HIP
            WHERE hiptyc_hip_main.HIP=skymap_stars.hip
            AND skymap_stars.hip NOT IN (SELECT HIP FROM tyc2_tyc2 GROUP BY HIP HAVING COUNT(HIP) > 1)
            AND hiptyc_hip_main.RAdeg is not NULL
        """.format(J1991_TO_J2000_PM_CONVERSION_FACTOR)
    #db.commit_query(q)
    t2 = time.time()
    print "{:.1f} s".format(t2 - t1)

    # Add data from Hipparcos variability annex
    print "Inserting Hipparcos Variability Annex data"
    t1 = time.time()
    q = """
            UPDATE skymap_stars, hiptyc_hip_va_1
            SET
              skymap_stars.max_magnitude=hiptyc_hip_va_1.maxMag,
              skymap_stars.min_magnitude=hiptyc_hip_va_1.minMag,
              skymap_stars.variable_name=hiptyc_hip_va_1.VarName
            WHERE hiptyc_hip_va_1.HIP=skymap_stars.hip
            AND skymap_stars.hip NOT IN (SELECT HIP FROM tyc2_tyc2 GROUP BY HIP HAVING COUNT(HIP) > 1)

        """
    #db.commit_query(q)
    t2 = time.time()
    print "{:.1f} s".format(t2 - t1)

    # Add cross index data
    print "Adding New Cross Index data"
    t1 = time.time()
    q = """
            UPDATE skymap_stars, cross_index_catalog
            SET
              skymap_stars.bayer=cross_index_catalog.Bayer,
              skymap_stars.flamsteed=cross_index_catalog.Fl,
              skymap_stars.constellation=cross_index_catalog.Cst
            WHERE cross_index_catalog.HD=skymap_stars.hd1 OR cross_index_catalog.HD=skymap_stars.hd2
        """
    #db.commit_query(q)
    t2 = time.time()
    print "{:.1f} s".format(t2 - t1)

    # Add star names
    print "Adding proper names"

    t1 = time.time()
    url = "https://www.iau.org/public/themes/naming_stars/"
    r = urllib.urlopen(url).read()
    soup = BeautifulSoup(r, "html5lib")

    for tr in soup.find_all("tbody")[0].find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
        try:
            hip = int(tds[7].get_text().strip())
        except ValueError:
            continue
        proper_name = tds[2].get_text().strip()
        date = tds[9].get_text().strip()
        if date == '2015-12-15':
            continue
        q = """UPDATE skymap_stars SET proper_name="{}" WHERE hip={}""".format(proper_name, hip)
        db.commit_query(q)

    # Add some special cases
    db.commit_query("""UPDATE skymap_stars SET proper_name="Barnard's Star" WHERE hip=87937""")
    db.commit_query("""UPDATE skymap_stars SET proper_name="Kapteyn's Star" WHERE hip=24186""")
    db.commit_query("""UPDATE skymap_stars SET proper_name="Groombridge 1618" WHERE hip=49908""")
    db.commit_query("""UPDATE skymap_stars SET proper_name="Groombridge 1830" WHERE hip=57939""")
    db.commit_query("""UPDATE skymap_stars SET proper_name="Lacaille 8760" WHERE hip=105090""")
    db.commit_query("""UPDATE skymap_stars SET proper_name="Lacaille 9352" WHERE hip=114046""")
    db.commit_query("""UPDATE skymap_stars SET proper_name="Lalande 21185" WHERE hip=54035""")
    db.commit_query("""UPDATE skymap_stars SET proper_name="Bradley 3077" WHERE hip=114622""")

    t2 = time.time()
    print "{:.1f} s".format(t2 - t1)

    # Add constellation
    print "Adding constellations"
    t1 = time.time()
    rows = db.query("""SELECT id, right_ascension, declination FROM skymap_stars""")
    nrecords = len(rows)
    sys.stdout.write("Number of stars: {}".format(nrecords))
    sys.stdout.flush
    for i, r in enumerate(rows):
        if i%1000 == 0:
            sys.stdout.write("\r{0:.1f}%".format(i * 100.0 / (nrecords - 1)))
            sys.stdout.flush()
        c = determine_constellation(r['right_ascension'], r['declination'], db)
        db.commit_query("UPDATE skymap_stars SET constellation='{}' WHERE id={}".format(c, r['id']))
    t2 = time.time()
    print "{:.1f} s".format(t2 - t1)



def select_stars(magnitude, constellation=None, ra_range=None, dec_range=None):
    db = SkyMapDatabase()
    result = []
    q = "SELECT * " \
        "FROM stars " \
        "WHERE magnitude<={0}".format(magnitude)

    if constellation:
        q += " AND constellation='{0}'".format(constellation)

    if ra_range:
        min_ra, max_ra = ra_range
        min_ra = ensure_angle_range(min_ra)
        max_ra = ensure_angle_range(max_ra)

        if min_ra < max_ra:
            q += " AND right_ascension>={0} AND right_ascension<={1}".format(min_ra, max_ra)
        elif max_ra < min_ra:
            q += " AND (right_ascension>={0} OR right_ascension<={1})".format(min_ra, max_ra)
        else:
            # min_ra is equal to max_ra: full circle: no ra limits
            pass

    if dec_range:
        min_dec = dec_range[0]
        max_dec = dec_range[1]

        if min_dec < -90 or min_dec > 90 or max_dec < -90 or max_dec > 90 or max_dec <= min_dec:
            raise ValueError("Illegal DEC range!")
        q += " AND declination>={0} AND declination<={1}".format(min_dec, max_dec)

    # Order stars from brightest to weakest so displaying them is easier
    q += " ORDER BY magnitude ASC"

    print q

    rows = db.query(q)
    for row in rows:
        result.append(Star(row))

    db.close()
    return result


if __name__ == "__main__":
    build_star_database()