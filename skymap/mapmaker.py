"""
MapMaker
\-> TikzFigure
    \-> DrawingArea
        units of mm relative to some origin
\-> AzimuthalEquidistantMap
    //vertical scale of 2 (horizontal scale is derived) mapped to the map vertical height
    bounding box in mm, vertical latitude range
    \-> AzimuthalEquidistantProjection
        //projects a specified parallel at a distance of 1 from origin
        half the latitude range, half the vertical map size (mm)
    \-> EquidistantCylindricalProjection
        half the latitude range, half the vertical map size (mm)
    \-> EquidistantConicProjection


"""

import math
import itertools

from skymap.milkyway import get_milky_way_south_boundary, get_milky_way_north_boundary, get_milky_way_holes, get_magellanic_clouds
from skymap.constellations import get_constellation_boundaries_for_area
from skymap.stars import select_stars
from skymap.map import *
from skymap.labels import LabelManager
from skymap.geometry import Rectangle
from skymap.tikz import TikzFigure

PAPERSIZES = {
    "A4": (210.0, 297.0),
    "A3": (297.0, 420.0),
    "A2": (420.0, 594.0)
}
LINEWIDTH = 0.5
FAINTEST_MAGNITUDE = 12


class SkyMapMaker(object):
    def __init__(self, filename=None, paper_size="A3", landscape=False, margin_lr=(20, 20), margin_bt=(20, 20)):
        self.filename = filename
        self.paper_size = paper_size
        self.landscape = landscape
        self.size = PAPERSIZES[paper_size]
        if landscape:
            self.size = (self.size[1], self.size[0])
        self.margin_lr = margin_lr
        self.margin_bt = margin_bt
        self.map = None
        self.figure = None
        self.labelmanager = LabelManager()

    def set_filename(self, filename):
        self.filename = filename
        basename = os.path.splitext(os.path.split(self.filename)[-1])[0]

        self.figure = TikzFigure(basename, papersize=self.paper_size, landscape=self.landscape) #MetaPostFigure(basename)

        self.drawing_area = self.figure.drawing_area(self.figure.llcorner, self.figure.urcorner-Point(80,0))

    # Map types
    def set_polar(self, filename, north=True, latitude_range=50):
        self.set_filename(filename)
        self.labelmanager = LabelManager()
        mapsize = (self.size[0]-self.margin_lr[0]-self.margin_lr[1], self.size[1]-self.margin_bt[0]-self.margin_bt[1])
        self.map = AzimuthalEquidistantMap(mapsize, (10,10), (10,10), north=north, latitude_range=latitude_range, celestial=True)

    def set_intermediate(self, filename, center, standard_parallel1=30, standard_parallel2=60, vertical_range=50):
        self.set_filename(filename)
        self.labelmanager = LabelManager()
        self.map = EquidistantConicMap(self.paper_size, self.margin_lr, self.margin_bt, center, standard_parallel1=standard_parallel1, standard_parallel2=standard_parallel2, reference_scale=vertical_range/2.0, celestial=True)

    def set_equatorial(self, filename, center_longitude, standard_parallel=25, vertical_range=50):
        self.set_filename(filename)
        self.labelmanager = LabelManager()
        self.map = EquidistantCylindricalMap(self.paper_size, self.margin_lr, self.margin_bt, center_longitude=center_longitude, standard_parallel=standard_parallel, reference_scale=vertical_range/2.0, celestial=True)

    # Drawing functions
    def draw_parallels(self, increment=10):
        print
        print "Drawing parallels"
        self.figure.comment("Parallels", True)

        min_latitude = int(increment * math.floor(self.map.min_latitude / float(increment)))
        for latitude in range(min_latitude, int(self.map.max_latitude) + 1, int(increment)):
            parallel = self.map.map_parallel(latitude)
            if isinstance(parallel, Circle):
                self.drawing_area.draw_circle(parallel, linewidth=LINEWIDTH)
            else:
                self.drawing_area.draw_line(parallel, linewidth=LINEWIDTH)
            marker = "{0}$^{{\\circ}}$".format(latitude)
            self.draw_ticks(parallel, marker, self.map.draw_parallel_ticks_on_horizontal_axis, self.map.draw_parallel_ticks_on_vertical_axis)

    def draw_meridians(self, increment=15):
        print
        print "Drawing meridians"
        self.figure.comment("Meridians", True)

        min_longitude = int(increment * math.floor(self.map.min_longitude / float(increment)))
        max_longitude = int(self.map.max_longitude)
        if max_longitude - 360 < min_longitude:
            max_longitude += 1

        for longitude in range(min_longitude, max_longitude, int(increment)):
            meridian = self.map.map_meridian(longitude)
            if isinstance(meridian, Circle):
                self.drawing_area.draw_circle(meridian, linewidth=LINEWIDTH)
            else:
                self.drawing_area.draw_line(meridian, linewidth=LINEWIDTH)
            if self.map.projection.celestial:
                ha = HourAngle()
                ha.from_degrees(longitude)
                if not longitude % 15:
                    marker = "\\textbf{{{0}\\textsuperscript{{h}}}}".format(ha.hours)

                else:
                    marker = "{0}\\textsuperscript{{m}}".format(ha.minutes)
            else:
                marker = "{0}$^{{\\circ}}$".format(longitude)
            self.draw_ticks(meridian, marker, self.map.draw_meridian_ticks_on_horizontal_axis, self.map.draw_meridian_ticks_on_vertical_axis)

    def draw_ticks(self, draw_object, text, horizontal_axis, vertical_axis):
        if horizontal_axis:
            for border, pos in [(self.map.bottom_border, "bot"), (self.map.top_border, "top")]:
                points = draw_object.inclusive_intersect_line(border)
                #for p in points:
                #    self.drawing_area.draw_text(p, text, pos, size="small", delay_write=True)
        if vertical_axis:
            for border, pos in [(self.map.right_border, "rt"), (self.map.left_border, "lft")]:
                points = draw_object.inclusive_intersect_line(border)
                #for p in points:
                #    self.drawing_area.draw_text(p, text, pos, size="small", delay_write=True)

    def draw_constellation_boundaries(self):
        print
        print "Drawing constellation borders"
        self.figure.comment("Constellation boundaries", True)

        edges = get_constellation_boundaries_for_area(self.map.min_longitude, self.map.max_longitude, self.map.min_latitude, self.map.max_latitude)
        for e in edges:
            points = [self.map.map_point(p) for p in e.interpolated_points]
            polygon = Polygon(points, closed=False)
            self.drawing_area.draw_polygon(polygon, linewidth=LINEWIDTH, dashed=True)

    def draw_stars(self):
        print
        print "Drawing stars"
        self.figure.comment("Stars")

        stars = select_stars(magnitude=FAINTEST_MAGNITUDE, constellation=None, ra_range=(self.map.min_longitude, self.map.max_longitude), dec_range=(self.map.min_latitude, self.map.max_latitude))
        for star in stars:
            # print
            # print "HIP:", star.hip
            # print "Bayer/Flamsteed:", star.bayer, star.flamsteed
            # print "Proper:", star.proper_name
            # print "Constellation:", star.constellation
            # print "Magnitude:", star.magnitude
            # print "Variable:", star.is_variable
            # print "Multiple:", star.is_multiple
            # print "Max/min magnitude:", star.max_magnitude, star.min_magnitude

            self.draw_star(star)

    def draw_star(self, star):
        p = self.map.map_point(star.position)
        if not self.map.inside_maparea(p):
            return

        # Print the star itself
        if star.is_variable:
            min_size = self.magnitude_to_size(star.min_magnitude)
            max_size = self.magnitude_to_size(star.max_magnitude)
            self.drawing_area.draw_point(p, max_size + 0.3*LINEWIDTH, color="white")
            c = Circle(p, 0.5 * max_size)
            self.drawing_area.draw_circle(c, linewidth=0.3*LINEWIDTH)
            if star.min_magnitude < FAINTEST_MAGNITUDE:
                self.drawing_area.draw_point(p, min_size)
            size = max_size
        else:
            size = self.magnitude_to_size(star.magnitude)
            self.drawing_area.draw_point(p, size + 0.3*LINEWIDTH, color="white")
            self.drawing_area.draw_point(p, size)

        # Print the multiple bar
        if star.is_multiple:
            p1 = Point(p[0] - 0.5 * size - 0.2, p[1])
            p2 = Point(p[0] + 0.5 * size + 0.2, p[1])
            l = Line(p1, p2)
            self.drawing_area.draw_line(l, linewidth=0.25)
            print "MULTIPLE:", star, star.magnitude, star.position

        o = Circle(p, 0.5 * size)
        self.labelmanager.add_object(o)

        # Print text
        if star.proper_name:
            print p
            self.labelmanager.add_label(p, star.proper_name, "tiny", extra_distance=0.5 * size - 0.7, object_for=o)
        elif star.identifier_string.strip():
            self.labelmanager.add_label(p, star.identifier_string, "tiny", extra_distance=0.5 * size - 0.7, object_for=o)

    def magnitude_to_size(self, magnitude):
        if magnitude is None:
            return 0.0
        if magnitude < -0.5:
            magnitude = -0.5
        #scale = 6.1815*self.map.paper_width/465.0
        #return scale * math.exp(-0.27 * magnitude)
        # return 0.8*(25.4/1200) * pow(4.3486 - 0.2503*magnitude, 1/0.26)

        s = -1.36913308 + (4.71252943 + 1.36913308) / pow((1 + pow((magnitude / 26.24176615), 1.28894382)), 4.82370053)
        return 0.5*s

    def split(self, curve):
        pieces = [[]]
        for i, p in enumerate(curve):
            if i > 0:
                prev_p = curve[i - 1]
                dx = abs(p.x - prev_p.x)
                if dx > 100:
                    pieces.append([])
            pieces[-1].append(p)
        return pieces

    def sort_curve(self, curve):
        pieces = self.split(curve)
        permutations = itertools.permutations([i for i in range(len(pieces))])
        for perm in permutations:
            pcurve = []
            for p in perm:
                pcurve += pieces[p]

            if len(self.split(pcurve)) == 1:
                return [pieces[i] for i in perm]

    def draw_milky_way(self):
        print
        print "Drawing milky way"
        self.figure.comment("Milky way")
        north_curve = get_milky_way_north_boundary()
        south_curve = get_milky_way_south_boundary()
        holes = get_milky_way_holes()
        magellan = get_magellanic_clouds()

        # Map all points
        north_curve = [self.map.map_point(p) for p in north_curve]
        south_curve = [self.map.map_point(p) for p in south_curve]

        self.figure.comment("Milky way fill")
        if self.map.north is None:
            north_curves = self.sort_curve(north_curve)
            south_curves = self.sort_curve(south_curve)
            curves = north_curves
            curves.extend([[p for p in reversed(c)] for c in reversed(south_curves)])
            self.figure.fill_connected_curves(curves, color="(0.6, 0.8, 1.0)")
        elif self.map.north:
            self.figure.fill_curve(south_curve, color="(0.6, 0.8, 1.0)")
            self.figure.fill_curve(north_curve, color="(1, 1, 1)")
        else:
            self.figure.fill_curve(north_curve, color="(0.6, 0.8, 1.0)")
            self.figure.fill_curve(south_curve, color="(1, 1, 1)")

        self.figure.comment("Milky way outline")
        if self.map.north is None:
            self.drawing_area.draw_connected_curves(curves, linewidth=0.5, color="black")
        else:
            self.drawing_area.draw_curve(north_curve, linewidth=LINEWIDTH, color="black")
            self.drawing_area.draw_curve(south_curve, linewidth=LINEWIDTH, color="black")

        self.figure.comment("Milky way holes")
        for h in holes:
            if len(self.split(h)) > 1:
                continue
            h = [self.map.map_point(p) for p in h]
            self.figure.fill_curve(h, color="(1, 1, 1)")
            self.drawing_area.draw_curve(h, closed=True, linewidth=0.5, color="black")

        self.figure.comment("Magellanic clouds")
        for m in magellan:
            m = [self.map.map_point(p) for p in m]
            self.figure.fill_curve(m, color="(0.6, 0.8, 1.0)")
            self.drawing_area.draw_curve(m, closed=True, linewidth=0.5, color="black")

    def render(self, open=False):
        """
        Order to draw things:

        :param open:
        :return:
        """

        self.drawing_area.clip(self.map.bounding_box())
        #self.draw_milky_way()
        self.draw_parallels()
        self.draw_meridians()
        #self.draw_constellation_boundaries()
        self.drawing_area.close_clip()

        #self.draw_stars()

        print "Drawing labels"
        #self.labelmanager.draw_labels(self.figure)

        #Clip the map area
        #llborder = Point(self.margin_lr[0], self.margin_bt[0])
        #urborder = Point(self.paper_size[0] - self.margin_lr[1], self.paper_size[1] - self.margin_bt[1])
        #self.figure.clip(llborder, urborder)

        # Draw border
        self.drawing_area.draw_bounding_box()
        self.drawing_area.draw_rectangle(self.map.bounding_box())
        #llborder = Point(self.margin_lr[0] - 10, self.margin_bt[0] - 10)
        #urborder = Point(self.paper_size[0] - self.margin_lr[1] + 10, self.paper_size[1] - self.margin_bt[1] + 10)
        #self.drawing_area.draw_rectangle(Rectangle(llborder, urborder), linewidth=1.0)

        # Create bounding box for page
        # llcorner = Point(0, 0)
        # urcorner = Point(self.paper_size[0], self.paper_size[1])
        # self.drawing_area.draw_rectangle(Rectangle(llcorner, urcorner), linewidth=0)

        # Finish
        #self.figure.end_figure()
        self.figure.render(self.filename, open=open)
