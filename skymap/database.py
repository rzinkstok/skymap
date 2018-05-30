import mysql.connector
DATA_TYPES = {int: "INT", str: "VARCHAR(512)", float: "DOUBLE"}


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
        datatypes = [DATA_TYPES[x] for x in datatypes]
        q = """CREATE TABLE {} (""".format(tablename)
        if create_primary_key:
            q += """pk INT AUTO_INCREMENT, """

        for c, t in zip(columns, datatypes):
            q += """`{}` {}, """.format(c, t)
        q += """PRIMARY KEY (pk))"""
        self.commit_query(q)

    def add_index(self, table, column, name=None, unique=False):
        if name is None:
            name = column
        q = """ALTER TABLE `{}` ADD """.format(table)
        if unique:
            q += """UNIQUE """
        q += """INDEX `{}` (`{}`)""".format(name, column)
        self.commit_query(q)

    def add_multiple_column_index(self, table, columns, name, unique=False):
        q = """ALTER TABLE `{}` ADD """.format(table)
        if unique:
            q += """UNIQUE """
        q += """INDEX `{}` ({})""".format(name, "`" + "`, `".join(columns) + "`")
        self.commit_query(q)

    def drop_table(self, table):
        try:
            self.cursor.execute("""DROP TABLE {0}""".format(table))
            self.conn.commit()
        except mysql.connector.errors.ProgrammingError:
            pass

    def insert_row(self, table, columns, values):
        q = """INSERT INTO {} (""".format(table)
        for c in columns:
            q += """`{}`, """.format(c)
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
