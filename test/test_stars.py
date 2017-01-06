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
            RIGHT JOIN hiptyc_hip_main AS h ON h.HIP=t.HIP
            WHERE t.HIP IS NULL/* AND h.RAdeg IS NOT NULL*/
        """
        self.assertEqual(self.db.query_one(q)['n'], 263)

    def test_hip_tyc1(self):
        pass

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
            SELECT t2.TYC1, t2.TYC2, t2.TYC3 FROM
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


def checks():
    # Goal 1: clean combination of Hipparcos, Hipparos New Reduction, Tycho-1 and Tycho-2
    # Goal 2: correct assignment of HD numbers
    # Goal 3: correct naming





    # Check that Tycho-2 supplement 1 stars are not in Tycho-2 main
    # Check that Tycho-2 supplement 2 stars are not in Tycho-2 main
    # Check that Tycho-2 supplement 1 stars are not in Tycho-2 supplement 1
    # Check that Tycho-2 supplement 2 stars are not in Tycho-2 supplement 1
    # Check that Tycho-2 main stars are not in Tycho-2 supplement 1
    # Check that Tycho-2 main stars are not in Tycho-2 supplement 2


    # Check whether all Tycho-2 supplement 1 stars are in Tycho-1 and/or Hipparcos



    # Check HIP numbers against Tycho-1 and Tycho-2 with supplement 1 and 2: no errors
    q = """
        SELECT t2.TYC1, t2.TYC2, t2.TYC3, t2.HIP, t1.HIP FROM ((SELECT TYC1, TYC2, TYC3, HIP FROM tyc2_tyc2) UNION ALL (SELECT TYC1, TYC2, TYC3, HIP FROM tyc2_suppl_1)) AS t2 JOIN hiptyc_tyc_main AS t1 ON t1.TYC1=t2.TYC1 AND t1.TYC2=t2.TYC2 AND t1.TYC3=t2.TYC3 WHERE t1.HIP != t2.HIP
    """

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
