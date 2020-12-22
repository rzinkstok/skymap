import time
import urllib
from bs4 import BeautifulSoup
from astroquery.simbad import Simbad

from skymap.database import SkyMapDatabase


def create_table(db):
    """
    Create the skymap_stars table in the SkyMapDatabase

    Args:
        db (skymap.database.SkyMapDatabase): An open SkyMapDatabase instance
    """

    db.drop_table("skymap_stars")

    print("Creating table")
    t1 = time.time()
    q = """CREATE TABLE skymap_stars (
                id INT NOT NULL AUTO_INCREMENT,
                hip INT,
                tyc1 INT,
                tyc2 INT,
                tyc3 INT,
                ccdm VARCHAR(64),
                ccdm_comp VARCHAR(2),
                hd1 INT,
                hd2 INT,
                hr INT,
                bd VARCHAR(64),
                cod VARCHAR(64),
                cpd VARCHAR(64),
                bayer VARCHAR(128),
                flamsteed INT,
                proper_name VARCHAR(512),
                variable_name VARCHAR(512),
                constellation VARCHAR(64),

                right_ascension DOUBLE,
                declination DOUBLE,
                proper_motion_ra DOUBLE,
                proper_motion_dec DOUBLE,
                parallax DOUBLE,

                johnsonV DOUBLE,
                johnsonBV DOUBLE,
                cousinsVI DOUBLE,
                hp_magnitude DOUBLE,
                vt_magnitude DOUBLE,
                bt_magnitude DOUBLE,

                hp_max DOUBLE,
                hp_min DOUBLE,
                vt_max DOUBLE,
                vt_min DOUBLE,
                max DOUBLE,
                min DOUBLE,

                variable BOOL,
                multiple BOOL,
                source VARCHAR(2),

                PRIMARY KEY (id)
            )"""

    db.commit_query(q)
    t2 = time.time()
    print(f"{t2-t1:.1f} s")


def hipparcos_single(db):
    print("Inserting Hipparcos single data")
    t1 = time.time()
    q = """
        INSERT INTO skymap_stars (
            hip, tyc1, tyc2, tyc3, CCDM,
            right_ascension,
            declination,
            parallax,
            proper_motion_ra, proper_motion_dec,
            johnsonV, johnsonBV, cousinsVI,
            bt_magnitude, vt_magnitude,
            hp_magnitude, hp_max, hp_min,
            variable,
            hd1, bd, cod, cpd,
            source
        )
        SELECT  
            h1.HIP, t.TYC1, t.TYC2, t.TYC3, h1.CCDM,
            DEGREES(h2.RArad) AS RAdeg,
            DEGREES(h2.DErad) AS DEdeg,
            h2.Plx,
            h2.pmRA, h2.pmDE,
            h1.Vmag, h1.`B-V`, h1.`V-I`,
            h1.BTmag, h1.VTmag,
            h1.Hpmag, h1.Hpmax, h1.Hpmin,
            CASE WHEN (h1.HVarType='P' OR (h1.HVarType='U' AND h1.Hpmin - h1.Hpmax > 0.2)) THEN 1 ELSE 0 END,
            h1.HD, h1.BD, h1.CoD, h1.CPD,
            'H2'
        FROM hipnew_hip2 h2
        JOIN hiptyc_hip_main h1 ON h1.HIP=h2.HIP
        LEFT JOIN
        (
            (
                SELECT 
                    TYC1, TYC2, TYC3, HIP, CCDM
                FROM
                    tyc2_tyc2
            ) 
            UNION ALL 
            (
                SELECT 
                    TYC1, TYC2, TYC3, HIP, CCDM
                FROM
                    tyc2_suppl_1
            )
        ) AS t 
        ON t.HIP = h1.HIP
        WHERE h1.RAdeg IS NOT NULL
        AND h1.HIP not in (SELECT HIP FROM hiptyc_h_dm_com);
    """
    db.commit_query(q)
    t2 = time.time()
    print(f"{t2-t1:.1f} s")


