# skymap
[![Documentation Status](https://readthedocs.org/projects/skymap/badge/?version=latest)](https://skymap.readthedocs.io/en/latest/?badge=latest)

Generate star charts based on Hipparcos/Tycho data

[Star database](skymap/stars/star_database.md)

## Moving to astropy

* Coordinates: should be transformed to astropy.coordinates. Precession not really needed.
* Database: should be converted to astroquery
* Geometry: SphericalPoint, HourAngle, DMSAngle should be converted to astropy.coordinates.
* Projections: should be adapted to use astropy.coordinates
* Constellations; precession to B1875 can be done in astropy (see get_constellation function). Rest of functionality in
 
## Installation
Dependencies:
* libspatialindex
* xelatex
 