import os
import sys
import re
import time
import ftplib
import gzip
from functools import partial

from skymap.database import SkyMapDatabase


VIZIER_SERVER = "cdsarc.u-strasbg.fr"
DATA_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), "data")

# RE pattern to parse the Vizier ReadMe Byte-by-byte description.
# This RE captures the start byte, stop byte, format and label to groups.
# Example line:
# 52- 63  F12.8 deg     RAdeg    *? alpha, degrees (ICRS, Epoch=J1991.25)   (H8)
BYTE_PATTERN = re.compile("^\s*(\d+)(\-\s*(\d+))?\s+(([A-Z])\d*(\.\d+)?)\s+\S+\s+(\S+)\s")

# Vizier only knows 3 data types
VIZIER_FORMATS = {"I": int, "A": str, "F": float}


def parse_readme(foldername):
    """Parses the ReadMe file that should be present in each catalog folder.

    The ReadMe file has a table that defines the record structure of each file
    in the catalog. The record structure definition follows a strictly defined
    convention. For each file in the catalog, his information is parsed into a
    list of column definitions. Each column definition is a dict with the
    following items:

    - startbyte: the first byte of the column data in the data file line
    - stopbyte: the last byte of the column data in the data file line
    - format: the python datatype of the column
    - label: the name of the column

    Args:
        foldername (str): the local folder where the catalog is saved

    Returns:
         dict: a mapping from filename to data definition for that file
    """
    filepath = os.path.join(DATA_FOLDER, foldername, "ReadMe")
    with open(filepath) as fp:
        lines = fp.readlines()

    current_files = []
    datadict = []
    datadicts = {}

    for l in lines:
        if l.startswith("Byte-by-byte Description of file:") or l.startswith("Byte-per-byte Description of file:"):
            # This line lists all files for which the byte-by-byte description is valid.
            # The files can be seperated by a space or a comma.
            files_in_line = l.split(":")[-1].strip()
            current_files = [x.strip() for x in re.split(',| ', files_in_line) if x.strip()]
            continue

        if current_files:
            if not l.strip():
                # End of the byte-by-byte description is reached. Save the datadict for each file in current_files
                # and clear the current files and datadict
                for f in current_files:
                    datadicts[f] = datadict
                current_files = []
                datadict = []
            else:
                m = re.match(BYTE_PATTERN, l)
                if m:
                    # This is a valid column definition line. Parse the data into a columndef and add it to the datadict
                    groups = m.groups()
                    coldef = {}
                    coldef['startbyte'] = int(groups[0]) - 1
                    if groups[2] is not None:
                        coldef['stopbyte'] = int(groups[2])
                    else:
                        coldef['stopbyte'] = int(groups[0])

                    coldef['format'] = VIZIER_FORMATS[groups[4]]
                    coldef['label'] = groups[6]
                    datadict.append(coldef)

    return datadicts


def parse_datafile(db, foldername, filename, table, coldefs, columns):
    """Parses a datafile and inserts the data into the database.

    Args:
        db (skymap.database.SkyMapDatabase): the opened database to write the data to
        foldername (str): the folder where the datafile is located
        table (str): the name of the table to put the data in
        coldefs (list): the column definitions for the data file
        columns (list): the column names of the table
    """
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

    # Loop over all lines, parse the data and add it in batches to the database
    batchsize = 1000
    batch = []
    for i, line in enumerate(fp):
        sys.stdout.write("\r{0:.1f}%".format(i * 100.0 / (nrecords - 1)))
        sys.stdout.flush()
        values = []
        for coldef in coldefs:
            coltype = coldef['format']
            valuestring = line[coldef['startbyte']:coldef['stopbyte']].strip()
            if not valuestring and coltype is not str:
                colvalue = None
            else:
                try:
                    colvalue = coltype(valuestring)
                except ValueError:
                    colvalue = None
            values.append(colvalue)
        batch.append(values)
        if len(batch) == batchsize:
            db.insert_rows(table, columns, batch)
            batch = []
    if batch:
        db.insert_rows(table, columns, batch)