def hipparcos_multiple(db):
    print("Inserting Hipparcos multiple data")
    t1 = time.time()
    q = """
            INSERT INTO skymap_stars (
                hip, tyc1, tyc2, tyc3, 
                ccdm, ccdm_comp,
                right_ascension,
                declination,
                parallax,
                proper_motion_ra, proper_motion_dec,
                bt_magnitude, vt_magnitude,
                hp_magnitude,
                hd1, bd, cod, cpd,
                source
            )
            SELECT 
                h.HIP, t.TYC1, t.TYC2, t.TYC3, 
                d.CCDM, d.comp_id,
                d.RAdeg,
                d.DEdeg,
                d.Plx,
                d.pmRA, d.pmDE,
                d.BT, d.VT,
                d.Hp,
                h.HD, h.BD, h.CoD, h.CPD,
                'H1'
            FROM 
                hiptyc_hip_main AS h 
            INNER JOIN 
                hiptyc_h_dm_com AS d ON d.HIP = h.HIP
            LEFT JOIN
                (
                    (
                        SELECT 
                            TYC1, TYC2, TYC3, HIP, CCDM
                        FROM
                            tyc2_tyc2
                    ) 
                    UNION ALL 
                    (
                        SELECT 
                            TYC1, TYC2, TYC3, HIP, CCDM
                        FROM
                            tyc2_suppl_1
                    )
                ) AS t 
                ON t.HIP = h.HIP
                AND (
                    IFNULL(d.comp_id, '') = TRIM(IFNULL(t.CCDM, '')) -- Single or no component in Tycho record 
                    OR
                    TRIM(d.comp_id) IN (SUBSTR(t.CCDM, 1, 1) , SUBSTR(t.CCDM, 2, 1), SUBSTR(t.CCDM, 3, 1)) -- Multiple components in single Tycho record
                )
            WHERE h.RAdeg IS NOT NULL;
    """
    db.commit_query(q)
    t2 = time.time()
    print(f"{t2-t1:.1f} s")


def tycho2(db):
    print("Inserting Tycho-2 data")
    t1 = time.time()
    q = """
        INSERT INTO skymap_stars (
            tyc1, tyc2, tyc3,
            hd1, hd2,
            right_ascension,
            declination,
            proper_motion_ra, proper_motion_dec,
            bt_magnitude, vt_magnitude,
            johnsonV,
            johnsonBV,
            vt_max, vt_min, variable,
            source
        )
        SELECT
            t2.TYC1, t2.TYC2, t2.TYC3,
            HD1, HD2,
            IFNULL(t2.RAmdeg, t2.RAdeg) as RAdeg,
            IFNULL(t2.DEmdeg, t2.DEdeg) as DEdeg,
            t2.pmRA, t2.pmDE,
            t2.BTmag, t2.VTmag,
            t2.VTmag - 0.090 * (t2.BTmag - t2.VTmag) as JohnsonV,
            0.085 * (t2.BTmag - t2.VTmag) as JohnsonBV,
            t1.VTmax, t1.VTmin, t1.varflag='V',
            'T2'
        FROM tyc2_tyc2 AS t2
        LEFT JOIN hiptyc_tyc_main t1 ON 
            t1.TYC1=t2.TYC1 AND t1.TYC2=t2.TYC2 AND t1.TYC3=t2.TYC3
        LEFT JOIN (
            SELECT TYC1, TYC2, TYC3, MIN(HD) AS HD1, CASE WHEN COUNT(HD)>1 THEN MAX(HD) ELSE NULL END AS HD2
            FROM tyc2hd_tyc2_hd
            WHERE Rem!='D'
            GROUP BY TYC1, TYC2, TYC3
        ) AS t2hd
        ON t2.TYC1=t2hd.TYC1 AND t2.TYC2=t2hd.TYC2 AND t2.TYC3=t2hd.TYC3
        WHERE t2.HIP IS NULL 
    """
    db.commit_query(q)
    t2 = time.time()
    print(f"{t2-t1:.1f} s")


def add_indices(db):
    """
    Add indices to the star table on the TYC1-3, HIP, HD columns.

    Args:
        db (skymap.database.SkyMapDatabase): An open SkyMapDatabase instance
    """

    print("Adding indices")
    t1 = time.time()
    db.add_index("skymap_stars", "HIP")
    db.add_index("skymap_stars", "TYC1")
    db.add_index("skymap_stars", "TYC2")
    db.add_index("skymap_stars", "TYC3")
    db.add_multiple_column_index("skymap_stars", ("TYC1", "TYC2", "TYC3"), "TYC")
    db.add_index("skymap_stars", "HD1")
    db.add_index("skymap_stars", "HD2")
    db.add_index("skymap_stars", "HR")
    t2 = time.time()
    print(f"{t2-t1:.1f} s")


