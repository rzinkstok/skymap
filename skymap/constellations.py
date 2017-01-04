import sys
import os
import math
import numpy
import datetime
import urllib

from skymap.database import SkyMapDatabase
from skymap.geometry import SphericalPoint, ensure_angle_range

DATA_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "data", "constellation_boundaries")
DATA_FILE = os.path.join(DATA_FOLDER, "bound_18.dat")
URL = "ftp://cdsarc.u-strasbg.fr/pub/cats/VI/49/bound_18.dat"

CONSTELLATIONS = {
    'and': 'Andromeda',
    'ant': 'Antlia',
    'aps': 'Apus',
    'aqr': 'Aquarius',
    'aql': 'Aquila',
    'ara': 'Ara',
    'ari': 'Aries',
    'aur': 'Auriga',
    'boo': 'Bootes',
    'cae': 'Caelum',
    'cam': 'Camelopardalis',
    'cnc': 'Cancer',
    'cvn': 'Canes Venatici',
    'cma': 'Canis Major',
    'cmi': 'Canis Minor',
    'cap': 'Capricornus',
    'car': 'Carina',
    'cas': 'Cassiopeia',
    'cen': 'Centaurus',
    'cep': 'Cepheus',
    'cet': 'Cetus',
    'cha': 'Chamaeleon',
    'cir': 'Circinus',
    'col': 'Columba',
    'com': 'Coma Berenices',
    'cra': 'Corona Austrina',
    'crb': 'Corona Borealis',
    'crv': 'Corvus',
    'crt': 'Crater',
    'cru': 'Crux',
    'cyg': 'Cygnus',
    'del': 'Delphinus',
    'dor': 'Dorado',
    'dra': 'Draco',
    'equ': 'Equuleus',
    'eri': 'Eridanus',
    'for': 'Fornax',
    'gem': 'Gemini',
    'gru': 'Grus',
    'her': 'Hercules',
    'hor': 'Horologium',
    'hya': 'Hydra',
    'hyi': 'Hydrus',
    'ind': 'Indus',
    'lac': 'Lacerta',
    'leo': 'Leo',
    'lmi': 'Leo Minor',
    'lep': 'Lepus',
    'lib': 'Libra',
    'lup': 'Lupus',
    'lyn': 'Lynx',
    'lyr': 'Lyra',
    'men': 'Mensa',
    'mic': 'Microscopium',
    'mon': 'Monoceros',
    'mus': 'Musca',
    'nor': 'Norma',
    'oct': 'Octans',
    'oph': 'Ophiuchus',
    'ori': 'Orion',
    'pav': 'Pavo',
    'peg': 'Pegasus',
    'per': 'Perseus',
    'phe': 'Phoenix',
    'pic': 'Pictor',
    'psc': 'Pisces',
    'psa': 'Piscis Austrinus',
    'pup': 'Puppis',
    'pyx': 'Pyxis',
    'ret': 'Reticulum',
    'sge': 'Sagitta',
    'sgr': 'Sagittarius',
    'sco': 'Scorpius',
    'scl': 'Sculptor',
    'sct': 'Scutum',
    'ser': 'Serpens',
    'sex': 'Sextans',
    'tau': 'Taurus',
    'tel': 'Telescopium',
    'tri': 'Triangulum',
    'tra': 'Triangulum Australe',
    'tuc': 'Tucana',
    'uma': 'Ursa Major',
    'umi': 'Ursa Minor',
    'vel': 'Vela',
    'vir': 'Virgo',
    'vol': 'Volans',
    'vul': 'Vulpecula'
}


REFERENCE_EPOCH = datetime.datetime(2000, 1, 1).date()
CONST_BOUND_EPOCH = datetime.datetime(1875, 1, 1).date()


def determine_constellation(ra, de, db):
    ra, de = precess(ra, de, REFERENCE_EPOCH, CONST_BOUND_EPOCH)
    ra /= 15.0  # Convert to fractional hours of right ascension

    q = """
            SELECT const
            FROM skymap.cst_id_data
            WHERE DE_low < {0} AND RA_low <= {1}  AND RA_up > {1} ORDER BY pk LIMIT 1
        """.format(de, ra)
    return db.query_one(q)['const'].lower()


