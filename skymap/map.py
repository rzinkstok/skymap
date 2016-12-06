import os
import math
from skymap.geometry import Point, SphericalPoint, Line, Circle, Arc, HourAngle
from skymap.metapost import MetaPostFigure
from skymap.projections import AzimuthalEquidistantProjection, EquidistantCylindricalProjection, EquidistantConicProjection
from skymap.constellations import get_constellation_boundaries_for_area
from skymap.hyg import select_stars

A4_SIZE = (297.0, 210.0)
FAINTEST_MAGNITUDE = 8


class Map(object):
    def __init__(self, filename, projection, paper_width=A4_SIZE[0], paper_height=A4_SIZE[1], margin_left=20, margin_bottom=20, margin_right=None, margin_top=None):
        self.filename = filename

        self.set_projection(projection)
        self.set_paper_size(paper_width, paper_height)
        self.set_margins(margin_left, margin_bottom, margin_right, margin_top)

        self.min_longitude = None
        self.max_longitude = None
        self.min_latitude = None
        self.max_latitude = None

        self.set_origin(Point(paper_width/2.0, paper_height/2.0))
        self.set_scale(2.0)

        basename = os.path.splitext(os.path.split(self.filename)[-1])[0]
        self.figure = MetaPostFigure(basename)

        self.draw_parallel_ticks_on_vertical_axis = True
        self.draw_parallel_ticks_on_horizontal_axis = False
        self.draw_meridian_ticks_on_vertical_axis = False
        self.draw_meridian_ticks_on_horizontal_axis = True

    def set_projection(self, projection):
        self.projection = projection

    def set_paper_size(self, paper_width, paper_height):
        self.paper_width = paper_width
        self.paper_height = paper_height

    def set_margins(self, margin_left, margin_bottom, margin_right=None, margin_top=None):
        self.margin_left = margin_left
        self.margin_bottom = margin_bottom
        if margin_right:
            self.margin_right = margin_right
        else:
            self.margin_right = margin_left
        if margin_top:
            self.margin_top = margin_top
        else:
            self.margin_top = margin_bottom
        self.map_size_x = float(self.paper_width - self.margin_left - self.margin_right)
        self.map_size_y = float(self.paper_height - self.margin_bottom - self.margin_top)

        self.map_ll_corner = Point(self.margin_left, self.margin_bottom)
        self.map_lr_corner = Point(self.paper_width - self.margin_right, self.margin_bottom)
        self.map_ur_corner = Point(self.paper_width - self.margin_right, self.paper_height - self.margin_top)
        self.map_ul_corner = Point(self.margin_left, self.paper_height - self.margin_top)

        self.bottom_border = Line(self.map_ll_corner, self.map_lr_corner)
        self.right_border = Line(self.map_lr_corner, self.map_ur_corner)
        self.top_border = Line(self.map_ur_corner, self.map_ul_corner)
        self.left_border = Line(self.map_ul_corner, self.map_ll_corner)

    def set_origin(self, origin):
        self.origin = origin

    def set_scale(self, scale):
        self.conversion = scale/self.map_size_x

        self.extent_x = self.conversion * self.map_size_x
        self.min_x = self.conversion * (self.margin_left - self.origin.x)
        self.max_x = self.min_x + self.extent_x

        self.extent_y = self.conversion * self.map_size_y
        self.min_y = self.conversion * (self.margin_bottom - self.origin.y)
        self.max_y = self.min_y + self.extent_y

    def point_to_paper(self, p):
        """Convert planar coordinates to a location on the map"""
        x, y = p
        map_x = self.margin_left + self.map_size_x * (x - self.min_x) / self.extent_x
        map_y = self.margin_bottom + self.map_size_y * (y - self.min_y) / self.extent_y
        return Point(map_x, map_y)

    def distance_to_paper(self, d):
        return self.point_to_paper(Point(0, 0)).distance(self.point_to_paper(Point(0, d)))

    def point_from_paper(self, map_p):
        """Convert a location on the map to planar coordinates"""
        map_x, map_y = map_p
        x = self.min_x + self.extent_x * (map_x - self.margin_left) / self.map_size_x
        y = self.min_y + self.extent_y * (map_y - self.margin_bottom) / self.map_size_y
        return Point(x, y)

    def inside_viewport(self, p):
        """Check whether the given point lies within the map area"""
        if p.x < self.margin_left or p.x > self.margin_left+self.map_size_x or p.y < self.margin_bottom or p.y > self.margin_bottom+self.map_size_y:
            return False
        else:
            return True

    def draw_object_to_paper(self, draw_object):
        try:
            return self.line_to_paper(draw_object)
        except AttributeError:
            pass
        try:
            return self.circle_to_paper(draw_object)
        except AttributeError:
            pass

    def line_to_paper(self, line):
        return Line(self.point_to_paper(line.p1), self.point_to_paper(line.p2))

    def circle_to_paper(self, circle):
        return Circle(self.point_to_paper(circle.center), self.distance_to_paper(circle.radius))

    def arc_to_paper(self, arc):
        return Arc(self.point_to_paper(arc.center), self.distance_to_paper(arc.radius), arc.start_angle, arc.stop_angle)

    def draw(self, draw_object, **kwargs):
        try:
            self.figure.draw_line(self.line_to_paper(draw_object), **kwargs)
            return
        except AttributeError:
            pass
        try:
            self.figure.draw_arc(self.arc_to_paper(draw_object), **kwargs)
            return
        except AttributeError:
            pass
        try:
            self.figure.draw_circle(self.circle_to_paper(draw_object), **kwargs)
            return
        except AttributeError:
            pass
        raise RuntimeError("Could not draw {}".format(draw_object))

    def draw_parallels(self):
        print
        print "Drawing parallels"
        self.figure.comment("Parallels", True)
        for latitude in range(int(self.min_latitude), int(self.max_latitude)+1, 10):
            parallel = self.projection.parallel(latitude)
            self.draw(parallel, linewidth=0.2)
            marker = "{0}$^{{\\circ}}$".format(latitude)
            self.draw_ticks(parallel, marker, self.draw_parallel_ticks_on_horizontal_axis, self.draw_parallel_ticks_on_vertical_axis)

    def draw_meridians(self):
        print
        print "Drawing meridians"
        self.figure.comment("Meridians", True)
        for longitude in range(int(self.min_longitude), int(self.max_longitude)+1, 15):
            meridian = self.projection.meridian(longitude)
            self.draw(meridian, linewidth=0.2)
            if self.projection.celestial:
                ha = HourAngle()
                ha.from_degrees(longitude)
                if not longitude % 15:
                    marker = "\\textbf{{{0}\\textsuperscript{{h}}}}".format(ha.hours)

                else:
                    marker = "{0}\\textsuperscript{{m}}".format(ha.minutes)
            else:
                marker = "{0}$^{{\\circ}}$".format(longitude)
            self.draw_ticks(meridian, marker, self.draw_meridian_ticks_on_horizontal_axis, self.draw_meridian_ticks_on_vertical_axis)

    def draw_ticks(self, draw_object, text, horizontal_axis, vertical_axis):
        draw_object = self.draw_object_to_paper(draw_object)
        if horizontal_axis:
            for border, pos in [(self.bottom_border, "bot"), (self.top_border, "top")]:
                points = draw_object.inclusive_intersect_line(border)
                for p in points:
                    self.figure.draw_text(p, text, pos, size="small", delay_write=True)
        if vertical_axis:
            for border, pos in [(self.right_border, "rt"), (self.left_border, "lft")]:
                points = draw_object.inclusive_intersect_line(border)
                for p in points:
                    self.figure.draw_text(p, text, pos, size="small", delay_write=True)

    def draw_constellation_boundaries(self, constellation=None):
        print
        print "Drawing constellation borders"
        self.figure.comment("Constellation boundaries", True)
        drawn_edges = []
        edges = get_constellation_boundaries_for_area(self.min_longitude, self.max_longitude, self.min_latitude, self.max_latitude, constellation=constellation)
        for e in edges:
            if e.identifier in drawn_edges:
                continue
            points = [self.point_to_paper(self.projection.project(p)) for p in e.interpolated_points]
            self.figure.draw_polygon(points, closed=False, linewidth=0.2, dashed=True)
            drawn_edges.append(e.identifier)
            drawn_edges.append(e.complement)

    def draw_stars(self):
        print
        print "Drawing stars"
        self.figure.comment("Stars")
        stars = select_stars(magnitude=FAINTEST_MAGNITUDE, constellation=None, ra_range=(self.min_longitude, self.max_longitude), dec_range=(self.min_latitude, self.max_latitude))
        for star in stars:
            self.draw_star(star)

    def draw_star(self, star):
        p = self.point_to_paper(self.projection.project(star.position))
        if not self.inside_viewport(p):
            return

        # Print the star itself
        if star.is_variable:
            min_size = self.magnitude_to_size(star.var_min)
            max_size = self.magnitude_to_size(star.var_max)
            self.figure.draw_point(p, max_size + 0.15, color="white")
            c = Circle(p, 0.5 * max_size)
            self.figure.draw_circle(c, linewidth=0.15)
            if star.var_min < FAINTEST_MAGNITUDE:
                self.figure.draw_point(p, min_size)
            size = max_size
        else:
            size = self.magnitude_to_size(star.mag)
            self.figure.draw_point(p, size + 0.15, color="white")
            self.figure.draw_point(p, size)

        # Print the multiple bar
        if star.is_multiple:
            p1 = Point(p[0] - 0.5 * size - 0.2, p[1])
            p2 = Point(p[0] + 0.5 * size + 0.2, p[1])
            l = Line(p1, p2)
            self.figure.draw_line(l, linewidth=0.25)
            print "MULTIPLE:", star, star.mag, star.position

        # Print text
        if star.identifier_string.strip():
            text_pos = Point(p.x + 0.5 * size - 0.9, p.y)
            self.figure.draw_text(text_pos, star.identifier_string, "rt", "tiny", scale=0.75, delay_write=True)
        if star.proper:
            text_pos = Point(p.x, p.y - 0.5 * size + 0.8)
            self.figure.draw_text(text_pos, star.proper, "bot", "tiny", scale=0.75, delay_write=True)

    def magnitude_to_size(self, magnitude):
        if magnitude < -0.5:
            magnitude = -0.5
        scale = 6.1815*self.paper_width/465.0
        return scale * math.exp(-0.27 * magnitude)

    def render(self):
        # Draw the coordinate grid
        self.draw_parallels()
        self.draw_meridians()

        self.draw_constellation_boundaries()

        self.draw_stars()

        # Clip the map area
        llborder = Point(self.margin_left, self.margin_bottom)
        urborder = Point(self.paper_width - self.margin_right, self.paper_height - self.margin_top)
        self.figure.clip(llborder, urborder)

        # Draw border
        self.figure.draw_rectange(llborder, urborder)

        # Create bounding box for page
        llcorner = Point(0, 0)
        urcorner = Point(self.paper_width, self.paper_height)
        self.figure.draw_rectange(llcorner, urcorner, linewidth=0)

        # Finish
        self.figure.end_figure()
        self.figure.render(self.filename)