def download_files(catalogue, foldername):
    """Retrieves the files for the given catalog from the Vizier FTP server.

    Args:
        catalogue (str): the name of the catalog
        foldername (str): the folder to save the data to

    Returns:
        list: the filenames of all the files that belong to the catalog
    """
    destfolder = os.path.join(DATA_FOLDER, foldername)
    if not os.path.exists(destfolder):
        os.makedirs(destfolder)

    # Open the FTP connection and retrieve the file list for the catalog
    ftp = ftplib.FTP(VIZIER_SERVER)
    ftp.login()
    ftp.cwd("pub/cats/{}/".format(catalogue))
    lines = []
    ftp.retrlines('LIST', lines.append)

    # Parse the file list and download each file, if it was not already downloaded
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
    """Downloads the datafiles for a catalog and builds a local database for it.

    Args:
        catalogue (str): the name of the catalog
        foldername (str): the folder where to save the data
        indices (list): the columns to generate indices for
        extra_function (function): a function to call after the database is built
    """
    print
    print "Building database for {} ({})".format(catalogue, foldername)
    t1 = time.time()

    files = download_files(catalogue, foldername)
    datadicts = parse_readme(foldername)
    db = SkyMapDatabase()

    for filename, coldefs in datadicts.items():
        datatypes = [coldef['format'] for coldef in coldefs]
        # SQL is case insensitive, and Vizier sometimes has column names in the same file that
        # have equivalent names. So, the column names are checked and updated when needed.
        column_names = []
        for coldef in coldefs:
            column_name = coldef["label"]
            i = 1
            lowercase_column_names = [x.lower() for x in column_names]
            while column_name.lower() in lowercase_column_names:
                if i > 1:
                    column_name = column_name[:-2]
                column_name += "_{}".format(i)
                i += 1

            column_names.append(column_name)

        # Clear the database table
        table = "{}_{}".format(foldername, filename.split(".")[0])
        db.drop_table(table)
        db.create_table(table, column_names, datatypes)

        # For large catalogs, the data can be spread over multiple files, so loop over all files
        real_files = [fn for fn in files if fn.startswith(filename)]
        for real_file in real_files:
            parse_datafile(db, foldername, real_file, table, coldefs, column_names)

        # Add indices
        for ind in indices:
            if ind in column_names:
                db.add_index(table, ind)

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

    db.commit_query("""DROP FUNCTION IF EXISTS SPLIT_TYC""")

    db.commit_query("""
        CREATE FUNCTION SPLIT_TYC(str VARCHAR(255), pos INT) RETURNS INT
        BEGIN
            SET str = TRIM(str);
            WHILE INSTR(str, '  ') > 0 DO
                SET str = REPLACE(str, '  ', ' ');
            END WHILE;
            SET str = REPLACE(
                SUBSTRING(
                    SUBSTRING_INDEX(str, ' ', pos), 
                    CHAR_LENGTH(
                        SUBSTRING_INDEX(str, ' ', pos - 1)
                    ) + 1
                )
                , ' ', ''
            );
            RETURN CAST(str AS UNSIGNED);
        END;
    """)

    db.commit_query("""
        UPDATE hiptyc_tyc_main
        SET 
          TYC1=SPLIT_TYC(TYC, 1), 
          TYC2=SPLIT_TYC(TYC, 2), 
          TYC3=SPLIT_TYC(TYC, 3)
    """)

    db.add_index("hiptyc_tyc_main", "TYC1")
    db.add_index("hiptyc_tyc_main", "TYC2")
    db.add_index("hiptyc_tyc_main", "TYC3")
    db.add_multiple_column_index("hiptyc_tyc_main", ("TYC1", "TYC2", "TYC3"), "TYC", unique=True)


def add_tyc2_index():
    db = SkyMapDatabase()
    db.add_multiple_column_index("tyc2_tyc2", ("TYC1", "TYC2", "TYC3"), "TYC", unique=True)


def build_stellar_source_databases():
    build_database("VI/42", "cst_id")
    build_database("VI/49", "cst_bound")
    build_database("I/311", "hipnew", indices=["HIP", "m_HIP"])
    build_database("I/239", "hiptyc", indices=["HIP", "m_HIP"], extra_function=split_tyc)
    build_database("I/259", "tyc2", indices=["TYC1", "TYC2", "TYC3", "HIP", "CCDM"], extra_function=add_tyc2_index)
    build_database("IV/25", "tyc2hd", indices=["TYC1", "TYC2", "TYC3", "HD"])
    build_database("IV/27A", "cross_index", indices=["HD"])
    build_database("V/50", "bsc", indices=['HR', 'HD'])

