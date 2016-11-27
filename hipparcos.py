"""
Hipparcos data from the XHIP-catalog
Position data is in the coordinate system ICRS, which is essentially J2000.0.
The epoch (time for which the positions are valid) is J1991.25
In order to get positions in J2000.0 coordinates at a certain date (epoch), just use proper motion to propagate the star's position.
If a different coordinate system is needed, precession of the coordinate system is needed. In practice, this will only apply to
constellation boundary data as these are defined in J1875 coordinates.
"""

import os
import sys
import gzip
import urllib
import sqlite3
import datetime

from geometry import HourAngle, DMSAngle


DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "hipparcos")
FILES_NAMES = ['ReadMe', 'main.dat.gz', 'photo.dat.gz', 'biblio.dat.gz']
DATA_FILES = [os.path.join(DATA_FOLDER, f) for f in FILES_NAMES]
DATABASE_FILE = os.path.join(DATA_FOLDER, "xhip.db")
URLS = [os.path.join("ftp://cdsarc.u-strasbg.fr/pub/cats/V/137D", f) for f in FILES_NAMES]
GREEK_LETTERS = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa", "lambda", "mu", "nu", "ksi", "omicron", "pi", "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega"]


def connect(wipe=False):
    if wipe and os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    return conn, cursor


class HipparcosStar(object):
    def __init__(self, row, column_names):
        self.data = dict(zip(column_names, row))

    @property
    def identifier(self):
        return self.data["id"]

    @property
    def right_ascension(self):
        return float(self.data["right_ascension"])

    @property
    def declination(self):
        return float(self.data["declination"])

    @property
    def proper_motion_ra(self):
        return float(self.data['proper_motion_ra'])

    @property
    def proper_motion_dec(self):
        return float(self.data['proper_motion_dec'])

    @property
    def median_magnitude(self):
        return float(self.data["median_magnitude"])

    @property
    def visual_magnitude(self):
        return float(self.data["Vmag"])

    @property
    def visual_magnitude_max(self):
        return self.median_magnitude_max-self.median_magnitude + self.visual_magnitude

    @property
    def visual_magnitude_min(self):
        return self.median_magnitude_min-self.median_magnitude + self.visual_magnitude

    @property
    def absolute_magnitude(self):
        return float(self.data["absolute_Vmag"])

    @property
    def median_magnitude_max(self):
        try:
            return float(self.data['median_magnitude_max'])
        except ValueError:
            return self.median_magnitude

    @property
    def median_magnitude_min(self):
        try:
            return float(self.data['median_magnitude_min'])
        except ValueError:
            return self.median_magnitude

    @property
    def variability_type(self):
        return self.data['variability_type']

    @property
    def is_variable(self):
        if self.variability_type.lower() != "c":
            if self.median_magnitude_max - self.median_magnitude_min <= -0.5:
                return True
        return False

    @property
    def is_double(self):
        return False

    @property
    def constellation(self):
        return self.data["constellation"]

    @property
    def name(self):
        return self.data["name"]

    @property
    def right_ascension_ha(self):
        ha = HourAngle()
        ha.from_degrees(self.right_ascension)
        return ha

    @property
    def declination_dms(self):
        dms = DMSAngle()
        dms.from_degrees(self.declination)
        return dms

    @property
    def greek_letter(self):
        for x in GREEK_LETTERS:
            if "{0} ".format(x) in self.name.lower():
                if x == "omicron":
                    return "o"
                else:
                    return "$\\{0}$".format(x)
        return ""

    @property
    def numeral(self):
        if self.name:
            part = self.name.split()[0]
            if part.isdigit():
                return part
        return ""

    @property
    def common_name(self):
        import re
        m = re.search("\((.+)\)", self.name)
        if m:
            common_name = m.groups()[0]
        else:
            common_name = ''
        for s in ['Wolf', 'HR', 'Lalande', 'Ross']:
            if common_name.startswith(s):
                common_name = ''
                break
        return common_name

    @property
    def identifier_string(self):
        return self.greek_letter or self.numeral

    def propagate_position(self, date=None):
        if date is None:
            date = datetime.date(2000, 1, 1)

        # J1991.25 is april 2, 1991
        delta = date - datetime.date(1991, 4, 2)
        dt = delta.days/365.25

        # mas/year = 1e-3 as/year = 1e-3/60.0 amin/year = 1e-3/3600 degrees/year
        ra = self.right_ascension + dt*self.proper_motion_ra/3.6e6
        dec = self.declination + dt*self.proper_motion_dec/3.6e6
        return ra, dec


