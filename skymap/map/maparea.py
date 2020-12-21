import math
from skymap.tikz import TikzPicture
from skymap.geometry import Point, Line, Circle, Arc, Rectangle, Label
from skymap.map import CoordinateGridFactory


class MapLegend(TikzPicture):
    def __init__(self, tikz, p1, p2):
        TikzPicture.__init__(self, tikz, p1, p2, origin=p1, boxed=True)
        self.draw()

    def draw(self):
        pass


class MapBorderConfig(object):
    def __init__(
        self,
        draw_inner=True,
        draw_outer=False,
        inner_linewidth=0.25,
        outer_linewidth=0.5,
        hmargin=0,
        vmargin=0,
    ):
        self.draw_inner = draw_inner
        self.draw_outer = draw_outer
        self.outer_linewidth = outer_linewidth
        self.inner_linewidth = inner_linewidth
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
        border_config,
        coordinate_grid_config,
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
            border_config: the MapBorderConfig object
            coordinate_grid_config: the CoordinateGridConfig indicating all info on the meridians and parallels
            projection: the map projection to use
            center_longitude:
            center_latitude:
            origin: the paper coordinates of the map origin, where the center longitude and latitude are mapped to
            clip_points:
        """
        self.border_config = border_config
        self.coordinate_grid_config = coordinate_grid_config
        self.projection = projection

        # Calculate the paper coordinates of the map corners
        minx, maxx = sorted((p1.x, p2.x))
        miny, maxy = sorted((p1.y, p2.y))
        llcorner = Point(minx, miny) + Point(
            self.border_config.hmargin, self.border_config.vmargin
        )
        urcorner = Point(maxx, maxy) - Point(
            self.border_config.hmargin, self.border_config.vmargin
        )

        # Initialize the picture from the inner map corners
        TikzPicture.__init__(
            self,
            tikz,
            llcorner,
            urcorner,
            origin=origin,
            boxed=self.border_config.draw_inner,
            box_linewidth=self.border_config.inner_linewidth,
        )

        # Calculate the map coordinates of the outer border corners
        self.outer_llcorner = Point(
            self.minx - self.border_config.hmargin,
            self.miny - self.border_config.vmargin,
        )
        self.outer_urcorner = Point(
            self.maxx + self.border_config.hmargin,
            self.maxy + self.border_config.vmargin,
        )
        self.outer_border = self.border_config.draw_outer

        # The center longitude and latitude
        self.center_longitude = center_longitude
        self.center_latitude = center_latitude

        self.clip_points = clip_points

        self._longitude_latitude_boundaries()

        self.draw()

    def draw(self):
        if self.outer_border:
            old_linewidth = self.linewidth
            self.linewidth = self.border_config.outer_linewidth
            self.draw_rectangle(Rectangle(self.outer_llcorner, self.outer_urcorner))
            self.linewidth = old_linewidth

        self.draw_grid()

    def _sky_to_map(self, s):
        return self.projection.project(s)

    def _map_to_sky(self, p):
        return self.projection.backproject(p)

    def _paper_to_sky(self, p):
        return self._map_to_sky(self._paper_to_picture(p))

    def _sky_to_paper(self, s):
        return self._picture_to_paper(self._sky_to_map(s))

    def _longitude_latitude_boundaries(self):
        """Determines the min/max longitude and latitude displayed in the map.
        """
        # The origin corresponds to center longitude and latitude

        if not self.clip_points:
            # Clip points are map corners in paper coordinates: determine lat/long from those
            pts = [
                # Backproject all four map corner points
                self._map_to_sky(self.llcorner),
                self._map_to_sky(self.lrcorner),
                self._map_to_sky(self.urcorner),
                self._map_to_sky(self.ulcorner),
                # Backproject the top and bottom border points at the x-coordinate of the origin
                self._map_to_sky(Point(0, self.llcorner.y)),
                self._map_to_sky(Point(0, self.ulcorner.y)),
            ]

            # Determine minimum and maximum longitude and latitude
            longitudes = [s.ra.degree for s in pts]
            latitudes = [s.dec.degree for s in pts]

            # Make sure the longitudes do not include a discontinuity
            longitudes = [
                l if math.fabs(l - self.center_longitude) < 180 else l - 360
                for l in longitudes
            ]

            self.min_longitude = min(longitudes)
            self.max_longitude = max(longitudes)
            self.min_latitude = min(latitudes)
            self.max_latitude = max(latitudes)

        else:
            # Clip points are sky coordinates
            self.min_longitude, _, _, self.max_longitude = sorted(
                [s.ra.degree for s in self.clip_points]
            )
            self.min_latitude, _, _, self.max_latitude = sorted(
                [s.dec.degree for s in self.clip_points]
            )

        print(f"Longitude range: {self.min_longitude} - {self.max_longitude}")
        print(f"Latitude range: {self.min_latitude} - {self.max_latitude}")

    def draw_grid_element(self, item):
        if item is None:
            return
        if isinstance(item, Line):
            self.draw_line(item)
        elif isinstance(item, Arc):
            self.draw_arc(item)
        elif isinstance(item, Circle):
            self.draw_circle(item)
        elif isinstance(item, Label):
            self.draw_label(item)
        else:
            raise NotImplementedError

    def draw_grid(self):
        factory = CoordinateGridFactory(
            self.coordinate_grid_config,
            self.projection,
            self.borderdict,
            self.clipper,
            (self.min_longitude, self.max_longitude),
            (self.min_latitude, self.max_latitude),
        )

        old_linewidth = self.linewidth
        self.linewidth = self.coordinate_grid_config.linewidth

        for m in factory.meridians:
            self.draw_grid_element(m.curve)
            self.draw_grid_element(m.tick1)
            self.draw_grid_element(m.tick2)
            self.draw_grid_element(m.label1)
            self.draw_grid_element(m.label2)

        for p in factory.parallels:
            self.draw_grid_element(p.curve)
            self.draw_grid_element(p.tick1)
            self.draw_grid_element(p.tick2)
            self.draw_grid_element(p.label1)
            self.draw_grid_element(p.label2)

        self.linewidth = old_linewidth
