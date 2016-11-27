import sys
import sqlite3
import os
import math
import datetime
import time
import urllib

DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "constellation_boundaries")
DATA_FILE = os.path.join(DATA_FOLDER, "bound_18.dat")
DATABASE_FILE = os.path.join(DATA_FOLDER, "constellation_boundaries.db")
URL = "ftp://cdsarc.u-strasbg.fr/pub/cats/VI/49/bound_18.dat"


def connect(wipe=False):
    if wipe and os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    return conn, cursor


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


class SphericalPoint(object):
    def __init__(self, ra, dec):
        self.ra = ra
        self.dec = dec

    def __str__(self):
        return "({0}, {1})".format(self.ra, self.dec)

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, item):
        return (self.ra, self.dec)[item]

    @property
    def x(self):
        return self.ra

    @property
    def y(self):
        return self.dec

    def __eq__(self, other):
        return (self.ra == other.ra or self.ra+360.0 == other.ra or self.ra-360.0 == other.ra) and self.dec == other.dec


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

    def interpolate_points(self, fixed_distance=1.0):
        # TODO: Include check for RA arcs larger than e.g. 180 deg to allow for zero-crossings
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

        if v2 < v1:
            invert = True
            v1, v2 = v2, v1
        else:
            invert = False

        # Prevent problems at 360 to 0 discontinuity
        d = abs(v2-v1)
        if v2>v1:
            d2 = abs(v2-v1-360)
            newv1, newv2 = v1+360, v2
        else:
            d2 = abs(v2-v1+360)
            newv1, newv2 = v1, v2+360
        if d2 < d:
            v1, v2 = newv1, newv2

        new_values = [v1]

        new_val = fixed_distance*math.ceil(v1/fixed_distance)
        while new_val < v2:
            if new_val>=360:
                new_values.append(new_val-360)
            else:
                new_values.append(new_val)
            new_val += fixed_distance
        new_values.append(v2)

        if invert:
            new_values.reverse()

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

    conn, cursor = connect()
    q = "SELECT * FROM constellation_boundaries WHERE constellation_boundaries.constellation='{0}' ORDER BY edge_order".format(constellation)
    res = cursor.execute(q)

    result = []
    columns = [x[0] for x in res.description]
    for row in res:
        row = dict(zip(columns, row))
        e = BoundaryEdge(row)
        e.precess(date)
        result.append(e)
    conn.close()

    return result


def get_constellation_boundaries_for_area(min_longitude, max_longitude, min_latitude, max_latitude, date=None):
    if date is None:
        date = datetime.date(2000, 1, 1)

    # Inverse precession to 1875
    min_longitude, min_latitude = herget_precession(min_longitude, min_latitude, fractional_year(date), 1875.0)
    max_longitude, max_latitude = herget_precession(max_longitude, max_latitude, fractional_year(date), 1875.0)

    conn, cursor = connect()
    q = "SELECT * FROM constellation_boundaries WHERE"

    if min_longitude < max_longitude:
        q += " (ra1>{0} AND ra1<{1}".format(min_longitude, max_longitude)
    else:
        q += " (ra1>{0} OR ra1<{1}".format(min_longitude, max_longitude)

    q += " AND dec1>{0} AND dec1<{1}) OR".format(min_latitude, max_latitude)

    if min_longitude < max_longitude:
        q += " (ra2>{0} AND ra2<{1}".format(min_longitude, max_longitude)
    else:
        q += " (ra2>{0} OR ra2<{1}".format(min_longitude, max_longitude)

    q += " AND dec2>{0} AND dec2<{1})".format(min_latitude, max_latitude)

    res = cursor.execute(q)

    result = []
    columns = [x[0] for x in res.description]
    for row in res:
        row = dict(zip(columns, row))
        e = BoundaryEdge(row)
        e.precess(date)
        result.append(e)
    conn.close()

    return result


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

            all_edges.append(edge)

    print
    print "Edge construction complete"

    # Create the table
    conn, cursor = connect(wipe=True)
    cursor.execute("""CREATE TABLE constellation_boundaries (
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
    conn.commit()

    # Fill the table
    nedges = len(all_edges)
    for i, edge in enumerate(all_edges):
        sys.stdout.write("\r{0:.1f}%".format(100.0*i/(nedges-1)))
        sys.stdout.flush()
        q = """INSERT INTO constellation_boundaries VALUES ({0}, "{1}", "{2}", {3}, {4}, {5}, {6}, {7}, {8})""".format(edge.identifier, edge.constellation, edge.other_constellation, edge.p1.ra, edge.p1.dec, edge.p2.ra, edge.p2.dec, edge.complement or "NULL", edge.order)
        cursor.execute(q)
        conn.commit()
    conn.close()
    print


def pair_edges():
    conn, cursor = connect()
    q = "SELECT * FROM constellation_boundaries ORDER BY id ASC"
    res = cursor.execute(q)
    columns = [x[0] for x in res.description]

    all_edges = []
    unpaired_edges = []

    for row in res:
        d = dict(zip(columns, row))
        e = BoundaryEdge(d)

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
            cursor.execute(q)
            conn.commit()