def get_star(hip_id):
    conn = sqlite3.connect("data/hipparcos/xhip.db")
    c = conn.cursor()

    q = "SELECT * " \
        "FROM main " \
        "JOIN photo ON photo.id=main.id " \
        "JOIN biblio ON biblio.id=main.id " \
        "WHERE main.id={0}".format(hip_id)
    res = c.execute(q)
    row = res.fetchone()
    columns = [x[0] for x in res.description]
    conn.close()
    return HipparcosStar(row, columns)


def select_stars(magnitude=0.0, constellation=None, ra_range=None, dec_range=None):
    conn = sqlite3.connect("data/hipparcos/xhip.db")
    c = conn.cursor()

    result = []
    q = "SELECT * " \
        "FROM main " \
        "JOIN photo ON photo.id=main.id " \
        "JOIN biblio ON biblio.id=main.id " \
        "WHERE photo.Vmag<{0}".format(magnitude)
    if constellation:
        q += " AND biblio.constellation='{0}'".format(constellation)
    if ra_range:
        if ra_range[0] < 0:
            while ra_range[0] < 0:
                ra_range = (ra_range[0] + 360, ra_range[1])
        if ra_range[1] < 0:
            while ra_range[1] < 0:
                ra_range = (ra_range[0], ra_range[1]+360)

        if ra_range[0] < 0 or ra_range[0] > 360 or ra_range[1] < 0 or ra_range[1] > 360:
            raise ValueError("Illegal RA range!")
        if ra_range[0] < ra_range[1]:
            q += " AND main.right_ascension>={0} AND main.right_ascension<={1}".format(ra_range[0], ra_range[1])
        elif ra_range[1] < ra_range[0]:
            q += " AND (main.right_ascension>={0} OR main.right_ascension<={1})".format(ra_range[0], ra_range[1])
        else:
            raise ValueError("Illegal RA range!")
    if dec_range:
        if dec_range[0] < -90 or dec_range[0] > 90 or dec_range[1] < -90 or dec_range[1] > 90 or dec_range[1] <= dec_range[0]:
            raise ValueError("Illegal DEC range!")
        q += " AND main.declination>={0} AND main.declination<={1}".format(dec_range[0], dec_range[1])

    q += " ORDER BY photo.Vmag ASC"
    res = c.execute(q)
    columns = [x[0] for x in res.description]
    for row in res:
        result.append(HipparcosStar(row, columns))

    conn.close()
    return result


