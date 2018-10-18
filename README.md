# skymap
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/cb07daea7f49492480cdc62a2f8a6ad5)](https://app.codacy.com/app/rzinkstok/skymap?utm_source=github.com&utm_medium=referral&utm_content=rzinkstok/skymap&utm_campaign=Badge_Grade_Dashboard)
[![Build Status](https://travis-ci.org/rzinkstok/skymap.svg?branch=master)](https://travis-ci.org/rzinkstok/skymap)
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
 