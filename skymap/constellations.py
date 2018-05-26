import math
import random

from astropy.coordinates import get_constellation
from astroquery.vizier import Vizier
from skymap.database import SkyMapDatabase
from skymap.geometry import ensure_angle_range, SkyCoordDeg, TOLERANCE
from skymap.coordinates import REFERENCE_EPOCH


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
CONST_BOUND_EPOCH = "B1875"


def constellations_in_area(min_longitude, max_longitude, min_latitude, max_latitude, nsamples=1000):
    """Generates a list of all constellations that overlap with the given area.

    Uses a simple Monte Carlo strategy.
    """
    constellations = {}

    sum_weight = 0
    for i in range(nsamples):
        # Generate a random longitude and latitude pair inside the bounding box
        longitude = min_longitude + (max_longitude - min_longitude) * random.random()
        latitude = min_latitude + (max_latitude - min_latitude) * random.random()

        # Retrieve the short name of the constellation for that coordinate
        constellation = get_constellation(SkyCoordDeg(longitude, latitude), short_name=True)

        # Use the cosine of the latitude as weight, so higher latitude areas are not dominating
        weight = math.cos(math.radians(latitude))

        # Update the constellation dict and sum_weight
        if constellation not in constellations:
            constellations[constellation] = weight
        else:
            constellations[constellation] += weight
        sum_weight += weight

    # Sort the constellation dict by value and return the constellations of decreasing area
    res = sorted([(v/sum_weight, k) for k, v in constellations.items()], reverse=True)
    return [x[1] for x in res]


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
    for row in res:
        p1 = SkyCoordDeg(row['ra1'], row['dec1'])
        p2 = SkyCoordDeg(row['ra2'], row['dec2'])
        e = ConstellationBoundaryEdge(p1, p2)
        e.precess()
        result.append(e)

    db.close()
    return result


# Constellation boundaries
class ConstellationBoundaryEdge(object):
    def __init__(self, p1, p2):
        self.epoch = CONST_BOUND_EPOCH

        self.coord1 = p1
        self.coord2 = p2
        self.interpolated_points = []

        if abs(self.coord1.ra.degree - self.coord2.ra.degree) < TOLERANCE:
            self.direction =  "parallel"
        elif abs(self.coord1.dec.degree - self.coord2.dec.degree) < TOLERANCE:
            self.direction = "meridian"
        raise ValueError("Edge is slanted")

    def __eq__(self, other):
        eq = (self.coord1 == other.coord1 and self.coord2 == other.coord2)
        eq_inv = (self.coord1 == other.coord2 and self.coord2 == other.coord1)
        return eq or eq_inv

    def __str__(self):
        return "Edge({0} -> {1})".format(self.coord1, self.coord2)

    def __repr__(self):
        return self.__str__()

    def interpolate_points(self, step=1.0):
        if self.epoch != CONST_BOUND_EPOCH:
            raise ValueError("Interpolations is only allowed for epoch 1875.0 boundaries!")

        if self.direction == "parallel":
            # dec is changing
            fixed_value = self.coord1.ra.degree
            v1 = self.coord1.dec.degree
            v2 = self.coord2.dec.degree
        elif self.direction == "meridian":
            # ra is changing
            fixed_value = self.coord1.dec.degree
            v1 = self.coord1.ra.degree
            v2 = self.coord2.ra.degree
        else:
            raise ValueError("Only one coordinate can change in an 1875 edge!")

        d = v2 - v1
        if abs(d) < 180:
            # No zero crossing (assuming edges never exceed 180)
            if d > 0:
                # Interpolate from v1 to v2 (forward)
                new_values = [v1]
                new_val = step * math.ceil(v1 / step)
                while new_val < v2:
                    new_values.append(new_val)
                    new_val += step
                new_values.append(v2)
            else:
                # Interpolate from v2 to v1 (backward)
                new_values = [v1]
                new_val = step * math.floor(v1 / step)
                while new_val > v2:
                    new_values.append(new_val)
                    new_val -= step
                new_values.append(v2)
        else:
            # Zero crossing
            if d < 0:
                # Interpolate from v1 to v2 (forward), with zero crossing
                new_values = [v1]
                new_val = step * math.ceil(v1 / step)
                while new_val < v2+360:
                    new_values.append(new_val)
                    new_val += step
                new_values.append(v2)
            else:
                # Interpolate from v2 to v2 (backward), with zero crossing
                new_values = [v1]
                new_val = step * math.floor(v1 / step)
                while new_val+360 >= v2:
                    new_values.append(new_val)
                    new_val -= step
                new_values.append(v2)

        if self.direction == "parallel":
            self.interpolated_points = [SkyCoordDeg(v, fixed_value) for v in new_values]
        else:
            self.interpolated_points = [SkyCoordDeg(fixed_value, v) for v in new_values]
        return self.interpolated_points

    def precess(self, frame="icrs"):
        if not self.interpolated_points:
            self.interpolate_points()

        precessed_points = []
        for p in self.interpolated_points:
            precessed_points.append(p.transform_to(frame))

        self.epoch = precessed_points[0].frame
        self.coord1 = precessed_points[0]
        self.coord2 = precessed_points[-1]
        self.interpolated_points = precessed_points