class AzimuthalEquidistantMap(Map):
    def __init__(self, filename, north=True, celestial=False, paper_width=A4_SIZE[0], paper_height=A4_SIZE[1], margin_left=20, margin_bottom=20, margin_right=None, margin_top=None, reference_longitude=0, reference_scale=45):
        p = AzimuthalEquidistantProjection(north=north, celestial=celestial, reference_longitude=reference_longitude, reference_scale=reference_scale)

        Map.__init__(self, filename, p, paper_width, paper_height, margin_left, margin_bottom, margin_right, margin_top)

        self.min_longitude = 0
        self.max_longitude = 360
        if north:
            self.min_latitude = 0
            self.max_latitude = 90
        else:
            self.min_latitude = -90
            self.max_latitude = 0

        self.draw_parallel_ticks_on_vertical_axis = False
        self.draw_meridian_ticks_on_vertical_axis = True


class EquidistantCylindricalMap(Map):
    def __init__(self, filename, celestial=False, paper_width=A4_SIZE[0], paper_height=A4_SIZE[1], margin_left=25, margin_bottom=20, margin_right=None, margin_top=None, standard_parallel=20, reference_longitude=0, reference_scale=30):
        margin_left = 0.5*(paper_width - (paper_height - 2*margin_bottom)*1.5)
        p = EquidistantCylindricalProjection(celestial=celestial, standard_parallel=standard_parallel, reference_longitude=reference_longitude, reference_scale=reference_scale)

        Map.__init__(self, filename, p, paper_width, paper_height, margin_left, margin_bottom, margin_right, margin_top)

        self.min_longitude = reference_longitude - reference_scale
        self.max_longitude = reference_longitude + reference_scale
        self.min_latitude = -reference_scale * self.map_size_y / self.map_size_x
        self.max_latitude = reference_scale * self.map_size_y / self.map_size_x


class EquidistantConicMap(Map):
    def __init__(self, filename, celestial=False, paper_width=A4_SIZE[0], paper_height=A4_SIZE[1], margin_left=25, margin_bottom=20, margin_right=None, margin_top=None, standard_parallel1=30, standard_parallel2=60, reference_longitude=0):
        p = EquidistantConicProjection(celestial=celestial, reference_longitude=reference_longitude, standard_parallel1=standard_parallel1, standard_parallel2=standard_parallel2)
        Map.__init__(self, filename, p, paper_width, paper_height, margin_left, margin_bottom, margin_right, margin_top)
        self.set_scale(1.0)
        self.min_longitude = reference_longitude - 120
        self.max_longitude = reference_longitude + 120
        if p.reference_latitude > 0:
            self.min_latitude = -70
            self.max_latitude = 90
        else:
            self.min_latitude = -90
            self.max_latitude = 70

