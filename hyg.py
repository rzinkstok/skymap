import sqlite3
import math
import datetime
import os
import sys
import urllib

DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "hyg")
DATA_FILE = os.path.join(DATA_FOLDER, "hygdata_v3.csv")
DATABASE_FILE = os.path.join(DATA_FOLDER, "hyg.db")
URL = "https://github.com/astronexus/HYG-Database/raw/master/hygdata_v3.csv"


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


def connect(wipe=False):
    if wipe and os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)
    conn = sqlite3.connect("data/hyg/hyg.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    return conn, c


class Star(object):
    def __init__(self, rowdict):
        self.data = rowdict

    def __getattr__(self, item):
        return self.data[item]

    @property
    def bayer2(self):
        b = self.bayer.lower()
        parts = b.split("-")
        if parts[0] == "omi":
            bayer = "o"
        else:
            bayer = "$\\{0}$".format(GREEK_LETTERS[parts[0]])
        if len(parts) == 2:
            bayer += "$^{0}$".format(parts[1])
        return bayer

    @property
    def identifier_string(self):
        identifier_string = ""
        if self.flam:
            identifier_string += "{0}".format(self.flam)
        if self.bayer:
            identifier_string += self.bayer2
        return identifier_string

    def propagate_position(self, date=None):
        if date is None:
            date = datetime.date(2000, 1, 1)

        # HYG is for epoch 2000.0
        delta = date - datetime.date(2000, 1, 1)
        dt = delta.days/365.25

        # mas/year = 1e-3 as/year = 1e-3/60.0 amin/year = 1e-3/3600 degrees/year
        ra = self.radeg + dt*self.pmra/3.6e6
        dec = self.decdeg + dt*self.pmdec/3.6e6
        return ra, dec

    @property
    def is_variable(self):
        return bool(self.var.strip())

    @property
    def is_multiple(self):
        return self.comp>1


def get_hip_star(hip_id):
    conn, cursor = connect()
    q = "SELECT * " \
        "FROM hygdata " \
        "WHERE hip={0}".format(hip_id)
    res = cursor.execute(q)
    row = res.fetchone()
    conn.close()
    return Star(row)


def select_stars(magnitude=0.0, constellation=None, ra_range=None, dec_range=None):
    conn, cursor = connect()
    result = []
    q = "SELECT * " \
        "FROM hygdata " \
        "WHERE mag<={0}".format(magnitude)
    if constellation:
        q += " AND con='{0}'".format(constellation)
    if ra_range:
        if ra_range[0] < 0:
            while ra_range[0] < 0:
                ra_range = (ra_range[0] + 360, ra_range[1])
        if ra_range[1] < 0:
            while ra_range[1] < 0:
                ra_range = (ra_range[0], ra_range[1]+360)

        if ra_range[0] < 0 or ra_range[0] > 360 or ra_range[1] < 0 or ra_range[1] > 360:
            raise ValueError("Illegal RA range!")

        min_ra = math.radians(ra_range[0])
        max_ra = math.radians(ra_range[1])

        if min_ra < max_ra:
            q += " AND rarad>={0} AND rarad<={1}".format(min_ra, max_ra)
        elif max_ra < min_ra:
            q += " AND (rarad>={0} OR rarad<={1})".format(min_ra, max_ra)
        else:
            raise ValueError("Illegal RA range!")

    if dec_range:
        min_dec = math.radians(dec_range[0])
        max_dec = math.radians(dec_range[1])

        if min_dec < -90 or min_dec > 90 or max_dec < -90 or max_dec > 90 or max_dec <= min_dec:
            raise ValueError("Illegal DEC range!")
        q += " AND decrad>={0} AND decrad<={1}".format(min_dec, max_dec)

    # Order stars from brightest to weakest so displaying them is easier
    q += " ORDER BY mag ASC"
    res = cursor.execute(q)
    for row in res:
        result.append(Star(row))

    conn.close()
    return result


def build_hyg_database():
    print("")
    print("Building HYG database")

    # Download data file
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE))
        print("Downloading {0}".format(URL))
        urllib.urlretrieve(URL, DATA_FILE)

    # Connect
    conn, c = connect(True)

    # Create table
    c.execute("""CREATE TABLE hygdata (
                    id INT,
                    hip INT,
                    hd INT,
                    hr INT,
                    gl INT,
                    bf TEXT,
                    proper TEXT,
                    ra REAL,
                    dec REAL,
                    dist REAL,
                    pmra REAL,
                    pmdec REAL,
                    rv REAL,
                    mag REAL,
                    absmag REAL,
                    spect TEXT,
                    ci REAL,
                    x REAL,
                    y REAL,
                    z REAL,
                    vx REAL,
                    vy REAL,
                    vz REAL,
                    rarad REAL,
                    decrad REAL,
                    pmrarad REAL,
                    pmdecrad REAL,
                    bayer TEXT,
                    flam TEXT,
                    con TEXT,
                    comp INT,
                    comp_primary INT,
                    base TEXT,
                    lum REAL,
                    var TEXT,
                    var_min REAL,
                    var_max REAL
                    )""")

    # Fill the table
    print("")
    print("Processing records")

    # Retrieve the number of records
    with open(DATA_FILE, "r") as fp:
        nrecords = sum([1 for i in fp.readlines()]) - 1

    # Parse all records
    with open(DATA_FILE, "r") as fp:
        for i, l in enumerate(fp.readlines()[1:]):
            sys.stdout.write("\r{0:.1f}%".format(i * 100.0 / (nrecords - 1)))
            sys.stdout.flush()
            parts = [x.strip() for x in l.split(",")]
            c.execute("INSERT INTO hygdata VALUES (\"" + "\",\"".join(parts) + "\")")
            conn.commit()
