import sys
import os
import math
import numpy
import datetime
import urllib

from skymap.database import SkyMapDatabase
from skymap.geometry import SphericalPoint, ensure_angle_range


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


CONST_BOUND_EPOCH = datetime.datetime(1875, 1, 1).date()
REFERENCE_EPOCH = datetime.datetime(2000, 1, 1).date()

# Precession
class PrecessionCalculator(object):
    def __init__(self, epoch1, epoch2):
        self.epoch1 = epoch1
        self.epoch2 = epoch2

        t1 = (epoch1 - REFERENCE_EPOCH).days / 36525.0
        m1 = self.inverse_rotation_matrix(t1)
        t2 = (epoch2 - REFERENCE_EPOCH).days / 36525.0
        m2 = self.rotation_matrix(t2)
        self.matrix = numpy.dot(m2, m1)

    def zeta(self, t):
        return 0.0007362625 + 0.6405786742 * t + 0.00008301386111 * t ** 2 + 0.000005005077778 * t ** 3 - 0.000000001658611 * t ** 4 - 8.813888889e-11 * t ** 5

    def z(self, t):
        return -0.0007362625 + 0.6405769947 * t + 0.0003035374444 * t ** 2 + 0.000005074547222 * t ** 3 - 0.000000007943333 * t ** 4 - 8.066666667e-11 * t ** 5

    def theta(self, t):
        return 0.5567199731 * t - 0.0001193037222 * t ** 2 - 0.0000116174 * t ** 3 - 0.000000001969167 * t ** 4 - 3.538888889E-11 * t ** 5

    def direction_sines_and_cosines(self, t):
        zeta = math.radians(self.zeta(t))
        z = math.radians(self.z(t))
        theta = math.radians(self.theta(t))

        cx = math.cos(zeta)
        sx = math.sin(zeta)
        cz = math.cos(z)
        sz = math.sin(z)
        ct = math.cos(theta)
        st = math.sin(theta)

        return cx, sx, cz, sz, ct, st

    def inverse_rotation_matrix(self, t):
        cx, sx, cz, sz, ct, st = self.direction_sines_and_cosines(t)
        m = numpy.array([
            [cx * ct * cz - sx * sz, cx * ct * sz + sx * cz, cx * st],
            [-sx * ct * cz - cx * sz, -sx * ct * sz + cx * cz, -sx * st],
            [-st * cz, -st * sz, ct]
        ])
        return m

    def rotation_matrix(self, t):
        cx, sx, cz, sz, ct, st = self.direction_sines_and_cosines(t)
        m = numpy.array([
            [cx * ct * cz - sx * sz, -sx * ct * cz - cx * sz, -st * cz],
            [cx * ct * sz + sx * cz, -sx * ct * sz + cx * cz, -st * sz],
            [cx * st, -sx * st, ct]
        ])
        return m

    def precess(self, ra, dec):
        ra = math.radians(ra)
        dec = math.radians(dec)
        cd = math.cos(dec)
        v1 = numpy.array([math.cos(ra) * cd, math.sin(ra) * cd, math.sin(dec)])

        v2 = numpy.dot(self.matrix, v1)

        ra2 = math.atan2(v2[1], v2[0])
        if ra2 < 0:
            ra2 += 2 * math.pi
        dec2 = math.asin(v2[2])

        return math.degrees(ra2), math.degrees(dec2)


class PointInConstellationPrecession(PrecessionCalculator):
    def __init__(self, epoch=None):
        if epoch is None:
            epoch = REFERENCE_EPOCH
        PrecessionCalculator.__init__(self, epoch, CONST_BOUND_EPOCH)


# Point in constellation determination
def determine_constellation(ra, de, pc, db):
    ra, de = pc.precess(ra, de)
    ra /= 15.0  # Convert to fractional hours of right ascension

    q = """
            SELECT const
            FROM skymap.cst_id_data
            WHERE DE_low < {0} AND RA_low <= {1}  AND RA_up > {1} ORDER BY pk LIMIT 1
        """.format(de, ra)
    return db.query_one(q)['const'].lower()