def fractional_year(date):
    def since_epoch(d): # returns seconds since epoch
        return time.mktime(d.timetuple())
    s = since_epoch

    year = date.year
    start_of_this_year = datetime.datetime(year=year, month=1, day=1)
    start_of_next_year = datetime.datetime(year=year+1, month=1, day=1)

    year_elapsed = s(date) - s(start_of_this_year)
    year_duration = s(start_of_next_year) - s(start_of_this_year)
    fraction = year_elapsed/year_duration

    return date.year + fraction


class BoundaryEdge(object):
    def __init__(self, row=None):
        if row:
            self.epoch = 1875.0
            self.identifier = row['id']
            self.p1 = SphericalPoint(row['ra1'], row['dec1'])
            self.p2 = SphericalPoint(row['ra2'], row['dec2'])
            self.constellation = row['constellation']
            self.order = row['edge_order']
            self.other_constellation = row['other_constellation']
            self.complement = row['complement']
            self.interpolated_points = []
        else:
            self.epoch = 1875.0
            self.identifier = None
            self.p1 = None
            self.p2 = None
            self.constellation = ''
            self.order = None
            self.other_constellation = ''
            self.complement = None
            self.interpolated_points = []

    def __eq__(self, other):
        return (self.p1 == other.p2 and self.p2 == other.p1) or (self.p1 == other.p1 and self.p2 == other.p2)

    def __str__(self):
        return "Edge({0} {1}: {2} -> {3})".format(self.identifier, self.constellation, self.p1, self.p2)

    def __repr__(self):
        return self.__str__()

    def interpolate_points(self):
        fixed_distance = 1.0

        if self.epoch != 1875.0:
            raise ValueError("Interpolations is only allowed for epoch 1875 boundaries!")
        if self.p1[0] == self.p2[0]:
            # dec is changing
            fixed_value = self.p1[0]
            index = 1
        elif self.p1[1] == self.p2[1]:
            # ra is changing
            fixed_value = self.p1[1]
            index = 0
        else:
            raise ValueError("Only one coordinate can change in an 1875 edge!")

        v1 = self.p1[index]
        v2 = self.p2[index]

        d = v2 - v1
        if abs(d) < 180:
            # No zero crossing (assuming edges never exceed 180)
            if d > 0:
                # Interpolate from v1 to v2 (forward)
                new_values = [v1]
                new_val = fixed_distance * math.ceil(v1 / fixed_distance)
                while new_val < v2:
                    new_values.append(new_val)
                    new_val += fixed_distance
                new_values.append(v2)
            else:
                # Interpolate from v2 to v1 (backward)
                new_values = [v1]
                new_val = fixed_distance * math.floor(v1 / fixed_distance)
                while new_val > v2:
                    new_values.append(new_val)
                    new_val -= fixed_distance
                new_values.append(v2)
        else:
            # Zero crossing
            if d < 0:
                # Interpolate from v1 to v2 (forward), with zero crossing
                new_values = [v1]
                new_val = fixed_distance * math.ceil(v1 / fixed_distance)
                while new_val < v2+360:
                    new_values.append(new_val)
                    new_val += fixed_distance
                new_values.append(v2)
            else:
                # Interpolate from v2 to v2 (backward), with zero crossing
                new_values = [v1]
                new_val = fixed_distance * math.floor(v1 / fixed_distance)
                while new_val+360 >= v2:
                    new_values.append(new_val)
                    new_val -= fixed_distance
                new_values.append(v2)

        if index == 0:
            new_points = [SphericalPoint(v, fixed_value) for v in new_values]
        else:
            new_points = [SphericalPoint(fixed_value, v) for v in new_values]
        return new_points

    def precess(self, date):
        new_epoch = fractional_year(date)
        if not self.interpolated_points:
            self.interpolated_points = self.interpolate_points()

        precessed_points = []
        for p in self.interpolated_points:
            pra, pdec = herget_precession(p.ra, p.dec, self.epoch, new_epoch)
            precessed_points.append(SphericalPoint(pra, pdec))

        self.epoch = new_epoch
        self.p1 = precessed_points[0]
        self.p2 = precessed_points[-1]
        self.interpolated_points = precessed_points


