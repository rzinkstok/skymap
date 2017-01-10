import unittest
from skymap.database import SkyMapDatabase


class StarDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.db = SkyMapDatabase()

    # Unicity
    def test_hip_unique(self):
        """Check whether HIP identification is unique within Hipparcos"""
        q = """
            SELECT COUNT(*) AS n FROM
            (
                SELECT HIP FROM hiptyc_hip_main GROUP BY HIP HAVING COUNT(HIP)>1
            ) AS h
        """

        self.assertEqual(self.db.query_one(q)['n'], 0)

    def test_tyc1_unique(self):
        """Check whether TYC identification is unique within Tycho-1"""
        q = """
            SELECT COUNT(*) AS n FROM (
                SELECT tyc FROM
                (
                    SELECT CONCAT(TYC1, '-', TYC2, '-', TYC3) as tyc
                    FROM hiptyc_tyc_main
                ) AS t1
                GROUP BY tyc HAVING COUNT(tyc)>1
            ) AS t2
        """

        self.assertEqual(self.db.query_one(q)['n'], 0)

    def test_tyc2_unique(self):
        """Check whether TYC identification is unique within Tycho-2.
        Strangely, 254 duplicates are found, all between main and supplement 1. In all cases except for 1 (there it is
        the AB-component), the A-component is in the main component, the other (in all but 4 cases the B-component,
        three times it is the C-component, once the P-component) in supplement 1. Positions differ slightly within each
        pair. All supplement 1 stars are Hipparcos stars. Stars seem to be in Tycho-1 and Hipparcos as single entries
        with multiple components (Double/Multiple annex). Not resolved yet!
        """

        # TODO: solve

        q = """
            SELECT COUNT(*) AS n FROM (
                SELECT tyc FROM
                (
                    SELECT CONCAT(TYC1, '-', TYC2, '-', TYC3) as tyc FROM tyc2_tyc2
                    UNION ALL
                    SELECT CONCAT(TYC1, '-', TYC2, '-', TYC3) as tyc FROM tyc2_suppl_1
                    UNION ALL
                    SELECT CONCAT(TYC1, '-', TYC2, '-', TYC3) as tyc FROM tyc2_suppl_2
                ) AS t1
                GROUP BY tyc HAVING COUNT(tyc)>1
            ) AS t2
        """

        self.assertEqual(self.db.query_one(q)['n'], 254)

    # Hipparcos - Hipparcos New Reduction
    def test_hip_hipnew(self):
        """Check whether all Hipparcos stars are in Hipparcos New Reduction;
        263 stars missing (all stars without proper astrometry)"""

        q = """
            SELECT COUNT(*) AS n FROM hiptyc_hip_main AS h
            LEFT JOIN hipnew_hip2 AS h2 ON h2.HIP=h.HIP
            WHERE h2.HIP IS NULL
        """
        self.assertEqual(self.db.query_one(q)['n'], 263)

    def test_hipnew_hip(self):
        """Check whether all Hipparcos New Reduction Stars are in Hipparcos"""

        q = """
            SELECT COUNT(*) AS n FROM hipnew_hip2 AS h2
            LEFT JOIN hiptyc_hip_main AS h ON h2.HIP=h.HIP
            WHERE h.HIP IS NULL
        """
        self.assertEqual(self.db.query_one(q)['n'], 0)

    # Hipparcos - Tycho-1
    def test_tyc1_hip(self):
        """Check whether all Tycho-1 stars labeled as Hipparcos stars are in Hipparcos"""

        q = """
            SELECT COUNT(*) AS n FROM
            hiptyc_tyc_main AS t
            LEFT JOIN
            hiptyc_hip_main AS h
            ON t.HIP=h.HIP
            WHERE t.HIP IS NOT NULL
            AND h.HIP IS NULL
        """

        self.assertEqual(self.db.query_one(q)['n'], 0)

    def test_hip_tyc1(self):
        """Check whether all Hipparcos stars are in Tycho-1. Only the Hipparcos stars without astrometric solutions
        (263 stars) are not found in Tycho-1.
        """
        q = """
            SELECT COUNT(*) AS n FROM
            hiptyc_hip_main AS h
            LEFT JOIN
            hiptyc_tyc_main AS t
            ON t.HIP=h.HIP
            WHERE t.HIP IS NULL
        """

        self.assertEqual(self.db.query_one(q)['n'], 263)

    def test_hip_to_multiple_tyc1(self):
        """Check multiple stars between Hipparcos and Tycho-1.
        These are multiple stars of which the components are recorded in both databases. The query checks for all
        components of a given HIP star to see if they are found in Tycho-1. Component identifiers should match or
        if not, the number of components from Hipparcos should be equal to the number of letters in the concatenated
        Tycho-1 component identifiers."""

        q = """
            SELECT COUNT(*) AS n FROM (
                SELECT t.HIP, t.m_HIP AS T_comp, h.m_HIP AS H_comp, h.Ncomp AS H_ncomp, t.Ncomp AS T_ncomp FROM
                (
                    SELECT HIP, GROUP_CONCAT(TRIM(m_HIP) SEPARATOR '') AS m_HIP, COUNT(HIP) AS Ncomp FROM hiptyc_tyc_main GROUP BY HIP HAVING COUNT(HIP)>1
                ) AS t
                LEFT JOIN
                (
                    SELECT HIP, m_HIP, Ncomp FROM hiptyc_hip_main
                ) AS h
                ON t.HIP=h.HIP
                WHERE NOT
                (
                    (t.m_HIP = h.m_HIP OR t.m_HIP = REVERSE(h.m_HIP))
                    OR
                    LENGTH(t.m_HIP) = h.Ncomp
                )
            ) AS t
        """

        self.assertEqual(self.db.query_one(q)['n'], 0)

    # Tycho-1 - Tycho-2
    def test_tyc1_tyc2(self):
        """Check whether all Tycho-1 stars are in Tycho-2 (including supplement 1 and 2). Stars with astrometric quality
        of 9 are not included in Tycho-2."""

        q = """
            SELECT COUNT(*) AS n
            FROM hiptyc_tyc_main AS t1
            LEFT JOIN
            (
                SELECT TYC1, TYC2, TYC3 FROM tyc2_tyc2 UNION ALL SELECT TYC1, TYC2, TYC3 FROM tyc2_suppl_1 UNION ALL SELECT TYC1, TYC2, TYC3 FROM tyc2_suppl_2
            ) AS t2
            ON t1.TYC1=t2.TYC1 AND t1.TYC2=t2.TYC2 AND t1.TYC3=t2.TYC3
            WHERE t2.TYC1 IS NULL
            AND t1.Q != 9
        """

        self.assertEqual(self.db.query_one(q)['n'], 0)

    def test_tyc2_tyc1(self):
        """Check whether all Tycho-2 stars that are labeled as Tycho-1 stars are in Tycho-1.
        Hipparcos stars that were not measured by Tycho-1 were included in Tycho-1, but are not labeled as Tycho-1 stars
        in Tycho-2. These stars are labeled in Tycho-1 with an 'H' in the 'Source' field.
        Tycho-1 stars that are resolved into multiple Tycho-2 stars are all labeled as Tycho-1 stars, but have different
        Tycho-2 ids. Such multiple stars share the same TYC1 and TYC2. The original Tycho-1 stars has TYC3 equal to 1,
        so the other components have higher TYC3 numbers. These are excluded as they will not be found in Tycho-1.
        """

        q = """
            SELECT COUNT(*) AS n FROM
            (
                SELECT TYC1, TYC2, TYC3 FROM tyc2_tyc2 WHERE TYC='T' AND TYC3=1
                UNION ALL
                SELECT TYC1, TYC2, TYC3 FROM tyc2_suppl_1 WHERE TYC='T' AND TYC3=1
                UNION ALL
                SELECT TYC1, TYC2, TYC3 FROM tyc2_suppl_2 WHERE TYC='T' AND TYC3=1
            ) AS t2
            LEFT JOIN
            (
                SELECT TYC1, TYC2, TYC3 FROM hiptyc_tyc_main WHERE Source!='H'
            ) AS t1
            ON t1.TYC1=t2.TYC1 AND t1.TYC2=t2.TYC2 AND t1.TYC3=t2.TYC3
            WHERE t1.TYC1 IS NULL
        """

        self.assertEqual(self.db.query_one(q)['n'], 0)

    # Tycho-2 internal
    def test_tyc2_supplement1(self):
        """Check that there is no overlap between Tycho-2 main and Tycho-2 supplement 1. See test_tyc2_unique for more
        info on the 254 stars that do overlap."""
        q = """
            SELECT COUNT(*) AS n
            FROM tyc2_tyc2 as t2
            INNER JOIN tyc2_suppl_1 as ts1
            ON t2.TYC1=ts1.TYC1 AND t2.TYC2=ts1.TYC2 AND t2.TYC3=ts1.TYC3
        """

        self.assertEqual(self.db.query_one(q)['n'], 254)

    def test_tyc2_supplement2(self):
        """Check that there is no overlap between Tycho-2 main and Tycho-2 supplement 1"""
        q = """
            SELECT COUNT(*) AS n
            FROM tyc2_tyc2 as t2
            INNER JOIN tyc2_suppl_2 as ts2
            ON t2.TYC1=ts2.TYC1 AND t2.TYC2=ts2.TYC2 AND t2.TYC3=ts2.TYC3
        """

        self.assertEqual(self.db.query_one(q)['n'], 0)

    def test_supplement1_supplement2(self):
        """Check that there is no overlap between Tycho-2 supplement 1 and Tycho-2 supplement 2"""
        q = """
            SELECT COUNT(*) AS n
            FROM tyc2_suppl_1 as ts1
            INNER JOIN tyc2_suppl_2 as ts2
            ON ts1.TYC1=ts2.TYC1 AND ts1.TYC2=ts2.TYC2 AND ts1.TYC3=ts2.TYC3
        """

        self.assertEqual(self.db.query_one(q)['n'], 0)

    # Hipparcos - Tycho-2
    def test_hip_tyc2(self):
        """Check whether all Hipparcos stars are found in Tycho-2. The 263 Hipparcos star without an astrometric
        solution are not included in Tycho-2."""
        q = """
            SELECT COUNT(*) AS n FROM
            hiptyc_hip_main AS h
            LEFT JOIN (
                SELECT TYC1, TYC2, TYC3, HIP FROM tyc2_tyc2
                UNION ALL
                SELECT TYC1, TYC2, TYC3, HIP FROM tyc2_suppl_1
                UNION ALL
                SELECT TYC1, TYC2, TYC3, HIP FROM tyc2_suppl_2
            ) AS t2
            ON t2.HIP=h.HIP
            WHERE t2.HIP IS NULL
        """

        self.assertEqual(self.db.query_one(q)['n'], 263)

    def test_tyc2_hip(self):
        """Check whether all Tycho-2 stars labeled as Hipparcos stars are found in Hipparcos"""
        q = """
            SELECT COUNT(*) AS n FROM (
                SELECT TYC1, TYC2, TYC3, HIP FROM tyc2_tyc2
                UNION ALL
                SELECT TYC1, TYC2, TYC3, HIP FROM tyc2_suppl_1
                UNION ALL
                SELECT TYC1, TYC2, TYC3, HIP FROM tyc2_suppl_2
            ) AS t2
            LEFT JOIN hiptyc_hip_main AS h
            ON t2.HIP=h.HIP
            WHERE h.HIP IS NULL
            AND t2.HIP IS NOT NULL
        """

        self.assertEqual(self.db.query_one(q)['n'], 0)

    def test_hip_to_multiple_tyc2(self):
        """Check multiple stars between Hipparcos and Tycho-2.
        These are multiple stars of which the components are recorded in both databases. The query checks for all
        components of a given HIP star to see if they are found in Tycho-2. Component identifiers should match or
        if not, the number of components from Hipparcos should be equal to the number of letters in the concatenated
        Tycho-2 component identifiers."""

        q = """
            SELECT COUNT(*) AS n FROM (
                SELECT t.HIP, t.m_HIP AS T_comp, h.m_HIP AS H_comp, h.Ncomp AS H_ncomp, t.Ncomp AS T_ncomp FROM
                (
                    SELECT HIP, GROUP_CONCAT(TRIM(CCDM) SEPARATOR '') AS m_HIP, COUNT(HIP) AS Ncomp FROM (
                        SELECT HIP, CCDM FROM tyc2_tyc2
                        UNION ALL
                        SELECT HIP, CCDM FROM tyc2_suppl_1
                    ) as tt
                    GROUP BY HIP HAVING COUNT(HIP)>1
                ) AS t
                LEFT JOIN
                (
                    SELECT HIP, m_HIP, Ncomp FROM hiptyc_hip_main
                ) AS h
                ON t.HIP=h.HIP
                WHERE NOT
                (
                    (t.m_HIP = h.m_HIP OR t.m_HIP = REVERSE(h.m_HIP))
                    OR
                    LENGTH(t.m_HIP) = h.Ncomp
                )
            ) AS t
        """

        self.assertEqual(self.db.query_one(q)['n'], 0)

    # Tycho-2 supplement 1 - Hipparcos/Tycho-1
    def test_supplement1_hip(self):
        """Check whether all Tycho-2 supplement 1 stars are in Tycho-1 and/or Hipparcos"""
        q = """
            SELECT COUNT(*) AS n
            FROM tyc2_suppl_1 AS ts1
            LEFT JOIN hiptyc_hip_main AS h
            ON ts1.HIP=h.HIP
            WHERE ts1.flag='H'
            AND h.HIP IS NULL
        """

        self.assertEqual(self.db.query_one(q)['n'], 0)

        q = """
            SELECT COUNT(*) AS n
            FROM tyc2_suppl_1 AS ts1
            LEFT JOIN hiptyc_tyc_main AS t
            ON ts1.TYC1=t.TYC1 AND ts1.TYC2=t.TYC2 AND ts1.TYC3=t.TYC3
            WHERE ts1.flag='T'
            AND t.TYC1 IS NULL
        """

        self.assertEqual(self.db.query_one(q)['n'], 0)

    # Tycho-2 supplement 2 - Hipparcos/Tycho-1
    def test_supplement2_hip(self):
        """Check whether all Tycho-2 supplement 2 stars are in Tycho-1 and/or Hipparcos"""
        q = """
            SELECT COUNT(*) AS n
            FROM tyc2_suppl_2 AS ts2
            LEFT JOIN hiptyc_hip_main AS h
            ON ts2.HIP=h.HIP
            WHERE ts2.flag='H'
            AND h.HIP IS NULL
        """

        self.assertEqual(self.db.query_one(q)['n'], 0)

        q = """
            SELECT COUNT(*) AS n
            FROM tyc2_suppl_2 AS ts2
            LEFT JOIN hiptyc_tyc_main AS t
            ON ts2.TYC1=t.TYC1 AND ts2.TYC2=t.TYC2 AND ts2.TYC3=t.TYC3
            WHERE ts2.flag='T'
            AND t.TYC1 IS NULL
        """

        self.assertEqual(self.db.query_one(q)['n'], 0)


