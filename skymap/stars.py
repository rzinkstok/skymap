import sys
import time
import math
import urllib
from bs4 import BeautifulSoup
from datetime import datetime

from skymap.database import SkyMapDatabase
from skymap.geometry import ensure_angle_range, SphericalPoint
from skymap.constellations import determine_constellation, PointInConstellationPrecession
from skymap.coordinates import julian_year_difference


RAD_TO_DEG = 360.0/(2*math.pi)
J1991_TO_J2000_PM_CONVERSION_FACTOR = ((datetime(2000, 1, 1).date() - datetime(1991, 4, 1).date()).days/365.25)/3.6e6
KM_PER_S_TO_PARSEC_PER_YEAR = 1/977780.0
MAS_FOR_FULL_CIRCLE = 360*60*60*1000


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
    """
    Simple propagation in angular coordinates.

    :param from_epoch: datetime
    :param to_epoch: datetime
    :param right_ascension: in degrees
    :param declination: in degrees
    :param proper_motion_ra: in mas/year, corrected for declination
    :param proper_motion_dec: in mas/year
    :return: new position
    """

    if not proper_motion_dec or not proper_motion_ra:
        return right_ascension, declination

    dt = julian_year_difference(to_epoch, from_epoch)

    # Convert proper motions to degrees per Julian year
    # 1 mas/year = 1e-3 as/year = 1e-3/60.0 amin/year = 1e-3/3600 degrees/year
    pm_ra = proper_motion_ra / 3.6e6
    pm_dec = proper_motion_dec / 3.6e6

    # Calculate the new positions
    ra = right_ascension + dt * pm_ra/math.cos(declination)
    dec = declination + dt * pm_dec

    return ra, dec


def propagate_position2(from_epoch, to_epoch, right_ascension, declination, proper_motion_ra, proper_motion_dec, distance=1.0, radial_velocity=0.0):
    """
    Rigorous propagation in Cartesian coordinates

    :param from_epoch: datetime
    :param to_epoch: datetime
    :param right_ascension: in degrees
    :param declination: in degrees
    :param proper_motion_ra: in mas/year
    :param proper_motion_dec: in mas/year
    :param distance: in parsec
    :param radial_velocity: in km/s
    :return: new position
    """

    # Convert time difference to Julian years
    dt = julian_year_difference(to_epoch, from_epoch)

    # Convert degrees to radians
    right_ascension = math.radians(right_ascension)
    declination = math.radians(declination)

    # Convert proper motion (mas/year) to linear velocity in km/s
    velocity_ra = proper_motion_ra * 2 * math.pi * distance/(MAS_FOR_FULL_CIRCLE * KM_PER_S_TO_PARSEC_PER_YEAR)
    velocity_dec = proper_motion_dec * 2 * math.pi * distance/(MAS_FOR_FULL_CIRCLE * KM_PER_S_TO_PARSEC_PER_YEAR)

    # Convert spherical location to Cartesian location in parsecs
    # +x towards RA 0h, DEC 0
    # +y towards RA 6h, DEC 0
    # +z towards DEC 90
    x = distance * math.cos(declination) * math.cos(right_ascension)
    y = distance * math.cos(declination) * math.sin(right_ascension)
    z = distance * math.sin(declination)

    # Convert spherical velocities to Cartesian, in km/s
    vx = (radial_velocity * math.cos(declination) * math.cos(right_ascension)) - (velocity_ra * math.sin(right_ascension)) - (velocity_dec * math.sin(declination) * math.cos(right_ascension))
    vy = (radial_velocity * math.cos(declination) * math.sin(right_ascension)) + (velocity_ra * math.cos(right_ascension)) - (velocity_dec * math.sin(declination) * math.sin(right_ascension))
    vz = radial_velocity * math.sin(declination) + velocity_dec * math.cos(declination)

    # Convert velocities from km/s to parsec/yr
    vx *= KM_PER_S_TO_PARSEC_PER_YEAR
    vy *= KM_PER_S_TO_PARSEC_PER_YEAR
    vz *= KM_PER_S_TO_PARSEC_PER_YEAR

    # Propagate position in parsecs
    x += vx * dt
    y += vy * dt
    z += vz * dt

    # Convert new position to spherical
    dxy = math.sqrt(x**2 + y**2)
    right_ascension = math.degrees(math.atan2(y, x))
    declination = math.degrees(math.atan2(z, dxy))

    if right_ascension < 0:
        right_ascension += 360.0

    return right_ascension, declination