def get_constellation_boundaries(constellation, date=None):
    if date is None:
        date = datetime.date(2000, 1, 1)

    db = SkyMapDatabase()
    q = "SELECT * FROM constellation_boundaries WHERE constellation_boundaries.constellation='{0}' ORDER BY edge_order".format(constellation)
    res = db.query(q)

    result = []
    for row in res:
        e = BoundaryEdge(row)
        e.precess(date)
        result.append(e)

    db.close()
    return result


def get_constellation_boundaries_for_area(min_longitude, max_longitude, min_latitude, max_latitude, date=None, constellation=None):
    if date is None:
        date = datetime.date(2000, 1, 1)

    # Convert longitude to 0-360 values
    min_longitude = ensure_angle_range(min_longitude)
    max_longitude = ensure_angle_range(max_longitude)
    if max_longitude == min_longitude:
        max_longitude += 360

    db = SkyMapDatabase()
    q = "SELECT * FROM constellation_boundaries WHERE"

    if min_longitude < max_longitude:
        q += " ((ra1>={0} AND ra1<={1}".format(min_longitude, max_longitude)
    else:
        q += " (((ra1>={0} OR ra1<={1})".format(min_longitude, max_longitude)

    q += " AND dec1>={0} AND dec1<={1}) OR".format(min_latitude, max_latitude)

    if min_longitude < max_longitude:
        q += " (ra2>={0} AND ra2<={1}".format(min_longitude, max_longitude)
    else:
        q += " ((ra2>={0} OR ra2<={1})".format(min_longitude, max_longitude)

    q += " AND dec2>={0} AND dec2<={1}))".format(min_latitude, max_latitude)

    if constellation is not None:
        q+= " AND constellation='{}'".format(constellation)

    print q
    res = db.query(q)

    result = []
    for row in res:
        e = BoundaryEdge(row)
        e.precess(date)
        result.append(e)

    db.close()
    return result


def get_edge(id):
    db = SkyMapDatabase()
    q = "SELECT * FROM constellation_boundaries WHERE id={}".format(id)
    row = db.query_one(q)
    db.close()
    return BoundaryEdge(row)


def precess(ra, dec, epoch1, epoch2):
    # from epoch1 to 2000.0
    ra = math.radians(ra)
    dec = math.radians(dec)
    cd = math.cos(dec)
    v1 = numpy.array([math.cos(ra) * cd, math.sin(ra) * cd, math.sin(dec)])
    T1 = (epoch1 - REFERENCE_EPOCH).days/36525.0

    X =  0.0007362625 + 0.6405786742 * T1 + 0.00008301386111 * T1**2 + 0.000005005077778 * T1**3 - 0.000000001658611 * T1**4 - 8.813888889e-11 * T1**5
    Z = -0.0007362625 + 0.6405769947 * T1 + 0.0003035374444  * T1**2 + 0.000005074547222 * T1**3 - 0.000000007943333 * T1**4 - 8.066666667e-11 * T1**5
    T =                 0.5567199731 * T1 - 0.0001193037222  * T1**2 - 0.0000116174      * T1**3 - 0.000000001969167 * T1**4 - 3.538888889E-11 * T1**5
    X = math.radians(X)
    Z = math.radians(Z)
    T = math.radians(T)

    CX = math.cos(X)
    SX = math.sin(X)
    CZ = math.cos(Z)
    SZ = math.sin(Z)
    CT = math.cos(T)
    ST = math.sin(T)

    Pinv = numpy.array([
        [ CX * CT * CZ - SX * SZ,  CX * CT * SZ + SX * CZ,  CX * ST],
        [-SX * CT * CZ - CX * SZ, -SX * CT * SZ + CX * CZ, -SX * ST],
        [-ST * CZ,                -ST * SZ,                 CT]
    ])

    v0 = numpy.dot(Pinv, v1)

    # from 2000.0 to date2
    T2 = (epoch2 - REFERENCE_EPOCH).days / 36525.0

    X =  0.0007362625 + 0.6405786742 * T2 + 0.00008301386111 * T2**2 + 0.000005005077778 * T2**3 - 0.000000001658611 * T2**4 - 8.813888889e-11 * T2**5
    Z = -0.0007362625 + 0.6405769947 * T2 + 0.0003035374444  * T2**2 + 0.000005074547222 * T2**3 - 0.000000007943333 * T2**4 - 8.066666667e-11 * T2**5
    T =                 0.5567199731 * T2 - 0.0001193037222  * T2**2 - 0.0000116174      * T2**3 - 0.000000001969167 * T2**4 - 3.538888889E-11 * T2**5
    X = math.radians(X)
    Z = math.radians(Z)
    T = math.radians(T)

    CX = math.cos(X)
    SX = math.sin(X)
    CZ = math.cos(Z)
    SZ = math.sin(Z)
    CT = math.cos(T)
    ST = math.sin(T)

    P = numpy.array([
        [CX * CT * CZ - SX * SZ, -SX * CT * CZ - CX * SZ, -ST * CZ],
        [CX * CT * SZ + SX * CZ, -SX * CT * SZ + CX * CZ, -ST * SZ],
        [CX * ST,                -SX * ST,                 CT]
    ])

    v2 = numpy.dot(P, v0)

    ra2 = math.atan2(v2[1], v2[0])
    if ra2 < 0:
        ra2 += 2 * math.pi
    dec2 = math.asin(v2[2])

    return math.degrees(ra2), math.degrees(dec2)


