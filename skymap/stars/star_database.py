import time
from skymap.database import SkyMapDatabase


def create_table(db):
    """
    Create the skymap_stars table in the SkyMapDatabase

    Args:
        db (skymap.database.SkyMapDatabase): An open SkyMapDatabase instance
    """

    db.drop_table("skymap_stars")

    print "Creating table"
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
    print "{:.1f} s".format(t2 - t1)


def hipparcos_single(db):
    print "Inserting Hipparcos single data"
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
    print "{:.1f} s".format(t2 - t1)


def hipparcos_multiple(db):
    print "Inserting Hipparcos multiple data"
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
    print "{:.1f} s".format(t2 - t1)


def tycho2(db):
    q = """
        
    """

if __name__ == "__main__":
    db = SkyMapDatabase()
    create_table(db)
    hipparcos_single(db)
    hipparcos_multiple(db)