class Star(object):
    def __init__(self, row):
        self.data = row

    @property
    def hip(self):
        return self.data['hip']

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
        m = [self.data['hp_magnitude'], self.data['vt_magnitude'], self.data['magnitude']]
        return next((item for item in m if item is not None), None)

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
                    hp_magnitude FLOAT,
                    vt_magnitude FLOAT,
                    bt_magnitude FLOAT,

                    right_ascension FLOAT,
                    declination FLOAT,
                    proper_motion_ra FLOAT,
                    proper_motion_dec FLOAT,

                    ccdm VARCHAR(16),
                    nhip_entries_for_ccdm INT,
                    component_identifiers VARCHAR(8),
                    number_of_components INT,
                    multiple_annex_flag VARCHAR(1),
                    tyc_multiple_flag VARCHAR(1),

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
            INSERT INTO skymap_stars (
                tyc1, tyc2, tyc3, hip, hd1, hd2,
                right_ascension,
                declination,
                proper_motion_ra, proper_motion_dec,
                bt_magnitude, vt_magnitude,
                component_identifiers
            )
            SELECT
                t2.TYC1, t2.TYC2, t2.TYC3, t2.HIP, t2hd.HD1, t2hd.HD2,
                t2.RAmdeg,
                t2.DEmdeg,
                t2.pmRA, t2.pmDE,
                t2.BTmag, t2.VTmag,
                t2.CCDM
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
    # TODO: Leave out the 254 duplicate stars?
    print "Inserting Tycho-2 supplement 1 data"
    t1 = time.time()
    q = """
            INSERT INTO skymap_stars (
                tyc1, tyc2, tyc3, hip, hd1, hd2,
                right_ascension,
                declination,
                proper_motion_ra, proper_motion_dec,
                bt_magnitude, vt_magnitude,
                component_identifiers
            )
            SELECT
                t2.TYC1, t2.TYC2, t2.TYC3, t2.HIP, t2hd.HD1, t2hd.HD2,
                CASE WHEN t2.pmRA IS NULL THEN t2.RAdeg ELSE t2.RAdeg + t2.pmRA*{0} END,
                CASE WHEN t2.pmDE IS NULL THEN t2.DEdeg ELSE t2.DEdeg + t2.pmDE*{0} END,
                t2.pmRA, t2.pmDE,
                t2.BTmag, t2.VTmag,
                t2.CCDM
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
    # Leave out Hipparcos stars not measured by Tycho-1 (Source=H)
    # TODO: Leave out Tycho-1 stars resolved into multiple stars by Tycho-2
    print "Inserting Tycho-1 data"
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
            AND hiptyc_tyc_main.Source != 'H'
        """
    #db.commit_query(q)
    t2 = time.time()
    print "{:.1f} s".format(t2 - t1)

    # Overwrite astrometry from Hipparcos New Reduction
    # Overwrite photometry, add multiplicity from Hipparcos
    # Hipparcos stars that are resolved into multiple Tycho stars are excluded
    # The 263 stars that lack proper astrometry are excluded
    # Astrometry is position at J1991.25 (ICRS), which is converted to J2000 using the proper motion
    print "Inserting Hipparcos data"

    t1 = time.time()
    q = """
            UPDATE skymap_stars, hipnew_hip2, hiptyc_hip_main
            SET
              skymap_stars.right_ascension=hipnew_hip2.RArad*{0} + hiptyc_hip_main.pmRA*{1},
              skymap_stars.declination=hipnew_hip2.DErad*{0} + hiptyc_hip_main.pmDE*{1},
              skymap_stars.proper_motion_ra=hipnew_hip2.pmRA,
              skymap_stars.proper_motion_dec=hipnew_hip2.pmDE,
              skymap_stars.hp_magnitude=hiptyc_hip_main.Hpmag,
              skymap_stars.ccdm=hiptyc_hip_main.CCDM,
              skymap_stars.nhip_entries_for_ccdm=hiptyc_hip_main.Nsys,
              skymap_stars.number_of_components=hiptyc_hip_main.Ncomp,
              skymap_stars.component_identifiers=hiptyc_hip_main.m_HIP
            WHERE hiptyc_hip_main.HIP=skymap_stars.hip
            AND hipnew_hip2.HIP=skymap_stars.hip
            AND skymap_stars.hip NOT IN (
                SELECT * FROM (
                    (SELECT HIP FROM tyc2_tyc2) UNION ALL (SELECT HIP FROM tyc2_suppl_1)
                ) AS all_hip GROUP BY HIP HAVING COUNT(HIP) > 1
            )
            AND hiptyc_hip_main.RAdeg is not NULL
        """.format(RAD_TO_DEG, J1991_TO_J2000_PM_CONVERSION_FACTOR)
    #db.commit_query(q)
    t2 = time.time()
    print "{:.1f} s".format(t2 - t1)

    # Add data from Hipparcos variability annex
    # Hipparcos stars that are resolved into multiple Tycho stars are excluded
    print "Inserting Hipparcos Variability Annex data"
    t1 = time.time()
    q = """
            UPDATE skymap_stars, hiptyc_hip_va_1
            SET
              skymap_stars.max_magnitude=hiptyc_hip_va_1.maxMag,
              skymap_stars.min_magnitude=hiptyc_hip_va_1.minMag,
              skymap_stars.variable_name=hiptyc_hip_va_1.VarName
            WHERE hiptyc_hip_va_1.HIP=skymap_stars.hip
            AND skymap_stars.hip NOT IN (
                SELECT * FROM (
                    (SELECT HIP FROM tyc2_tyc2) UNION ALL (SELECT HIP FROM tyc2_suppl_1)
                ) AS all_hip GROUP BY HIP HAVING COUNT(HIP) > 1
            )
        """
    #db.commit_query(q)
    t2 = time.time()
    print "{:.1f} s".format(t2 - t1)

    # Add the 263 Hipparcos stars with no astrometric solution (use the Hipparcos Input Catalog data)
    # Of these, only stars that have a value for Hpmag are included (249 stars)
    # print "Inserting Hipparcos stars without astrometric solution"
    # t1 = time.time()
    # stars = db.query("""SELECT * FROM hiptyc_hip_main WHERE RAdeg IS NULL AND Hpmag IS NOT NULL""")
    # for s in stars:
    #     q = """
    #         INSERT INTO skymap_stars (
    #                 hip, hd1, hd2,
    #                 right_ascension,
    #                 declination,
    #                 hp_magnitude,
    #                 max_magnitude,
    #                 min_magnitude
    #             )
    #             SELECT
    #                 t2.TYC1, t2.TYC2, t2.TYC3, t2.HIP, t2hd.HD1, t2hd.HD2,
    #                 CASE WHEN t2.pmRA IS NULL THEN t2.RAdeg ELSE t2.RAdeg + t2.pmRA*{0} END,
    #                 CASE WHEN t2.pmDE IS NULL THEN t2.DEdeg ELSE t2.DEdeg + t2.pmDE*{0} END,
    #                 t2.pmRA, t2.pmDE,
    #                 t2.BTmag, t2.VTmag,
    #                 t2.CCDM
    #             FROM tyc2_suppl_1 AS t2
    #
    #     """
    #     db.commit_query(q)
    # t2 = time.time()
    # print "{:.1f} s".format(t2 - t1)

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
        hd = int(tds[8].get_text().strip())
        proper_name = tds[2].get_text().strip()
        date = tds[9].get_text().strip()
        if date == '2015-12-15':
            continue

        row = db.query_one("""SELECT id FROM skymap_stars WHERE hip={} ORDER BY hp_magnitude ASC LIMIT 1""".format(hip))
        if row is None:
            row = db.query_one("""SELECT id FROM skymap_stars WHERE hd1={0} OR hd2={0} ORDER BY hp_magnitude ASC LIMIT 1""".format(hd))

        q = """UPDATE skymap_stars SET proper_name="{}" WHERE id={}""".format(proper_name, row['id'])
        db.commit_query(q)

    # Add some special cases
    special_cases = {
        87937: "Barnard's Star",
        24186: "Kapteyn's Star",
        49908: "Groombridge 1618",
        57939: "Groombridge 1830",
        105090: "Lacaille 8760",
        114046: "Lacaille 9352",
        54035: "Lalande 21185",
        114622: "Bradley 3077"
    }
    for hip, proper_name in special_cases.items():
        rid = db.query_one("""SELECT id FROM skymap_stars WHERE hip={} ORDER BY hp_magnitude ASC LIMIT 1""".format(hip))['id']
        q = """UPDATE skymap_stars SET proper_name="{}" WHERE id={}""".format(proper_name, rid)
        db.commit_query(q)

    t2 = time.time()
    print "{:.1f} s".format(t2 - t1)

    # Add constellation
    print "Adding constellations"
    t1 = time.time()
    rows = db.query("""SELECT id, right_ascension, declination FROM skymap_stars""")
    nrecords = len(rows)
    pc = PointInConstellationPrecession()
    for i, r in enumerate(rows):
        if i%1000 == 0:
            sys.stdout.write("\r{0:.1f}%".format(i * 100.0 / (nrecords - 1)))
            sys.stdout.flush()
        c = determine_constellation(r['right_ascension'], r['declination'], pc, db)
        db.commit_query("UPDATE skymap_stars SET constellation='{}' WHERE id={}".format(c, r['id']))
    t2 = time.time()
    print
    print "{:.1f} s".format(t2 - t1)