# Build constellation boundary database

def point_hash(x, y, mult=1e5):
    hx = int(round(x * mult))
    hy = int(round((y + 90.0) * mult))
    return int("{:08d}{:08d}".format(hx, hy))


def point_unhash(h, mult=1e5):
    hstr = "{:016d}".format(h)
    x = int(hstr[:8])/mult
    y = int(hstr[8:])/mult - 90.0
    return x, y


class QuickEdge(object):
    def __init__(self, h1, h2):
        self.h1 = h1
        self.h2 = h2
        self.h1str = "{:016d}".format(h1)
        self.h2str = "{:016d}".format(h2)
        self.ra1 = int(self.h1str[:8])
        self.ra2 = int(self.h2str[:8])
        self.dec1 = int(self.h1str[8:])
        self.dec2 = int(self.h2str[8:])

        self.connected_edge1 = None
        self.connected_edge2 = None

        if self.ra1 == self.ra2:
            self.direction = "parallel"
        elif self.dec1 == self.dec2:
            self.direction = "meridian"
        else:
            raise ValueError("Edge is slanted")

        self.hash = "{}{}".format(*sorted([self.h1str, self.h2str]))

    @property
    def coordinates(self):
        ra1, dec1 = point_unhash(self.h1)
        ra2, dec2 = point_unhash(self.h2)
        return float(ra1), float(dec1), float(ra2), float(dec2)

    def connect(self, other):
        if self.direction != other.direction:
            return

        if self.h1 == other.h1:
            self.connected_edge1 = other
            other.connected_edge1 = self
        elif self.h1 == other.h2:
            self.connected_edge1 = other
            other.connected_edge2 = self
        elif self.h2 == other.h1:
            self.connected_edge2 = other
            other.connected_edge1 = self
        elif self.h2 == other.h2:
            self.connected_edge2 = other
            other.connected_edge2 = self

    @property
    def extended_edge(self):
        extended_h1 = self.h1
        next_edge = self.connected_edge1

        while next_edge is not None:
            if next_edge.h1 == extended_h1:
                extended_h1 = next_edge.h2
                next_edge = next_edge.connected_edge2
            else:
                extended_h1 = next_edge.h1
                next_edge = next_edge.connected_edge1
            if (next_edge is not None) and (next_edge == self):
                raise ValueError("Closed circular edge for {}".format(self))

        extended_h2 = self.h2
        next_edge = self.connected_edge2

        while next_edge is not None:
            if next_edge.h1 == extended_h2:
                extended_h2 = next_edge.h2
                next_edge = next_edge.connected_edge2
            else:
                extended_h2 = next_edge.h1
                next_edge = next_edge.connected_edge1

            if (next_edge is not None) and (next_edge == self):
                raise ValueError("Closed circular edge for {}".format(self))

        total_edge = QuickEdge(extended_h1, extended_h2)
        return total_edge

    def __eq__(self, other):
        return self.hash == other.hash

    def __ne__(self, other):
        return not self.__eq__(other)


def build_constellation_boundary_database():
    print
    print "Creating constellation boundary database"
    db = SkyMapDatabase()
    db.drop_table("skymap_constellation_boundaries")
    db.create_table("skymap_constellation_boundaries", ["ra1", "dec1", "ra2", "dec2"], [float, float, float, float])

    # Retrieve data from Vizier
    print
    print "Retrieving data from Vizier"
    Vizier.ROW_LIMIT = -1
    catalog = Vizier.get_catalogs("VI/49")
    constbnd = catalog['VI/49/constbnd']

    print
    print "Building edges from {} points".format(len(constbnd))
    prev_hash = None
    edges = []
    for row in constbnd:
        if not row['adj']:
            prev_hash = None

        current_hash = point_hash(row['RAB1875'], row['DEB1875'])
        if prev_hash is not None:
            e = QuickEdge(prev_hash, current_hash)

            if e not in edges:
                edges.append(e)

        prev_hash = current_hash

    print
    print "Connecting {} edges".format(len(edges))
    for i, e1 in enumerate(edges):
        for e2 in edges[i+1:]:
            e1.connect(e2)

    print
    print "Building extended edges"
    new_edges = []
    for i, e in enumerate(edges):
        new_edge = e.extended_edge
        if new_edge not in new_edges:
            new_edges.append(new_edge)

    print
    print "Loading {} edges to database".format(len(new_edges))
    for i, e in enumerate(new_edges):
        db.insert_row("skymap_constellation_boundaries", ["ra1", "dec1", "ra2", "dec2"], e.coordinates)


if __name__ == "__main__":
    build_constellation_boundary_database()



