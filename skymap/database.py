import os
import sqlite3

DATA_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "data")
DATABASE_FILE = os.path.join(DATA_FOLDER, "skymap.db")


class SkyMapDatabase(object):
    def __init__(self):
        self.connect()

    def connect(self, wipe=False):
        if wipe and os.path.exists(DATABASE_FILE):
            os.remove(DATABASE_FILE)
        self.conn = sqlite3.connect(DATABASE_FILE)
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()

    def drop_table(self, table):
        try:
            self.cursor.execute("""DROP TABLE {0}""".format(table))
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

    def query(self, q):
        result = self.cursor.execute(q)
        rows = result.fetchall()
        columns = [x[0] for x in result.description]
        return [dict(zip(columns, row)) for row in rows]

    def query_one(self, q):
        rows = self.query(q)
        return rows[0]

    def commit_query(self, q):
        self.cursor.execute(q)
        self.conn.commit()



if __name__ == "__main__":
    from hipparcos import build_hipparcos_database
    from hyg import build_hyg_database
    from constellations import build_constellation_database
    from milkyway import build_milkyway_database

    build_constellation_database()
    build_hipparcos_database()
    build_hyg_database()
    build_milkyway_database()