# Constellation boundaries
class BoundaryEdge(object):
    def __init__(self, p1, p2):
        self.epoch = CONST_BOUND_EPOCH

        self.p1 = p1 #SphericalPoint(row['ra1'], row['dec1'])
        self.p2 = p2 #SphericalPoint(row['ra2'], row['dec2'])
        self.interpolated_points = []
        self.extension1 = None
        self.extension2 = None

    def __eq__(self, other):
        return (self.p1 == other.p2 and self.p2 == other.p1) or (self.p1 == other.p1 and self.p2 == other.p2)

    def __str__(self):
        return "Edge({0} -> {1})".format(self.p1, self.p2)

    def __repr__(self):
        return self.__str__()

    @property
    def direction(self):
        if self.p1[0] == self.p2[0]:
            return "parallel"
        elif self.p1[1] == self.p2[1]:
            return "meridian"
        raise ValueError("Edge is slanted")

    def connect(self, other):
        if self.direction != other.direction:
            return

        if self.p1 == other.p1:
            self.extension1 = other
            other.extension1 = self
        elif self.p1 == other.p2:
            self.extension1 = other
            other.extension2 = self
        elif self.p2 == other.p1:
            self.extension2 = other
            other.extension1 = self
        elif self.p2 == other.p2:
            self.extension2 = other
            other.extension2 = self
        else:
            return

    @property
    def extended_edge(self):
        # print
        # print "------------------------------------------"
        # print "Extending edge for", self
        # print "------------------------------------------"
        # print
        # print "Connection to P1"
        ep1 = self.p1
        ext = self.extension1
        while ext is not None:
            # print ep1, ext
            # print ext.p1, ext.extension1
            # print ext.p2, ext.extension2
            if ext.p1 == ep1:
                ep1 = ext.p2
                ext = ext.extension2
            else:
                ep1 = ext.p1
                ext = ext.extension1
            # print "New point:", ep1
            # print "Next edge:", ext
            if (ext is not None) and (ext == self):
                raise ValueError("Closed circular edge for {}".format(self))
        # print
        # print "Connection to P2"
        ep2 = self.p2
        ext = self.extension2
        while ext is not None:
            # print ep2, ext
            # print ext.p1, ext.extension1
            # print ext.p2, ext.extension2
            if ext.p1 == ep2:
                ep2 = ext.p2
                ext = ext.extension2
            else:
                ep2 = ext.p1
                ext = ext.extension1

            # print "New point:", ep2
            # print "Next edge:", ext
            if (ext is not None) and (ext == self):
                raise ValueError("Closed circular edge for {}".format(self))

        ee = BoundaryEdge(ep1, ep2)
        # print
        # print "Total edge:", ee
        # print "------------------------------------------"
        return ee

    def interpolate_points(self):
        fixed_distance = 1.0

        if self.epoch != CONST_BOUND_EPOCH:
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

    def precess(self, pc):
        if not self.interpolated_points:
            self.interpolated_points = self.interpolate_points()

        precessed_points = []
        for p in self.interpolated_points:
            pra, pdec = pc.precess(p.ra, p.dec)
            precessed_points.append(SphericalPoint(pra, pdec))

        self.epoch = pc.epoch2
        self.p1 = precessed_points[0]
        self.p2 = precessed_points[-1]
        self.interpolated_points = precessed_points


def get_constellation_boundaries_for_area(min_longitude, max_longitude, min_latitude, max_latitude, epoch=REFERENCE_EPOCH):
    # Convert longitude to 0-360 values
    min_longitude = ensure_angle_range(min_longitude)
    max_longitude = ensure_angle_range(max_longitude)
    if max_longitude == min_longitude:
        max_longitude += 360

    db = SkyMapDatabase()
    q = "SELECT * FROM skymap_constellation_boundaries WHERE"

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

    res = db.query(q)

    result = []
    pc = PrecessionCalculator(CONST_BOUND_EPOCH, epoch)
    for row in res:
        p1 = SphericalPoint(row['ra1'], row['dec1'])
        p2 = SphericalPoint(row['ra2'], row['dec2'])
        e = BoundaryEdge(p1, p2)
        e.precess(pc)
        result.append(e)

    db.close()
    return result