def select_stars(magnitude, constellation=None, ra_range=None, dec_range=None):
    db = SkyMapDatabase()
    result = []
    q = """SELECT * FROM skymap_stars WHERE magnitude<={0}""".format(magnitude)

    if constellation:
        q += """ AND constellation='{0}'""".format(constellation)

    if ra_range:
        min_ra, max_ra = ra_range
        min_ra = ensure_angle_range(min_ra)
        max_ra = ensure_angle_range(max_ra)

        if min_ra < max_ra:
            q += """ AND right_ascension>={0} AND right_ascension<={1}""".format(min_ra, max_ra)
        elif max_ra < min_ra:
            q += """ AND (right_ascension>={0} OR right_ascension<={1})""".format(min_ra, max_ra)
        else:
            # min_ra is equal to max_ra: full circle: no ra limits
            pass

    if dec_range:
        min_dec = dec_range[0]
        max_dec = dec_range[1]

        if min_dec < -90 or min_dec > 90 or max_dec < -90 or max_dec > 90 or max_dec <= min_dec:
            raise ValueError("Illegal DEC range!")
        q += """ AND declination>={0} AND declination<={1}""".format(min_dec, max_dec)

    # Order stars from brightest to weakest so displaying them is easier
    q += """ ORDER BY magnitude ASC"""

    rows = db.query(q)
    for row in rows:
        result.append(Star(row))

    db.close()
    return result


