import sys
import math
import datetime
import random

from skymap.database import SkyMapDatabase
from skymap.geometry import SphericalPoint, ensure_angle_range
from skymap.coordinates import REFERENCE_EPOCH, PrecessionCalculator


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


# The epoch for which the constellation boundaries where defined by Delporte
CONST_BOUND_EPOCH = datetime.datetime(1875, 1, 1).date()


class PointInConstellationPrecession(PrecessionCalculator):
    """Convenience class to precess a coordinate to the epoch of the Delporte boundaries."""
    def __init__(self, epoch=None):
        if epoch is None:
            epoch = REFERENCE_EPOCH
        PrecessionCalculator.__init__(self, epoch, CONST_BOUND_EPOCH)


class ConstellationFinder(object):
    """
    Find the constellation for a given coordinate.
    """
    def __init__(self, epoch=None):
        self.db = SkyMapDatabase()
        self.precessor = PointInConstellationPrecession(epoch)

    def find(self, ra, de):
        ra, de = self.precessor.precess(ra, de)
        ra /= 15.0  # Convert to fractional hours of right ascension

        q = """
                SELECT const
                FROM skymap.cst_id_data
                WHERE DE_low < {0} AND RA_low <= {1}  AND RA_up > {1} ORDER BY pk LIMIT 1
            """.format(de, ra)
        return self.db.query_one(q)['const'].lower()


def constellations_in_area(min_longitude, max_longitude, min_latitude, max_latitude, nsamples=1000):
    """
    Generates a list of all constellations that overlap with the given area.
    Uses a simple Monte Carlo strategy.
    """

    constellations = {}
    cf = ConstellationFinder()

    total = 0
    for i in range(nsamples):
        x = min_longitude + (max_longitude - min_longitude) * random.random()
        y = min_latitude + (max_latitude - min_latitude) * random.random()
        c = cf.find(x, y)
        w = math.cos(math.radians(y))
        if c not in constellations:
            constellations[c] = w
        else:
            constellations[c] += w
        total += w

    res = sorted([(v/total, k) for k, v in constellations.items()], reverse=True)
    return [x[1] for x in res]


# Constellation boundaries
class BoundaryEdge(object):
    def __init__(self, p1, p2):
        self.epoch = CONST_BOUND_EPOCH

        self.p1 = p1
        self.p2 = p2
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
    # TODO: sometimes boundaries cross the map but have no vertices within the map area + margin and are not plotted
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
    build_constellation_boundary_database()
