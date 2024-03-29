from skymap.tikz import TikzPicture
from skymap.geometry import Point, Line, Circle, Arc, Rectangle, Label, Polygon
from skymap.map import CoordinateGridFactory, AzimuthalEquidistantProjection


class MapLegend(TikzPicture):
    def __init__(self, tikz, p1, p2):
        TikzPicture.__init__(self, tikz, p1, p2, origin=p1, boxed=True)
        self.draw()

    def draw(self):
        pass


class MapConfig(object):
    def __init__(self):
        # Variable for each map
        self._center_longitude = None
        self._center_latitude = None
        self.min_longitude = None
        self.max_longitude = None
        self.min_latitude = None
        self.max_latitude = None
        self.clipbox = None

        # Variable
        self.latitude_range_func = None
        self.coordinate_grid_config = None
        self.projection_class = None
        self.standard_parallel1 = None
        self.standard_parallel2 = None
        self.horizontal_stretch = None
        self.origin = None

        # Fixed for atlas
        self.llcorner = None
        self.urcorner = None
        self.draw_inner_border = None
        self.draw_outer_border = None
        self.inner_border_linewidth = None
        self.outer_border_linewidth = None
        self.border_vmargin = None
        self.border_hmargin = None
        self.clip_at_border = None
        self.latitude_range = None

    @property
    def center_longitude(self):
        return self._center_longitude

    @center_longitude.setter
    def center_longitude(self, val):
        if self.coordinate_grid_config is not None:
            self.coordinate_grid_config.center_longitude = val
        self._center_longitude = val

    @property
    def center_latitude(self):
        return self._center_latitude

    @center_latitude.setter
    def center_latitude(self, val):
        if self.coordinate_grid_config is not None:
            self.coordinate_grid_config.center_latitude = val
        self._center_latitude = val

    @property
    def map_width(self):
        return self.urcorner.x - self.llcorner.x - 2 * self.border_hmargin

    @property
    def map_height(self):
        return self.urcorner.y - self.llcorner.y - 2 * self.border_vmargin

    @property
    def map_llcorner(self):
        return self.llcorner + Point(self.border_hmargin, self.border_vmargin)

    @property
    def map_urcorner(self):
        return self.urcorner - Point(self.border_hmargin, self.border_vmargin)

    @property
    def reference_scale(self):
        return self.latitude_range / self.map_height

    @property
    def projection(self):
        return self.projection_class(
            center_longitude=self.center_longitude,
            center_latitude=self.center_latitude,
            standard_parallel1=self.standard_parallel1,
            standard_parallel2=self.standard_parallel2,
            reference_scale=self.reference_scale,
            horizontal_stretch=self.horizontal_stretch,
            celestial=True,
        )


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
    """

    def __init__(self, tikz, config, clip_points=None):
        """

        Args:
            tikz: the tikz page to add the maparea to
            config: the MapConfig object specifying the map
            clip_points:
        """
        self.config = config
        self.projection = self.config.projection

        # Calculate the paper coordinates of the map corners
        minx, maxx = sorted((config.llcorner.x, config.urcorner.x))
        miny, maxy = sorted((config.llcorner.y, config.urcorner.y))
        llcorner = Point(minx, miny) + Point(
            self.config.border_hmargin, self.config.border_vmargin
        )
        urcorner = Point(maxx, maxy) - Point(
            self.config.border_hmargin, self.config.border_vmargin
        )

        # Initialize the picture from the inner map corners
        TikzPicture.__init__(
            self,
            tikz,
            llcorner,
            urcorner,
            origin=config.origin,
            boxed=self.config.draw_inner_border,
            box_linewidth=self.config.inner_border_linewidth,
        )

        # Calculate the map coordinates of the outer border corners
        self.outer_llcorner = Point(
            self.minx - self.config.border_hmargin,
            self.miny - self.config.border_vmargin,
        )
        self.outer_urcorner = Point(
            self.maxx + self.config.border_hmargin,
            self.maxy + self.config.border_vmargin,
        )
        self.outer_border = self.config.draw_outer_border

        # The center longitude and latitude
        self.center_longitude = config.center_longitude
        self.center_latitude = config.center_latitude

        self.clip_points = clip_points

        self._longitude_latitude_boundaries()
        self.latitude_range_func = config.latitude_range_func

        self.draw()

    def draw(self):
        if self.outer_border:
            old_linewidth = self.linewidth
            self.linewidth = self.config.outer_border_linewidth
            self.draw_rectangle(Rectangle(self.outer_llcorner, self.outer_urcorner))
            self.linewidth = old_linewidth

        if self.config.clipbox is not None:
            with self.clip(self.config.clipbox):
                self.draw_grid()
        else:
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
        """Determines the min/max longitude and latitude displayed in the map."""
        # The origin corresponds to center longitude and latitude

        if self.config.clip_at_border:
            # Clip points are map corners in paper coordinates: determine lat/long from those
            # TODO: This only works correctly for specific maps!
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

        else:
            # Clip points are sky coordinates
            longitudes = [self.config.min_longitude, self.config.max_longitude]
            latitudes = [self.config.min_latitude, self.config.max_latitude]

        # Make sure the center longitudes and latitudes are included
        longitudes.append(self.center_longitude)
        latitudes.append(self.center_latitude)

        # Make sure the longitudes do not include a discontinuity
        continuous_longitudes = []
        for l in longitudes:
            if l - self.center_longitude > 180:
                continuous_longitudes.append(l - 360)
            elif l - self.center_longitude < -180:
                continuous_longitudes.append(l + 360)
            else:
                continuous_longitudes.append(l)

        self.min_longitude = min(continuous_longitudes)
        self.max_longitude = max(continuous_longitudes)
        self.min_latitude = min(latitudes)
        self.max_latitude = max(latitudes)

        # For azimuthal projections, make sure all longitudes are included
        if isinstance(self.projection, AzimuthalEquidistantProjection):
            self.min_longitude = 0
            self.max_longitude = 360

        print("Grid range")
        print(f"Longitude: {self.min_longitude} to {self.max_longitude}")
        print(f"Latitude: {self.min_latitude} to {self.max_latitude}")

    def draw_grid_element(self, item, pen_style=None):
        if item is None:
            return

        prev_pen_style = self.pen_style
        if pen_style is not None:
            self.pen_style = pen_style

        if isinstance(item, Line):
            self.draw_line(item)
        elif isinstance(item, Arc):
            self.draw_arc(item)
        elif isinstance(item, Circle):
            self.draw_circle(item)
        elif isinstance(item, Label):
            self.draw_label(item)
        elif isinstance(item, Polygon):
            self.draw_polygon(item)
        else:
            raise NotImplementedError(f"Cannot draw {item}")

        self.pen_style = prev_pen_style

    def draw_grid(self):
        factory = CoordinateGridFactory(
            self.config.coordinate_grid_config,
            self.projection,
            self.borderdict,
            self.config.clip_at_border,
            self.clipper,
            (self.min_longitude, self.max_longitude),
            (self.min_latitude, self.max_latitude),
            self.latitude_range_func,
        )

        old_linewidth = self.linewidth
        self.linewidth = self.config.coordinate_grid_config.linewidth

        for m in factory.meridians:
            self.comment(f"Meridian at {m.coordinate}")
            self.draw_grid_element(m.curve)
            self.draw_grid_element(m.tick1)
            self.draw_grid_element(m.tick2)
            self.draw_grid_element(m.label1)
            self.draw_grid_element(m.label2)

        for p in factory.parallels:
            self.comment(f"Parallel at {p.coordinate}")
            self.draw_grid_element(p.curve)
            self.draw_grid_element(p.tick1)
            self.draw_grid_element(p.tick2)
            self.draw_grid_element(p.internal_tick)
            self.draw_grid_element(p.label1)
            self.draw_grid_element(p.label2)
            self.draw_grid_element(p.internal_label)

        self.comment("Polar ticks")
        self.draw_grid_element(factory.polar_tick)
        self.draw_grid_element(factory.polar_label)

        self.comment("Galactic equator")
        self.draw_grid_element(
            factory.galactic_equator,
            pen_style=self.config.coordinate_grid_config.galactic_pen_style,
        )

        self.comment("Ecliptic equator")
        self.draw_grid_element(
            factory.ecliptic_equator,
            pen_style=self.config.coordinate_grid_config.ecliptic_pen_style,
        )

        for p in factory.galactic_meridians:
            self.comment(f"Galactic equator tick at {p.longitude}")
            self.draw_grid_element(p.tick)
            self.draw_grid_element(p.label)

        self.comment(f"Galactic poles")
        for p in factory.galactic_poles:
            self.draw_grid_element(p)

        for p in factory.ecliptic_meridians:
            self.comment(f"Ecliptic equator tick at {p.longitude}")
            self.draw_grid_element(p.tick)
            self.draw_grid_element(p.label)

        self.linewidth = old_linewidth
