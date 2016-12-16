import os
import re

from skymap.database import SkyMapDatabase
from skymap.geometry import HourAngle, DMSAngle, SphericalPoint

DATA_FOLDER = os.path.dirname(os.path.realpath(__file__))
URL = "http://www.skymap.com/files/overlays/milky.zip"


def parse_file(file_path, db, curve_id, point_id):
    with open(file_path, "r") as fp:
        lines = fp.readlines()

    for l in lines:
        l = l.strip()
        if not l or l.startswith(";"):
            continue

        if l.startswith("MOVE"):
            curve_id += 1
            p = extract_point(l)
            q = """INSERT INTO milkyway VALUES ({0}, "{1}", "{2}", {3})""".format(point_id, curve_id, p.longitude, p.latitude)
        elif l.startswith("DRAW"):
            p = extract_point(l)
            q = """INSERT INTO milkyway VALUES ({0}, "{1}", "{2}", {3})""".format(point_id, curve_id, p.longitude, p.latitude)
        else:
            continue
        db.commit_query(q)
        point_id += 1

    return curve_id, point_id


def extract_point(line):
    point_pattern = "^[A-Z]+\s(\d\d \d\d \d\d), (\-?)(\d\d \d\d)$"
    m = re.search(point_pattern, line)
    try:
        long = m.groups()[0]
        latsign = m.groups()[1]
        lat = m.groups()[2]

        if latsign == "-":
            latsign = -1
        else:
            latsign = 1

        h, m, s = (int(x) for x in long.split())
        longitude = HourAngle(h, m, s).to_degrees()

        d, m = (int(x) for x in lat.split())
        latitude = DMSAngle(degrees=d, minutes=m, sign=latsign).to_degrees()

        return SphericalPoint(longitude, latitude)
    except AttributeError:
        return None


def get_milky_way_curve(id):
    db = SkyMapDatabase()
    q = "SELECT * FROM milkyway WHERE curve_id={0} ORDER BY id ASC".format(id)
    result = db.query(q)
    curve = []
    for row in result:
        curve.append(SphericalPoint(row['ra'], row['dec']))
    if curve[0] == curve[-1]:
        curve = curve[:-1]
    db.close()
    return curve


def get_milky_way_north_boundary():
    return get_milky_way_curve(2)


def get_milky_way_south_boundary():
    return get_milky_way_curve(1)


def get_milky_way_holes():
    curves = []
    for i in (3, 4, 5, 6):
        curves.append(get_milky_way_curve(i))
    return curves


def get_magellanic_clouds():
    curves = []
    for i in (7, 8, 9):
        curves.append(get_milky_way_curve(i))
    return curves


def build_milkyway_database():
    print("")
    print("Building milky way boundary database")

    db = SkyMapDatabase()

    # Drop table
    db.drop_table("milkyway")

    # Create table
    db.commit_query("""CREATE TABLE milkyway (
                            id INT PRIMARY KEY ,
                            curve_id INT,
                            ra REAL,
                            dec REAL
        )""")

    # Fill table
    point_id = 0
    curve_id = 0
    curve_id, point_id = parse_file(os.path.join(DATA_FOLDER, "milkyway.txt"), db, curve_id, point_id)
    curve_id, point_id = parse_file(os.path.join(DATA_FOLDER, "magellanic_clouds.txt"), db, curve_id, point_id)

    db.close()