def build_hipparcos_database():
    print("")
    print("Building Hipparcos database")

    # Download data files
    for i, f in enumerate(DATA_FILES):
        data_path = os.path.dirname(f)
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        if not os.path.exists(f):
            url = URLS[i]
            print("Downloading {0}".format(url))
            urllib.urlretrieve(url, f)

    # Determine number of records per table
    number_of_records = {}
    with open(DATA_FILES[0], 'r') as fp:
        for l in fp.readlines():
            for f in [f for f in FILES_NAMES if f != "ReadMe"]:
                fn = f[:-3]
                if l.startswith(fn):
                    number_of_records[f] = int(l.split()[2])

    # Connect to database and wipe it clean
    conn, c = connect(True)

    # Create main table
    c.execute("""CREATE TABLE main (
                  id INT,
                  component TEXT,
                  classes TEXT,
                  groups TEXT,
                  right_ascension real,
                  declination real,
                  parallax real,
                  proper_motion_ra real,
                  proper_motion_dec real,
                  se_right_ascension real,
                  se_declination real,
                  se_parallax real,
                  se_proper_motion_ra real,
                  se_proper_motion_dec real,
                  ref_astrometry text,
                  ref_proper_motion text,
                  galactic_longitude real,
                  galactic_latitude real,
                  distance real,
                  e_distance real,
                  proper_motion_glon real,
                  proper_motion_glat real,
                  x real,
                  y real,
                  z real,
                  galactocentric_distance real,
                  transverse_velocity real,
                  spectral_type text,
                  temperature_class text,
                  luminosity_class text,
                  radial_velocity real,
                  se_radial_velocity real,
                  quality_flag_radial_velocity text,
                  iron_abundance real,
                  se_iron_abundance real,
                  quality_flag_iron_abundance text,
                  age real,
                  lower_cl_age real,
                  upper_cl_age real,
                  u real,
                  v real,
                  w real,
                  total_heliocentric_velocity real,
                  minimum_distance real,
                  timing_minimum_distance real,
                  orbital_eccentricity real,
                  pericenter_position_angle real,
                  semi_major_axis real,
                  semi_minor_axis real,
                  focus_to_center_distance real,
                  semilatus_rectum real,
                  orbital_radius_pericenter real,
                  orbital_radius_apocenter real,
                  number_of_exoplanets int,
                  exoplanet_discovery_methods text
                  )""")
    conn.commit()

    # Create photo table
    c.execute("""CREATE TABLE photo (
                          id int,
                          median_magnitude real,
                          se_median_magnitude real,
                          reference_flag_median_magnitude text,
                          median_magnitude_max real,
                          median_magnitude_min real,
                          variability_period real,
                          variability_type text,
                          Umag real,
                          Bmag real,
                          Vmag real,
                          Rmag real,
                          Imag real,
                          Jmag real,
                          Hmag real,
                          Kmag real,
                          Jmag_uncertainty real,
                          Hmag_uncertainty real,
                          Kmag_uncertainty real,
                          source_designation_2MASS text,
                          JHK_photometric_quality_flag text,
                          BV text,
                          VI text,
                          se_BV text,
                          se_VI text,
                          absolute_median_magnitude float,
                          absolute_Umag real,
                          absolute_Bmag real,
                          absolute_Vmag real,
                          absolute_Rmag real,
                          absolute_Imag real,
                          absolute_Jmag real,
                          absolute_Hmag real,
                          absolute_Kmag real,
                          luminosity real,
                          magmin float
            )""")
    conn.commit()

    # Create biblio table
    c.execute("""CREATE TABLE biblio (
                        id int,
                        henri_draper_id text,
                        constellation text,
                        millenium_star_atlas_page int,
                        coordinates text,
                        name text,
                        group_name text,
                        ref_component text,
                        ref_spectral_type text,
                        ref_radial_velocity text,
                        reference_iron_abundance text
            )""")
    conn.commit()

    # Fill the tables
    for file_path in DATA_FILES[1:]:
        file_name = os.path.split(file_path)[-1]
        table_name = file_name.split(".")[0]
        print("")
        print("Processing {0}".format(file_name))
        nrecords = number_of_records[file_name]
        fp = gzip.open(file_path, "rb")
        for i, l in enumerate(fp):
            sys.stdout.write("\r{0:.1f}%".format(i*100.0/(nrecords-1)))
            sys.stdout.flush()
            parts = [x.strip() for x in l.split("|")]

            # Fix error in biblio database
            if table_name == "biblio" and i == 30679:
                parts.pop(6)

            c.execute("INSERT INTO " + table_name + " VALUES (\"" + "\",\"".join(parts) + "\")")
            conn.commit()