def add_cross_index(db):
    """
    Add information from the HD-DM-GC-HR-HIP-Bayer-Flamsteed Cross Index (IV/27A). Bayer, Flamsteed, HR numbers.

    Args:
        db (skymap.database.SkyMapDatabase): An open SkyMapDatabase instance
    """

    print("Adding New Cross Index data")
    t1 = time.time()
    q = """
        UPDATE skymap_stars, cross_index_catalog
        SET
          skymap_stars.bayer = cross_index_catalog.Bayer,
          skymap_stars.flamsteed = cross_index_catalog.Fl,
          skymap_stars.hr = cross_index_catalog.HR
        WHERE cross_index_catalog.HD=skymap_stars.hd1 OR cross_index_catalog.HD=skymap_stars.hd2
            """
    db.commit_query(q)
    t2 = time.time()
    print(f"{t2-t1:.1f} s")


def add_bright_star_catalog(db):
    """
    Adds HR numbers from the Bright Star Catalog

    Args:
        db (skymap.database.SkyMapDatabase): An open SkyMapDatabase instance
    """

    print("Adding Bright Star Catalog data")
    t1 = time.time()
    q = """
        UPDATE skymap_stars, bsc_catalog
        SET
          skymap_stars.hr = bsc_catalog.hr
        WHERE bsc_catalog.hd=skymap_stars.hd1 OR bsc_catalog.hd=skymap_stars.hd2
    """
    db.commit_query(q)
    t2 = time.time()
    print(f"{t2-t1:.1f} s")


def add_proper_names(db):
    """
    Adds the IAU proper names to the star database.

    Args:
        db (skymap.database.SkyMapDatabase): An open SkyMapDatabase instance
    """

    print("Adding proper names")
    t1 = time.time()

    # Retrieve the proper name list
    url = "https://www.iau.org/public/themes/naming_stars/"
    r = urllib.urlopen(url).read()
    soup = BeautifulSoup(r, "html5lib")

    # Loop over all stars in the list
    for tr in soup.find_all("tbody")[0].find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue

        designation = tds[1].get_text().strip()
        if designation.startswith("HR"):
            columns = ["HR"]
            value = int(designation[2:].strip())
        elif designation.startswith("HD"):
            columns = ["HD1", "HD2"]
            value = int(designation[2:].strip())
        else:
            result_table = Simbad.query_objectids(designation)
            try:
                value = int(
                    [x for x in result_table if x["ID"].startswith("HIP")][0]["ID"][
                        3:
                    ].strip()
                )
            except IndexError:
                continue
            columns = ["HIP"]

        proper_name = tds[0].get_text().strip()

        # Find the brightes star with the given identifier
        q = f"""SELECT id FROM skymap_stars WHERE {columns[0]} = {value}"""
        for c in columns[1:]:
            q += f""" OR {c}={value}"""
        q += """ ORDER BY hp_magnitude ASC LIMIT 1"""
        row = db.query_one(q)
        if row is None:
            continue

        # Update the database record
        q = f"""UPDATE skymap_stars SET proper_name="{proper_name}" WHERE id={row["id"]}"""
        db.commit_query(q)

    # Add some special cases
    special_cases = {
        24186: "Kapteyn's Star",
        49908: "Groombridge 1618",
        57939: "Groombridge 1830",
        105_090: "Lacaille 8760",
        114_046: "Lacaille 9352",
        54035: "Lalande 21185",
        114_622: "Bradley 3077",
    }

    for hip, proper_name in special_cases.items():
        rid = db.query_one(
            f"""SELECT id FROM skymap_stars WHERE hip={hip} ORDER BY hp_magnitude ASC LIMIT 1"""
        )["id"]
        q = f"""UPDATE skymap_stars SET proper_name="{proper_name}" WHERE id={rid}"""
        db.commit_query(q)

    t2 = time.time()
    print(f"{t2-t1:.1f} s")


def build_stellar_database():
    db = SkyMapDatabase()
    create_table(db)
    hipparcos_single(db)
    hipparcos_multiple(db)
    tycho2(db)
    add_indices(db)
    add_cross_index(db)
    add_bright_star_catalog(db)
    add_proper_names(db)
