import os
import sys
import re
import time
import ftplib
import urllib
import gzip
from functools import partial

from skymap.database import SkyMapDatabase


VIZIER_SERVER = "cdsarc.u-strasbg.fr"
DATA_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "data")
BYTE_PATTERN = re.compile("^\s*(\d+)(\-\s*(\d+))?\s+(([A-Z])\d*(\.\d+)?)\s+\S+\s+(\S+)\s")
VIZIER_FORMATS = {"I": int, "A": str, "F": float}


def parse_readme(foldername):
    filepath = os.path.join(DATA_FOLDER, foldername, "ReadMe")
    with open(filepath) as fp:
        lines = fp.readlines()

    current_files = []
    datadict = []
    datadicts = {}

    for l in lines:
        if l.startswith("Byte-by-byte Description of file:") or l.startswith("Byte-per-byte Description of file:"):
            files_l = l.split(":")[-1].strip()
            if "," in files_l:
                current_files = [x.strip() for x in files_l.split(",")]
            elif " " in files_l:
                current_files = [x.strip() for x in files_l.split(" ")]
            else:
                current_files = [files_l]

        if current_files:
            if not l.strip():
                for f in current_files:
                    datadicts[f] = datadict
                current_files = []
                datadict = []
            else:
                m = re.match(BYTE_PATTERN, l)
                if m:
                    g = m.groups()
                    d = {}
                    d['startbyte'] = int(g[0]) - 1
                    if g[2] is not None:
                        d['stopbyte'] = int(g[2])
                    else:
                        d['stopbyte'] = int(g[0])

                    d['format'] = VIZIER_FORMATS[g[4]]
                    d['label'] = g[6]
                    datadict.append(d)

    # for f, dds in datadicts.items():
    #     print
    #     print f
    #     for dd in dds:
    #         print dd

    return datadicts


def parse_datafile(db, foldername, filename, table, datadicts, columns):
    print
    print "Parsing", filename

    filepath = os.path.join(DATA_FOLDER, foldername, filename)
    ext = os.path.splitext(filepath)[-1]
    if ext in ['.z', '.gz']:
        fp = gzip.open(filepath)
        rewind = fp.rewind
    elif ext == ".dat":
        fp = open(filepath)
        rewind = partial(fp.seek, 0)
    else:
        raise IOError("Unsupported file type {}".format(ext))

    # Read number of records and rewind to start
    nrecords = len(fp.readlines())
    rewind()

    batchsize = 1000
    batch = []
    for i, line in enumerate(fp):
        sys.stdout.write("\r{0:.1f}%".format(i * 100.0 / (nrecords - 1)))
        sys.stdout.flush()
        values = []
        for d in datadicts:
            s = line[d['startbyte']:d['stopbyte']]
            if s and s[-1] == "\n":
                s = s[:-1]
            t = d['format']
            if not s and t is not str:
                v = None
            else:
                try:
                    v = t(s)
                except ValueError:
                    v = None
                # if t == str:
                #     v = v.rstrip("\n")
            values.append(v)
        batch.append(values)
        if len(batch) == batchsize:
            db.insert_rows(table, columns, batch)
            batch = []
    if batch:
        db.insert_rows(table, columns, batch)


def get_files(catalogue, foldername):
    destfolder = os.path.join(DATA_FOLDER, foldername)
    if not os.path.exists(destfolder):
        os.makedirs(destfolder)

    ftp = ftplib.FTP(VIZIER_SERVER)
    ftp.login()
    ftp.cwd("pub/cats/{}/".format(catalogue))
    lines = []
    ftp.retrlines('LIST', lines.append)

    files = []
    for l in lines:
        l = l.strip()
        if l.startswith("d"):
            # Skip directories
            continue
        if l.startswith("l"):
            # Skip links
            continue
        f = l.split()[-1].strip()
        files.append(f)
        destfile = os.path.join(destfolder, f)
        if os.path.exists(destfile):
            print "Already downloaded:", f
            continue
        print "Downloading", f
        ftp.retrbinary('RETR {}'.format(f), open(destfile, 'wb').write)
    ftp.quit()
    return files


def build_database(catalogue, foldername, indices=(), extra_function=None):
    print
    print "Building database for {} ({})".format(catalogue, foldername)
    t1 = time.time()
    files = get_files(catalogue, foldername)

    datadicts = parse_readme(foldername)
    db = SkyMapDatabase()
    for f, dds in datadicts.items():
        table = "{}_{}".format(foldername, f.split(".")[0])
        db.drop_table(table)

        columns = []
        lc_columns = []
        datatypes = []
        for dd in dds:
            c = dd["label"]

            # Check for columns that have equivalent names
            i = 1
            while c.lower() in lc_columns:
                if i == 1:
                    c += "_1"
                else:
                    c = c[:-2] + "_{}".format(i)
                i += 1

            lc_columns.append(c.lower())
            columns.append(c)
            datatypes.append(dd['format'])

        db.create_table(table, columns, datatypes)

        real_files = [fn for fn in files if fn.startswith(f)]
        for real_file in real_files:
            parse_datafile(db, foldername, real_file, table, dds, columns)
        for i in indices:
            if i in columns:
                db.add_index(table, i)

    t2 = time.time()
    print
    print
    print "Time: {} s".format(t2-t1)

    if extra_function:
        extra_function()


def split_tyc():
    db = SkyMapDatabase()
    db.commit_query("""
        ALTER TABLE hiptyc_tyc_main
        ADD COLUMN `TYC1` INT AFTER `TYC`,
        ADD COLUMN `TYC2` INT AFTER `TYC1`,
        ADD COLUMN `TYC3` INT AFTER `TYC2`
    """)
    db.commit_query("""
        UPDATE hiptyc_tyc_main
        SET TYC1=CAST(substr(TYC, 1, 4) AS UNSIGNED), TYC2=CAST(substr(hiptyc_tyc_main.TYC, 5, 6) AS UNSIGNED), TYC3=CAST(substr(hiptyc_tyc_main.TYC, 11, 2) AS UNSIGNED)
    """)
    db.add_index("hiptyc_tyc_main", "TYC1")
    db.add_index("hiptyc_tyc_main", "TYC2")
    db.add_index("hiptyc_tyc_main", "TYC3")


if __name__ == "__main__":
    # build_database("VI/42", "cst_id")
    #build_database("VI/49", "cst_bound")
    #build_database("I/311", "hipnew", indices=["HIP"])

    build_database("I/239", "hiptyc", indices=["HIP"], extra_function=split_tyc)
    # build_database("I/259", "tyc2", indices=["TYC1", "TYC2", "TYC3"])
    # build_database("IV/25", "tyc2hd", indices=["TYC1", "TYC2", "TYC3", "HD"])
    # build_database("IV/27A", "cross_index", indices=["HD"])

    # build_database("I/274", "ccdm")
    # build_database("B/gcvs", "gcvs")
    # build_database("I/276", "tdsc")
    # build_database("VII/118", "ngc")
