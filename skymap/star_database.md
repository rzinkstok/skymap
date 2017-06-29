# Star database

The stars plotted in SkyMap all come from the Hipparcos, Tycho and Tycho-2 catalogues published by ESA:

* The Hipparcos and Tycho Catalogues (ESA 1997), http://cdsarc.u-strasbg.fr/viz-bin/Cat?cat=I%2F239
* The Tycho-2 Catalogue of the 2.5 Million Brightest Stars, Hog et al., Astron. Astrophys. 355, L27 (2000), http://cdsarc.u-strasbg.fr/viz-bin/Cat?I/259
* Hipparcos, the new Reduction of the Raw data, van Leeuwen F., Astron. Astrophys. 474, 653 (2007), http://cdsarc.u-strasbg.fr/viz-bin/Cat?I/311

For ease of use, these were converted to MySQL databases: all queries below are performed on these databases.

## History

The Hipparcos catalogue (118218 stars) was first published in 1997, together with the larger Tycho catalogue (1058332 stars). 
In 2000, the Tycho-2 catalogue was published, containing even more stars (2539913) at a slightly higher accuracy than Tycho-1.
For all practical purposes, the newer Tycho-2 supersedes Tycho-1 completely. In 2007, an new reduction of the Hipparcos 
catalogue was published with more accurate astrometrics.

The astrometric accuracy of the Hipparcos catalogue is much better: for Hp < 9 mag, the median precision for the position 
is 0.77/0.64 mas (RA/dec), and for proper motion 0.88/0.74 mas/yr (RA/dec). The Tycho catalogue does not get better than
7 mas for stars with Vt < 9 mag. The photometric accuracy of Hipparcos is better as well: for Hp < 9 mag, the median photometric 
precision is 0.0015 mag, while Tycho-1 is limited to 0.012 mag (Vt).

## Structure of the databases

### Hipparcos
Identifier: HIP

Catalogue parts:
* Main catalogue: astrometrics, photometrics
* Double and Multiple System Annex (DMSA): component information for entries resolved into 2 or more components
* Variability Annex: variability data

### Tycho
Identifier: TYC1, TYC2, TYC3, HIP

Catalogue parts:
* Main catalogue

### Tycho-2
Identifier: TYC1, TYC2, TYC3, HIP

Catalogue parts:
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

| Description             | Number |
| ----------------------- | ------ |
| Entries with a CCDM id  |  19393 |
| Number of CCDM pairs    |   1714 |
| Number of CCDM triplets |     43 |
| Number of CCDM quartets |      5 |

Example query:

```SQL
SELECT COUNT(*) FROM (
	SELECT CCDM from hiptyc_hip_main WHERE nsys=2 GROUP BY CCDM
) t1;
```

Checking some numbers: first the total number of components 
| Description                               | Number |
| -----------------------                   | ------ |
| Components in main with CCDM id           | 30770  |
| Components in part C                      | 24588  |
| Single entry CCDM                         | 15816  |
| Single-pointing systems with 2 components | 11048  |
| Single-pointing systems with 3 components |   129  |
| Single-pointing systems with 4 components |     6  |
| 

````SQL
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

-- Number of single-pointing entries/systems with 2 components (11048; 3 components 129; 4 components 6)
SELECT COUNT(*) FROM hiptyc_hip_main WHERE Source IN ('',  'S') AND MultFlag='C' AND nComp=2;

-- Number of two- and three-pointing systems (2028)
SELECT COUNT(*) FROM hiptyc_hip_main WHERE Source IN ('F', 'I', 'L', 'P') AND MultFlag='C';
````


### Linking Tycho-2 stars to Hipparcos

A simple join of the main Hipparcos file with part C of the DMSA would yield a complete list of all resolved stars in
Hipparcos. Every record in this list is uniquely identified by the HIP identifier and the CCDM component identifier. In
principle, each of these records should correspond to an entry in the Tycho-2 main database, or it is listed in the Tycho-2
Supplement 1 (Hipparcos/Tycho-1 stars not in Tycho-2).