def build_constellation_boundary_database():
    print
    print "Building constellation boundary database"
    db = SkyMapDatabase()
    db.drop_table("skymap_constellation_boundaries")
    db.create_table("skymap_constellation_boundaries", ["ra1", "dec1", "ra2", "dec2"], [float, float, float, float])

    edges = []
    rows = db.query("""SELECT * FROM cst_bound_constbnd""")

    print "Creating raw edges"
    prev_point = None
    nrecords = len(rows)
    next_id = 1
    for i, row in enumerate(rows):
        sys.stdout.write("\r{0:.1f}%".format(i * 100.0 / (nrecords - 1)))
        sys.stdout.flush()

        if not row['adj']:
            prev_point = None

        ra = 15.0 * row['RAhr']
        dec = row['DEdeg']
        point = SphericalPoint(ra, dec)

        if prev_point is not None:
            e = BoundaryEdge(prev_point, point)
            if e not in edges:
                edges.append(e)
                next_id += 1

        prev_point = point

    print
    print "Connecting edges"
    n = 0
    nrecords = len(edges) * (len(edges)-1) / 2
    for i, e1 in enumerate(edges):
        for e2 in edges[i+1:]:
            sys.stdout.write("\r{0:.1f}%".format(n * 100.0 / (nrecords - 1)))
            sys.stdout.flush()
            n += 1
            if e1 == e2:
                continue

            e1.connect(e2)

    print
    print "Building extended edges"
    new_edges = []
    nrecords = len(edges)
    for i, e in enumerate(edges):
        sys.stdout.write("\r{0:.1f}%".format(i * 100.0 / (nrecords - 1)))
        sys.stdout.flush()
        new_edge = e.extended_edge
        if new_edge not in new_edges:
            new_edges.append(new_edge)
    print
    nrecords = len(new_edges)
    print "Loading {} edges to database".format(nrecords)

    for i, e in enumerate(new_edges):
        sys.stdout.write("\r{0:.1f}%".format(i * 100.0 / (nrecords - 1)))
        sys.stdout.flush()
        db.insert_row("skymap_constellation_boundaries", ["ra1", "dec1", "ra2", "dec2"], [e.p1.ra, e.p1.dec, e.p2.ra, e.p2.dec])




if __name__ == "__main__":
    from skymap.stars import Star

    e1 = BoundaryEdge(SphericalPoint(0, 0), SphericalPoint(0, 10))
    e2 = BoundaryEdge(SphericalPoint(0, 0), SphericalPoint(0, -20))
    e3 = BoundaryEdge(SphericalPoint(0, 0), SphericalPoint(15, 0))

    e1.connect(e2)
    e1.connect(e3)
    e2.connect(e3)

    print "Edge 1"
    print e1.p1, e1.extension1
    print e1.p2, e1.extension2
    print
    print "Edge 2"
    print e2.p1, e2.extension1
    print e2.p2, e2.extension2
    print
    print "Edge 3"
    print e3.p1, e3.extension1
    print e3.p2, e3.extension2
    print
    print "Combined"
    print e1.extended_edge
    print e2.extended_edge
    print e3.extended_edge

    build_constellation_boundary_database()

    sys.exit()
    db = SkyMapDatabase()

    s = Star(db.query_one("SELECT * FROM dummy WHERE proper_name='Acrux'"))
    pc = PointInConstellationPrecession()
    print CONSTELLATIONS[determine_constellation(s.right_ascension, s.declination, pc, db)]
    print
    ra1 = 0
    dec1 = 90


    e0 = datetime.datetime(2000, 1, 1).date()

    e1 = datetime.datetime(1700, 1, 1).date()
    pc = PrecessionCalculator(e0, e1)
    print pc.precess(ra1, dec1)
    e1 = datetime.datetime(1800, 1, 1).date()
    pc = PrecessionCalculator(e0, e1)
    print pc.precess(ra1, dec1)
    e1 = datetime.datetime(1900, 1, 1).date()
    pc = PrecessionCalculator(e0, e1)
    print pc.precess(ra1, dec1)
    e1 = datetime.datetime(2100, 1, 1).date()
    pc = PrecessionCalculator(e0, e1)
    print pc.precess(ra1, dec1)
    e1 = datetime.datetime(2200, 1, 1).date()
    pc = PrecessionCalculator(e0, e1)
    print pc.precess(ra1, dec1)
    e1 = datetime.datetime(2300, 1, 1).date()
    pc = PrecessionCalculator(e0, e1)
    print pc.precess(ra1, dec1)