def herget_precession(ra1, dec1, epoch1, epoch2):
    # ra1 and dec1 in degrees, epoch1 and epoch2 in years AD
    ra1 = math.radians(ra1)
    dec1 = math.radians(dec1)
    cdr = 0.17453292519943e-01

    # Compute input direction cosines
    a = math.cos(dec1)
    x1 = [a * math.cos(ra1), a * math.sin(ra1), math.sin(dec1)]

    # Set up rotation matrix
    ep1 = epoch1
    ep2 = epoch2
    csr = cdr/3600.0
    t = 0.001 * (ep2 - ep1)
    st = 0.001 * (ep1 - 1900.0)
    a = csr * t * (23042.53 + st * (139.75 + 0.06 * st) + t * (30.23 - 0.27 * st + 18.0 * t))
    b = csr * t * t * (79.27 + 0.66 * st + 0.32 * t) + a
    c = csr * t * (20046.85 - st * (85.33 + 0.37 * st) + t * (-42.67 - 0.37 * st - 41.8 * t))
    sina = math.sin(a)
    sinb = math.sin(b)
    sinc = math.sin(c)
    cosa = math.cos(a)
    cosb = math.cos(b)
    cosc = math.cos(c)

    r = [[None for i in range(3)] for j in range(3)]

    r[0][0] = cosa * cosb * cosc - sina * sinb
    r[0][1] = -cosa * sinb - sina * cosb * cosc
    r[0][2] = -cosb * sinc
    r[1][0] = sina * cosb + cosa * sinb * cosc
    r[1][1] = cosa * cosb - sina * sinb * cosc
    r[1][2] = -sinb * sinc
    r[2][0] = cosa * sinc
    r[2][1] = -sina * sinc
    r[2][2] = cosc

    # Perform the rotation to get the direction cosines at epoch2
    x2 = [0.0, 0.0, 0.0]
    for i in range(3):
        for j in range(3):
            x2[i] += r[i][j] * x1[j]

    ra2 = math.atan2(x2[1], x2[0])
    if ra2 <  0:
        ra2 += 2*math.pi
    dec2 = math.asin(x2[2])
    return math.degrees(ra2), math.degrees(dec2)