def sum_magnitudes(m1, m2):
    return -2.5*math.log10(pow(10, -m1/2.5) + pow(10, -m2/2.5))


if __name__ == "__main__":
    build_star_database()



"""
Multiplicity
------------

Hipparcos:

Primary: CCDM

- Proximity flag (Proxy), values H or T for Hipparcos or Tycho.
  Indicates component within 10 arcseconds. Component is either an entry or a component of an entry. Hip entries with
  G, O, V or X in field MultFlag are not counted (so only multiple stars with component solutions or single stars),
  just as entries with S in Qual (suspected non-single). If both H and T apply, then H is used.
- Reference flag for astrometrics (AstroRef), values A-G, S, *, +
  Indicates for which component (or the photocenter, or the center of mass) the astrometrics are given
- Reference flag for Tycho photometrics BT and VT (m_BTmag), values A-E, S, *, -
  Indicates for which component (or all, or several) the photometrics are given
- Reference flag for Hipparcos photometrics Hpmag, values A-E, S, *, -
  Indicates for which component (or all) the photometrics are given
- CCDM: CCDM identifier (CCDM)
- Historical status of the CCDM identifier (n_CCDM), values H, I, M
- Nsys: Number of catalogue entries with the same CCDM identifier
- Ncomp: Number of components into which the entry was resolved
- MultFlag: Double and Multiple Systems Annex flag, values C, G, O, V, X
  Only value C refers to real resolved multiple systems
- Source: Source of the absolute astrometry, values F, I, L, P, S, blank
  F, I and L are secondary components, P is primary; S means multiple system processed as single star;
- Solution quality flag, values A-D, S
  S means suspected; can be regarded as single.
- Component designation, values AB, BA, etc
  Data for these components are presented in the following fields, with the first component mentioned being the brightest
- Position angle, separation, magnitude difference, ...

Tycho-1:
- TYC3 component number
  Components must be within 15 arcseconds to be included in the same TYC1/TYC2 number
- Proximity flag (Proxy), values H or T
  Whether star or component within 10 arcseconds. Includes Hipparcos components that are merged into single Tycho entry
- Unresolved duplicity flag, values D, R, S, Y, Z, blank
  Resolved stars have seperate entries. Duplicity is clearly indicated for unresolved entries only when this flag is D
- CCDM component identifier [A-Z, AB, TT=ABC] (5898 have more than 1 component)

Tycho-2:
- TYC3 component number
- CCDM component identifier (5082 have 2 components, 2 have 3 components)


"""