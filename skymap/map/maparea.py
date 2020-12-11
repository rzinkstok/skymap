from enum import Enum
from skymap.tikz import TikzPicture
from skymap.geometry import Point, Circle

"""

MapArea
    Projection
    Gridlines/axes
    Border with gridline labels etc
    
    plot a point
    plot a line
    plot a circle
    


"""


class MapLegend(TikzPicture):
    def __init__(self, tikz, p1, p2):
        TikzPicture.__init__(self, tikz, p1, p2, origin=None, boxed=True)
        self.draw()

    def draw(self):
        pass


class MapAreaClipMode(Enum):
    paper = 1
    sky = 2


class MapMargins(object):
    def __init__(self, horizontal, vertical):
        self.horizontal = horizontal
        self.vertical = vertical

    def __getitem__(self, key):
        if key == 0:
            return self.horizontal
        if key == 1:
            return self.vertical
        raise IndexError


class MapArea(TikzPicture):
    """Area on the paper used to plot a map.
    Area is defined by the points p1 and p2.
    Origin of the area is lower left corner (p1), and a box is drawn around the map.

    Map is either bounded by a rectangle (independent of coordinate grid), or by parallels and/or meridians. This
    boundary is implemented as a clipping path. The map area that is actually added to the map is usually larger
    that the area inside the clipping path, as that is defined by longitude and latitude.

    The boundary can be provided with ticks and/or labels.

    The whole map including ticks and labels can be enclosed in a box.

    Input to the class:
    - p1, p2
    - boxed
    - center longitude, center latitude
    - clipping path type (paper or sky)
    - clipping path points (only for sky clipping path)
    - projection
    - min/max latitude (maybe determined from clipping path?)
    - min/max longitude (maybe determined from clipping path?)
    - ...



    Objects to place:
      - Box
      - Border
      - Ticks and numbers
      - Meridians and parallels
      - Ecliptic, galactic equator
      - Constellation boundaries
      - Stars
      - Galaxies
      - Other objects
    """

    def __init__(
        self,
        tikz,
        p1,
        p2,
        projection,
        center_longitude,
        center_latitude,
        origin,
        map_margins,
        # clipmode,
        clip_points=None,
        boxed=True,
    ):
        TikzPicture.__init__(self, tikz, p1, p2, origin=origin, boxed=boxed)
        self.center_longitude = center_longitude
        self.center_latitude = center_latitude
        self.map_margins = map_margins
        # self.clipmode = clipmode
        self.clip_points = clip_points
        self.projection = projection

        # Paper coordinates of map corners
        self.llcorner = Point(self.minx, self.miny) + Point(*self.map_margins)
        self.lrcorner = Point(self.maxx, self.miny) + Point(
            -self.map_margins[0], self.map_margins[1]
        )
        self.urcorner = Point(self.maxx, self.maxy) - Point(*self.map_margins)
        self.ulcorner = Point(self.minx, self.maxy) + Point(
            self.map_margins[0], -self.map_margins[1]
        )

        self._longitude_latitude_boundaries()

    def _map_to_paper(self, p):
        return self.origin + p

    def _paper_to_map(self, p):
        return p - self.origin

    def _sky_to_map(self, s):
        return self.projection.project(s)

    def _map_to_sky(self, p):
        return self.projection.backproject(p)

    def _paper_to_sky(self, p):
        return self._paper_to_map(self._map_to_sky(p))

    def _sky_to_paper(self, s):
        return self._sky_to_map(self._map_to_paper(s))

    def _longitude_latitude_boundaries(self):
        # origin correspnds to center longitude and latitude
        if not self.clip_points:  # self.clipmode == MapAreaClipMode.paper:
            # Clip points are map corners in paper coordinates: determine lat/long from those

            # Backproject all four map corner points
            s1 = self._paper_to_sky(self.llcorner)
            s2 = self._paper_to_sky(self.lrcorner)
            s3 = self._paper_to_sky(self.urcorner)
            s4 = self._paper_to_sky(self.ulcorner)

            # Determine minimum and maximum longitude and latitude
            min_longitude = min(
                s1.dec.degree, s2.dec.degree, s3.dec.degree, s4.dec.degree
            )
            max_longitude = max(
                s1.dec.degree, s2.dec.degree, s3.dec.degree, s4.dec.degree
            )
            min_latitude = min(s1.ra.degree, s2.ra.degree, s3.ra.degree, s4.ra.degree)
            max_latitude = max(s1.ra.degree, s2.ra.degree, s3.ra.degree, s4.ra.degree)

        else:
            # Clip points are sky coordinates
            min_longitude = min([s.dec.degree for s in self.clip_points])
            max_longitude = min([s.dec.degree for s in self.clip_points])
            min_latitude = min([s.dec.degree for s in self.clip_points])
            max_latitude = min([s.dec.degree for s in self.clip_points])

        return min_longitude, max_longitude, min_latitude, max_latitude


class StarMarker(object):
    def __init__(self, skycoord, magnitude):
        self.skycoord = skycoord
        self.magnitude = magnitude

    def draw(self, map_area):
        point = map_area.projection.project(self.skycoord)
        map_area.fill_circle(Circle(point, self.size(map_area)))
