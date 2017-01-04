import os
import mysql.connector


DATA_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "data")
DATABASE_FILE = os.path.join(DATA_FOLDER, "skymap.db")
DATATYPES = {int: "INT", str: "VARCHAR(512)", float: "FLOAT"}


class SkyMapDatabase(object):
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        self.conn = mysql.connector.connect(user='skymap', host='127.0.0.1', database='skymap')
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()

    def create_table(self, tablename, columns, datatypes, create_primary_key=True):
        datatypes = [DATATYPES[x] for x in datatypes]
        q = """CREATE TABLE {} (""".format(tablename)
        if create_primary_key:
            q += """pk INT AUTO_INCREMENT, """

        for c, t in zip(columns, datatypes):
            q += """`{}` {}, """.format(c, t)
        q += """PRIMARY KEY (pk))"""
        self.commit_query(q)

    def add_index(self, table, column):
        self.commit_query("""ALTER TABLE `{}` ADD INDEX `{}` (`{}`)""".format(table, column, column))

    def drop_table(self, table):
        try:
            self.cursor.execute("""DROP TABLE {0}""".format(table))
            self.conn.commit()
        except mysql.connector.errors.ProgrammingError:
            pass

    def insert_row(self, table, columns, values):
        q = """INSERT INTO {} (""".format(table)
        for c in columns:
            q += """"`{}`, """.format(c)
        q = q[:-2] + """) VALUES ("""
        for v in values:
            q += """%s, """
        q = q[:-2] + """)"""
        self.commit_query(q, values)

    def insert_rows(self, table, columns, values_batch):
        q = """INSERT INTO {} (""".format(table)
        for c in columns:
            q += """`{}`, """.format(c)
        q = q[:-2] + """) VALUES """
        params = []
        for values in values_batch:
            q += """(""" + """%s, """ * len(values)
            q = q[:-2] + """), """
            params.extend(values)
        q = q[:-2]
        self.commit_query(q, params)

    def query(self, q, params=(), fetch=True):
        self.cursor.execute(q, params)
        if fetch:
            rows = self.cursor.fetchall()
            columns = [x[0] for x in self.cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def query_one(self, q, params=()):
        rows = self.query(q, params)
        try:
            return rows[0]
        except IndexError:
            return None

    def commit_query(self, q, params=()):
        self.cursor.execute(q, params)
        self.conn.commit()


if __name__ == "__main__":
    pass
    # from skymap.milkyway import build_milkyway_database
    # from skymap.labels import build_label_database

    # build_constellation_database()
    # build_hipparcos_database()
    # build_hyg_database()
    # build_milkyway_database()
    # build_label_database()
    # build_star_designation_database()
    # build_tycho_database()
