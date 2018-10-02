import time
from skymap.database.vizier import build_stellar_source_databases
from skymap.stars.star_database import build_stellar_database


if __name__ == "__main__":
    t1 = time.time()
    build_stellar_source_databases()
    build_stellar_database()
    t2 = time.time()
    print("Total build time: {:.1f} s".format(t2 - t1))