def build_constellation_database():
    print("")
    print("Building constellation boundary database")

    # Download data file
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE))
        print("Downloading {0}".format(URL))
        urllib.urlretrieve(URL, DATA_FILE)

    # Read data
    with open(DATA_FILE, "r") as fp:
        lines = fp.readlines()

    print("Collecting points")
    # Collect all points
    point_data = {}
    npoints = 0
    for l in lines:
        if not l.strip():
            continue
        npoints += 1
        parts = [x.strip() for x in l.split()]
        ra = 360.0*float(parts[0])/24.0
        dec = float(parts[1])
        constellation = parts[2].lower()

        if constellation not in point_data.keys():
            point_data[constellation] = []
        point_data[constellation].append(SphericalPoint(ra, dec))

    print("Building edges")
    # Build edges from points
    all_edges = []
    for c, points in point_data.items():
        prev_point = points[-1]

        for n, p in enumerate(points):
            if n == 0:
                order = len(points)
            else:
                order = n

            edge = BoundaryEdge()
            edge.identifier = len(all_edges)+1
            edge.p1 = prev_point
            edge.p2 = p
            edge.constellation = c
            edge.order = order

            prev_point = p

            # Fix octans problems
            if c == 'oct':
                if order in [1, 13, 14]:
                    continue
                if order == 12:
                    edge.p2.dec = -82.5

            all_edges.append(edge)

    print("Filling database")

    # Create the table
    db = SkyMapDatabase()

    db.drop_table("constellation_boundaries")

    db.commit_query("""CREATE TABLE constellation_boundaries (
                        id INT PRIMARY KEY ,
                        constellation TEXT,
                        other_constellation TEXT,
                        ra1 REAL,
                        dec1 REAL,
                        ra2 REAL,
                        dec2 REAL,
                        complement INT,
                        edge_order INT
    )""")

    # Fill the table
    nedges = len(all_edges)
    for i, edge in enumerate(all_edges):
        sys.stdout.write("\r{0:.1f}%".format(100.0*i/(nedges-1)))
        sys.stdout.flush()
        q = """INSERT INTO constellation_boundaries VALUES ({0}, "{1}", "{2}", {3}, {4}, {5}, {6}, {7}, {8})""".format(edge.identifier, edge.constellation, edge.other_constellation, edge.p1.ra, edge.p1.dec, edge.p2.ra, edge.p2.dec, edge.complement or "NULL", edge.order)
        db.commit_query(q)

    print("")
    print("Pairing edges")
    pair_edges(db)

    db.close()


def pair_edges(db):
    q = "SELECT * FROM constellation_boundaries ORDER BY id ASC"
    res = db.query(q)

    all_edges = []
    unpaired_edges = []

    for row in res:
        e = BoundaryEdge(row)

        if all_edges:
            sys.stdout.write("\r{0} - {1}/{2} ({3:.1f}%)".format(e.constellation, len(unpaired_edges), len(all_edges), 100.0*len(unpaired_edges)/len(all_edges)))
            sys.stdout.flush()

        try:
            i = unpaired_edges.index(e)
        except ValueError:
            all_edges.append(e)
            unpaired_edges.append(e)
            continue

        complement = unpaired_edges[i]
        e.other_constellation = complement.constellation
        e.complement = complement.identifier
        all_edges[complement.identifier-1].other_constellation = e.constellation
        all_edges[complement.identifier-1].complement = e.identifier
        unpaired_edges.remove(complement)
        all_edges.append(e)

    if not unpaired_edges:
        for e in all_edges:
            q = "UPDATE constellation_boundaries SET complement={0}, other_constellation='{1}' WHERE id={2}".format(e.complement, e.other_constellation, e.identifier)
            db.commit_query(q)
    else:
        print("")
        print("Unpaired edges left over:")
        print(unpaired_edges)


if __name__ == "__main__":
    # import time
    # from skymap.stars import Star
    #
    # db = SkyMapDatabase()
    #
    # s = Star(db.query_one("SELECT * FROM dummy WHERE proper_name='Acrux'"))
    # print CONSTELLATIONS[determine_constellation(s.right_ascension, s.declination, db)]

    ra1 = 0
    dec1 = 90

    e0 = datetime.datetime(2000, 1, 1).date()

    e1 = datetime.datetime(1700, 1, 1).date()
    print precess(ra1, dec1, e0, e1)
    e1 = datetime.datetime(1800, 1, 1).date()
    print precess(ra1, dec1, e0, e1)
    e1 = datetime.datetime(1900, 1, 1).date()
    print precess(ra1, dec1, e0, e1)
    e1 = datetime.datetime(2100, 1, 1).date()
    print precess(ra1, dec1, e0, e1)
    e1 = datetime.datetime(2200, 1, 1).date()
    print precess(ra1, dec1, e0, e1)
    e1 = datetime.datetime(2300, 1, 1).date()
    print precess(ra1, dec1, e0, e1)




