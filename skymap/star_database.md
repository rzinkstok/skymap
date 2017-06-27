# Star database

The stars plotted in SkyMap all come from the Hipparcos, Tycho and Tycho-2 catalogues published by ESA.

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
* Double and Multiple System Annex: component information for entries resolved into 2 or more components
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
solution type also indicates double stars. Aligning all this data is quite a task.

### Hipparcos multiplicity

A star can be part of a multiple system when:
* Its entry shares the CCDM identifier with one or more other entries
* It is resolved into separate components: it has one entry with number of components larger than 1
 
In the latter case, the components are described in part C of the Double and Multiple Systems Annex, which deals with
component solutions. Other parts of the Annex describe less clear solutions (acceleration terms, orbital solutions, 
variability induced movers and stochastic solutions). These are not counted as resolved.

This means multiple systems can be found by the following:
* Find all entries linked by a common CCDM identifier
* Find all entries with number of components greater than 1; these have a multiplicity flag equal to C, and their component data is found in part C of the Double and Multiple Systems Annex)

Dubious multiple systems can be found by looking at entries where 