def checks():
    # Goal 1: clean combination of Hipparcos, Hipparos New Reduction, Tycho-1 and Tycho-2
    # Goal 2: correct assignment of HD numbers
    # Goal 3: correct naming











    # Check HD numbers between Tycho-1 and Hipparcos
    # 1) HIP entries that correspond to a single TYC entry: 42 contradictions (TYC2_HD makes a decision)
    q = """
        SELECT t.TYC1, t.TYC2, t.TYC3, h.HIP, t.m_HIP, t.HD AS THD, h.HD AS HHD, thd.HD AS T2HD FROM
        (
            SELECT TYC1, TYC2, TYC3, HIP, m_HIP, HD FROM hiptyc_tyc_main WHERE HIP NOT IN
            (SELECT HIP FROM hiptyc_tyc_main GROUP BY HIP HAVING COUNT(HIP) > 1)
        ) AS t
        JOIN hiptyc_hip_main AS h
        ON t.HIP=h.HIP
        JOIN (
            SELECT TYC1, TYC2, TYC3, GROUP_CONCAT(HD) AS HD FROM tyc2hd_tyc2_hd GROUP BY TYC1, TYC2, TYC3
        ) AS thd
        ON t.TYC1=thd.TYC1 AND t.TYC2=thd.TYC2 AND t.TYC3=thd.TYC3
        WHERE t.HD!=h.HD
        ORDER BY t.HD
    """

    # 2) HIP entries resolved in TYC: 50 contradictions (TYC2_HD makes a decision)
    q = """
        SELECT t.TYC1, t.TYC2, t.TYC3, h.HIP, t.m_HIP, t.HD AS THD, h.HD AS HHD, thd.HD AS T2HD FROM
        (
            SELECT TYC1, TYC2, TYC3, HIP, m_HIP, HD FROM hiptyc_tyc_main WHERE HIP IN
            (SELECT HIP FROM hiptyc_tyc_main GROUP BY HIP HAVING COUNT(HIP) > 1)
        ) AS t
        JOIN hiptyc_hip_main AS h
        ON t.HIP=h.HIP
        JOIN (
            SELECT TYC1, TYC2, TYC3, GROUP_CONCAT(HD) AS HD FROM tyc2hd_tyc2_hd GROUP BY TYC1, TYC2, TYC3
        ) AS thd
        ON t.TYC1=thd.TYC1 AND t.TYC2=thd.TYC2 AND t.TYC3=thd.TYC3
        WHERE t.HD!=h.HD
        ORDER BY t.HD
    """

    # Check HD numbers between Tycho-1 and tyc2_hd: 300 contradictions
    q = """
        SELECT
            t1.TYC1, t1.TYC2, t1.TYC3, t1.HD, t1.Vmag, t1.HIP,
            t2hd.HD1, t2hd.HD2, t2hd.n_HD, t2hd.n_TYC, t2hd.Note, t2hd.Rem
        FROM
            ((SELECT TYC1, TYC2, TYC3 FROM tyc2_tyc2) UNION ALL (SELECT TYC1, TYC2, TYC3 FROM tyc2_suppl_1)) AS t2
            INNER JOIN
            (
                SELECT
                    TYC1, TYC2, TYC3,
                    MIN(HD) AS HD1,
                    CASE WHEN COUNT(HD)>1 THEN MAX(HD) ELSE NULL END AS HD2,
                    GROUP_CONCAT(n_HD) AS n_HD, GROUP_CONCAT(n_TYC) AS n_TYC, GROUP_CONCAT(Note) AS Note, GROUP_CONCAT(Rem) AS Rem
                FROM tyc2hd_tyc2_hd
                GROUP BY TYC1, TYC2, TYC3
            ) AS t2hd
            ON t2.TYC1=t2hd.TYC1 AND t2.TYC2=t2hd.TYC2 AND t2.TYC3=t2hd.TYC3
            INNER JOIN hiptyc_tyc_main AS t1
            ON t1.TYC1=t2hd.TYC1 AND t1.TYC2=t2hd.TYC2 AND t1.TYC3=t2hd.TYC3
        WHERE t1.HD != t2hd.HD1 AND (t2hd.HD2 IS NULL OR t1.HD != t2hd.HD2)
    """

    # Check HD numbers between Tycho-2/tyc2_hd and Hipparcos
