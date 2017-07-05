# Stellar database

The stars plotted in SkyMap all come from the Hipparcos, Tycho and Tycho-2 catalogues published by ESA:

* The Hipparcos and Tycho Catalogues (ESA 1997), http://cdsarc.u-strasbg.fr/viz-bin/Cat?I/239
* The Tycho-2 Catalogue of the 2.5 Million Brightest Stars, Hog et al., Astron. Astrophys. 355, L27 (2000), http://cdsarc.u-strasbg.fr/viz-bin/Cat?I/259
* Hipparcos, the new Reduction of the Raw data, van Leeuwen F., Astron. Astrophys. 474, 653 (2007), http://cdsarc.u-strasbg.fr/viz-bin/Cat?I/311

For ease of use, these were converted to MySQL databases: all queries below are performed on these databases.

## History

The Hipparcos catalogue (118,218 stars) was first published in 1997, together with the larger Tycho catalogue (1,058,332 stars). 
In 2000, the Tycho-2 catalogue was published, containing even more stars (2,539,913) at a slightly higher accuracy than Tycho-1.
For all practical purposes, the newer Tycho-2 supersedes the earlier Tycho catalogue (from now on, Tycho-1) completely. The
only exceptions is the variability data in Tycho-1: Tycho-2 does not say anything about that. For the 
Hipparcos catalogue, a new reduction of the raw data was published in 2007, bringing much more accurate astrometrics.

The astrometric accuracy of the Hipparcos catalogue is much better than that of the Tycho catalogues: for Hp < 9 mag, the median precision for the position 
is 0.77/0.64 mas (RA/dec), and for proper motion 0.88/0.74 mas/yr (RA/dec). The Tycho catalogue does not get better than
7 mas for stars with Vt < 9 mag. The photometric accuracy of Hipparcos is better as well: for Hp < 9 mag, the median photometric 
precision is 0.0015 mag, while Tycho-1 is limited to 0.012 mag (Vt).

## Structure of the databases

### Hipparcos
* Identifier: HIP
* Reference system: ICRS
* Position epoch: J1991.25
* Catalogue parts:
  * Main catalogue: astrometrics, photometrics
  * Double and Multiple System Annex (DMSA): component information for entries resolved into 2 or more components
  * Variability Annex: variability data

### Tycho
* Identifier: TYC1, TYC2, TYC3, HIP
* Reference system: ICRS
* Position epoch: J1991.25
* Catalogue parts:
  * Main catalogue

### Tycho-2
* Identifier: TYC1, TYC2, TYC3, HIP
* Reference system: ICRS
* Position epoch: J2000
* Catalogue parts:
  * Main catalogue
  * Supplement 1 (Hipparcos/Tycho-1 stars not in Tycho-2)
  * Supplement 2 (Tycho-1 stars either false or heavily disturbed)

## Combining the databases

In order to make use of the large number of stars in Tycho-2, but not lose out on the much more accurate data in Hipparcos,
it would be nice to combine the databases. However, this is not trivial, especially due to the multiplicity as indicated in 
Hipparcos. Tycho-1 does not indicate much about multiplicity: only a duplicity flag (T49) and the CCDM component identifier (T51) to
link to Hipparcos. Tycho-2 does not have a duplicity flag (one assumes all multiples in Tycho-1 were resolved in Tycho-2), but
does give the CCDM component identifiers. The new Hipparcos reduction gives information on the number of components, and the
solution type also indicates double stars: it seems that no new doubles or multiples are identified.

The general idea will be as follows:
* Use all Hipparcos data
* Use all data from Tycho-1 except Hipparcos stars (Tycho-1 stars with HIP number) and Tycho-2 supplement 2 stars
* Use all data from Tycho-2 except Hipparcos stars (Tycho-2 stars with HIP number); overwrite astrometrics for Tycho-1 stars

Further data will come from other sources:
* Variability data from GCVS
* HD numbers
* Bayer, Flamsteed
* Proper names from IAU
* Constellation assignment

