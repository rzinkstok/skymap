from enum import Enum
from skymap.tikz import TikzPicture
from skymap.geometry import Point, Circle, Rectangle

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
        TikzPicture.__init__(self, tikz, p1, p2, origin=p1, boxed=True)
        self.draw()

    def draw(self):
        pass


class MapBorders(object):
    def __init__(self, draw_inner=True, draw_outer=False, hmargin=0, vmargin=0):
        self.draw_inner = draw_inner
        self.draw_outer = draw_outer
        self.hmargin = hmargin
        self.vmargin = vmargin


class MapArea(TikzPicture):
    """Area on the paper used to plot a map.

    The outer area (including the border is defined by the points p1 and p2. The actual map is inset from this by
    the map margins, and this inner area is defined by the lower left, upper left, upper right and lower right
    corners.

    Origin of the area is lower left corner (p1), and a box is drawn around the map.

    Map is either bounded by a rectangle (independent of coordinate grid), or by parallels and/or meridians. This
    boundary is implemented as a clipping path. The map area that is actually added to the map is usually larger
    that the area inside the clipping path, as that is defined by longitude and latitude.

    The boundary can be provided with ticks and/or labels.

    The whole map including ticks and labels can be enclosed in a box.

    Input to the class:
    - p1, p2
    - border: MapBorders object
    - center longitude, center latitude
    - clipping path points (only for sky clipping path)
    - projection
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
        borders,
        projection,
        center_longitude,
        center_latitude,
        origin,
        clip_points=None,
    ):
        """

        Args:
            tikz: the tikz page to add the maparea to
            p1: the paper coordinates of the lower left corner
            p2: the paper coordinates of the upper right corner
            borders: the MapBorders object indicating whether to draw the outer and inner borders, and the margins to use
            projection: the map projection to use
            center_longitude:
            center_latitude:
            origin: the paper coordinates of the origin of the map, where the center longitude and latitude are mapped to
            clip_points:
        """
        self.borders = borders

        # Calculate the paper coordinates of the map corners
        minx, maxx = sorted((p1.x, p2.x))
        miny, maxy = sorted((p1.y, p2.y))
        llcorner = Point(minx, miny) + Point(self.borders.hmargin, self.borders.vmargin)
        urcorner = Point(maxx, maxy) - Point(self.borders.hmargin, self.borders.vmargin)

        # Initialize the picture from the inner map corners
        TikzPicture.__init__(
            self, tikz, llcorner, urcorner, origin=origin, boxed=self.borders.draw_inner
        )

        # Calculate the map coordinates of the map corners
        self.llcorner = Point(self.minx, self.miny)
        self.lrcorner = Point(self.maxx, self.miny)
        self.urcorner = Point(self.maxx, self.maxy)
        self.ulcorner = Point(self.minx, self.maxy)

        # Calculate the map coordinates of the outer border corners
        self.outer_llcorner = Point(
            self.minx - self.borders.hmargin, self.miny - self.borders.vmargin
        )
        self.outer_urcorner = Point(
            self.maxx + self.borders.hmargin, self.maxy + self.borders.vmargin
        )
        self.outer_border = self.borders.draw_outer

        # The center longitude and latitude
        self.center_longitude = center_longitude
        self.center_latitude = center_latitude

        self.clip_points = clip_points
        self.projection = projection

        self._longitude_latitude_boundaries()

        self.draw()

    def draw(self):
        if self.outer_border:
            self.draw_rectangle(Rectangle(self.outer_llcorner, self.outer_urcorner))

    def _map_to_paper(self, p):
        return self.origin + p

    def _paper_to_map(self, p):
        return p - self.origin

    def _sky_to_map(self, s):
        return self.projection.project(s)

    def _map_to_sky(self, p):
        return self.projection.backproject(p)

    def _paper_to_sky(self, p):
        return self._map_to_sky(self._paper_to_map(p))

    def _sky_to_paper(self, s):
        return self._map_to_paper(self._sky_to_map(s))

    def _longitude_latitude_boundaries(self):
        """Determines the min/max longitude and latitude from the  """
        # The origin corresponds to center longitude and latitude

        if not self.clip_points:
            # Clip points are map corners in paper coordinates: determine lat/long from those

            # Backproject all four map corner points
            s1 = self._map_to_sky(self.llcorner)
            s2 = self._map_to_sky(self.lrcorner)
            s3 = self._map_to_sky(self.urcorner)
            s4 = self._map_to_sky(self.ulcorner)

            # Determine minimum and maximum longitude and latitude
            min_longitude, _, _, max_longitude = sorted(
                (s1.ra.degree, s2.ra.degree, s3.ra.degree, s4.ra.degree)
            )
            min_latitude, _, _, max_latitude = sorted(
                (s1.dec.degree, s2.dec.degree, s3.dec.degree, s4.dec.degree)
            )

        else:
            # Clip points are sky coordinates
            min_longitude, _, _, max_longitude = sorted(
                [s.ra.degree for s in self.clip_points]
            )
            min_latitude, _, _, max_latitude = sorted(
                [s.dec.degree for s in self.clip_points]
            )

        return min_longitude, max_longitude, min_latitude, max_latitude


class StarMarker(object):
    def __init__(self, skycoord, magnitude):
        self.skycoord = skycoord
        self.magnitude = magnitude

    def draw(self, map_area):
        point = map_area.projection.project(self.skycoord)
        map_area.fill_circle(Circle(point, self.size(map_area)))
