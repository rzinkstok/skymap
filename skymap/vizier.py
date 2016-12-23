import os
import sys
import re
import ftplib
import gzip
from functools import partial

from skymap.database import SkyMapDatabase


VIZIER_SERVER = "cdsarc.u-strasbg.fr"
DATA_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "data")
BYTE_PATTERN = re.compile("^\s*(\d+)(\-\s*(\d+))?\s+(([A-Z])\d*(\.\d+)?)\s+\S+\s+(\S+)\s")
VIZIER_DB = os.path.join(DATA_FOLDER, "vizier.db")
VIZIER_FORMATS = {"I": int, "A": str, "F": float}


def parse_readme(foldername):
    filepath = os.path.join(DATA_FOLDER, foldername, "ReadMe")
    with open(filepath) as fp:
        lines = fp.readlines()

    current_files = []
    datadict = []
    datadicts = {}

    for l in lines:
        if l.startswith("Byte-by-byte Description of file:"):
            current_files = [x.strip() for x in l.split(":")[-1].split(",")]

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


def parse_datafile(db, foldername, filename, table, datadicts):
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

    for i, line in enumerate(fp):
        sys.stdout.write("\r{0:.1f}%".format(i * 100.0 / (nrecords - 1)))
        sys.stdout.flush()
        values = []
        for d in datadicts:
            s = line[d['startbyte']:d['stopbyte']].strip()
            t = d['format']
            if not s and t is not str:
                v = None
            else:
                try:
                    v = t(s)
                except ValueError:
                    v = None
            values.append(v)
        db.insert_row(table, values)


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


def build_database(catalogue, foldername):
    print
    print "Building database for {} ({})".format(catalogue, foldername)
    files = get_files(catalogue, foldername)
    datadicts = parse_readme(foldername)
    db = SkyMapDatabase(VIZIER_DB)
    for f, dds in datadicts.items():
        table = "{}_{}".format(foldername, f.split(".")[0])
        db.drop_table(table)

        columns = []
        lc_columns = []
        for c in [dd["label"] for dd in dds]:
            i = 1
            while c.lower() in lc_columns:
                if i == 1:
                    c += "_1"
                else:
                    c = c[:-2] + "_{}".format(i)
                i += 1

            lc_columns.append(c.lower())
            columns.append(c)

        datatypes = [dd['format'] for dd in dds]
        db.create_table(table, columns, datatypes)

        real_files = [file for file in files if file.startswith(f)]
        for real_file in real_files:
            parse_datafile(db, foldername, real_file, table, dds)


if __name__ == "__main__":
    #build_database("V/137D", "xhip")
    #build_database("I/259", "tyc2")
    #build_database("IV/27A", "cross_index")
    #build_database("IV/25", "tyc2hd")
    build_database("I/274", "ccdm")
    build_database("B/gcvs", "gcvs")
    build_database("I/239", "hiptyc")
    build_database("I/276", "tdsc")