Issues:
* Propagation of star positions to a common epoch (maybe not required)
* Hipparcos double/multiple stars that are not resolved in Tycho-1 (5898 cases, see p. 159 of the *Hipparcos and Tycho Catalogue*; ignore the Tycho-1 data?)
* Hipparcos stars resolved into multiple Tycho-1 stars: this does not occur (only one of the stars is assigned the Hipparcus number)
* Tycho-1 stars that are resolved into multiple Tycho-2 stars: (ignore Tycho-1 data?) 
* 

### Hipparcos multiplicity

A star can be part of a multiple system when:
* Its entry shares the CCDM identifier with one or more other entries
* It is resolved into separate components: it has one entry with number of components larger than 1
 
In the latter case, the components are described in part C of the DMSA, which deals with
component solutions. Other parts of the DMSA describe less clear solutions (acceleration terms, orbital solutions, 
variability induced movers and stochastic solutions). These are not counted as resolved.

This means multiple systems can be found by the following:
* Find all entries linked by a common CCDM identifier
* Find all entries with number of components greater than 1; these have a multiplicity flag equal to C, and their component data is found in part C of the Double and Multiple Systems Annex)

If required, dubious multiple systems can be found by looking at entries where the multiplicity flag is set but unequal 
to C (that is, G, O, V or X).

Using this method, all double and multiple systems can be found, grouped by the CCDM identifier. Incidentally, there are 
also entries with number of components equal to 1 that do have an entry in part C of the DMSA: these are always part of 
a multy-entry (multi-pointing) system.

In the language of the Hipparcos guide, systems are called two-pointing when two separate entries (two separate pointings
of the sattelite's detector) describe a system having two or more components, and the astrometrics of the system is solved using
the data of both entries combined. Three-pointing and four-pointing systems are defined similarly. Not all 
all entries linked by a common CCDM identifier are two-, three- or four-pointing: for some cases, the astrometrics are solved
for each entry separately.

| Description                               | Number |
| ----------------------------------------- | -----: |
| Entries with a CCDM id                    |  19393 |
| Number of CCDM pairs                      |   1714 |
| Number of CCDM triplets                   |     43 |
| Number of CCDM quartets                   |      5 |
| Components in main with CCDM id           |  30770 |
| Components in part C                      |  24588 |
| Single entry CCDM                         |  15816 |

Queries used:

```SQL
-- Number of CCDM pairs in main
SELECT COUNT(*) FROM (
	SELECT CCDM from hiptyc_hip_main WHERE nsys=2 GROUP BY CCDM
) t1;

-- Number of components in main 
SELECT COUNT(*)
FROM hiptyc_hip_main AS main
LEFT JOIN hiptyc_h_dm_com as dm ON dm.HIP = main.HIP
WHERE main.CCDM != '';

-- Number of components in part C of DMSA
SELECT COUNT(*) 
FROM hiptyc_hip_main AS main
INNER JOIN hiptyc_h_dm_com as dm ON dm.HIP = main.HIP
WHERE main.CCDM != '';

-- Number of single entry CCDM systems
SELECT COUNT(*) FROM (
	SELECT CCDM from hiptyc_hip_main WHERE nsys=1 GROUP BY CCDM
) t1;
```

On page 125 of the *Hipparcos and Tycho Catalogue*, a full analysis of the number of double and multiple systems is
presented. In order to get a feel of the data, the core numbers are reproduced here:
 
| Components in system | Single-pointing | Two-pointing | Three-pointing |
| -------------------- | --------------: | -----------: | -------------: |
| 2                    |           11048 |          957 |              0 |
| 3                    |             129 |           50 |              3 |
| 4                    |               6 |            1 |              1 |

Queries used:

````SQL
-- Number of single-pointing entries/systems with 2 components (11048; 3 components 129; 4 components 6)
SELECT COUNT(*) FROM hiptyc_hip_main WHERE Source IN ('',  'S') AND MultFlag='C' AND nComp=2;

-- Number of two-pointing systems with 2 components (957; 3 components 50; 4 components 1)
-- Number of three-pointing systems with 2 components (0; 3 components 3; 4 components 1)
-- Funny enough, this query does not yield correct results when applied to single-pointing systems...
SELECT COUNT(*) FROM (
	SELECT COUNT(DISTINCT m.hip) AS npointing, COUNT(DISTINCT d.pk) AS ncomponents
	FROM hiptyc_hip_main AS m 
	LEFT JOIN hiptyc_h_dm_com AS d ON d.HIP = m.HIP
	WHERE m.Source IN ('F', 'I', 'L', 'P') 
	GROUP BY d.CCDM 
) t2
WHERE npointing=2 AND ncomponents=2;
````


### Linking Hipparcos and Tycho-1

A simple join of the main Hipparcos file with part C of the DMSA would yield a complete list of all resolved stars in
Hipparcos: this is a list of 129,595 records. Every record in this list is uniquely identified by the HIP identifier 
and the CCDM component identifier. In principle, each of these records should correspond to an entry in the Tycho-1
database.

However, there are 5,898 entries in Hipparcos that contain 2 or 3 stars (specified in the DMSA) that are not resolved in 
Tycho-1, comprising 5,896 Hipparcos numbers. In Tycho-1, the m_HIP field contains both component IDs (AB, AC, etc) for
the double stars or TT for the three cases where it is a triple system, where the component IDs are in fact ABC. For
these unresolved systems, we ignore the Tycho-1 data.

The 263 stars in Hipparcos that have no proper astrometry are not found in Tycho, and are suppressed.

In order to generate a list of all individual stars in Hipparcos and Tycho-1, the following method is used:
* Left join Hipparcos main to the DMSA part C yields all individual stars in Hipparcos; call this IndiHip
* Right join IndiHip and Tycho-1 on the HIP number and component ID, omitting all 5,898 unresolved entries where 
LENGTH(TRIM(m_HIP)) > 1; call this IndiHipTyc
* Add to IndiHipTyc the Hipparcos records for the unresolved doubles
* Add to IndiHipTyc the Hipparcos records for the unresolved triples


| Description                                    | Number    |
| ---------------------------------------------- | --------: |
| Stars in Tycho-1                               | 1,058,332 |
| Resolved Hipparcos stars in Tycho-1            | 1,052,434 |
| Hipparcos double stars not resolved in Tycho-1 |    11,790 |
| Hipparcos triple stars not resolved in Tycho-1 |         9 |


```SQL
-- Combine Hipparcos with Tycho-1

-- All stars from Tycho-1 with added Hipparcos data for those Hipparcos stars that are resolved in Tycho 
SELECT h.HIP, h.comp_id, t.TYC, t.HIP, t.m_HIP FROM (
	SELECT m.HIP, d.comp_id
	FROM hiptyc_hip_main AS m 
	LEFT JOIN hiptyc_h_dm_com AS d ON m.HIP=d.HIP
) as h
RIGHT JOIN (
	SELECT * FROM hiptyc_tyc_main WHERE LENGTH(TRIM(m_HIP)) < 2
) AS t ON t.HIP=h.hip AND t.m_HIP=COALESCE(h.comp_id, '')

UNION

-- All stars from Hipparcos that are not resolved in Tycho-1, where NULL values are inserted for the Tycho data
SELECT h.HIP, h.comp_id, NULL as TYC, NULL as HIP, NULL as m_HIP FROM (
SELECT m.HIP, d.comp_id
	FROM hiptyc_hip_main AS m 
	LEFT JOIN hiptyc_h_dm_com AS d ON m.HIP=d.HIP
) as h
LEFT JOIN (
	SELECT * FROM hiptyc_tyc_main WHERE LENGTH(TRIM(m_HIP)) > 1
) as t ON t.HIP=h.hip
WHERE t.pk is not NULL

```

