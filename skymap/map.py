import os
import math
import numpy
from operator import xor
from skymap.tikz import DrawingArea, DrawError
from skymap.geometry import Point, SphericalPoint, Line, Circle, Arc, Rectangle, ensure_angle_range
from skymap.projections import AzimuthalEquidistantProjection, EquidistantCylindricalProjection, EquidistantConicProjection, UnitProjection
from skymap.gridlines import GridLineFactory, Label
from skymap.constellations import get_constellation_boundaries_for_area


class MapArea(DrawingArea):
    def __init__(self, p1, p2, origin=None, hmargin=0, vmargin=0, box=True):
        if origin is None:
            origin = 0.5 * (p1 + p2)
        DrawingArea.__init__(self, p1, p2, origin, box)

        # Total map
        self.map_hmargin = hmargin
        self.map_vmargin = vmargin

        # Central map area
        self.map_width = float(self.width - 2 * self.map_hmargin)
        self.map_height = float(self.height - 2 * self.map_vmargin)

        self.map_minx = self.p1.x + self.map_hmargin - self.origin.x
        self.map_maxx = self.map_minx + self.map_width
        self.map_miny = self.p1.y + self.map_vmargin - self.origin.y
        self.map_maxy = self.map_miny + self.map_height

        self.map_llcorner = Point(self.map_minx, self.map_miny)
        self.map_lrcorner = Point(self.map_maxx, self.map_miny)
        self.map_urcorner = Point(self.map_maxx, self.map_maxy)
        self.map_ulcorner = Point(self.map_minx, self.map_maxy)

        self.map_bottom_border = Line(self.map_llcorner, self.map_lrcorner)
        self.map_right_border = Line(self.map_lrcorner, self.map_urcorner)
        self.map_top_border = Line(self.map_urcorner, self.map_ulcorner)
        self.map_left_border = Line(self.map_ulcorner, self.map_llcorner)

        self.map_box = Rectangle(self.map_llcorner, self.map_urcorner)

        self.projection = UnitProjection()

        # Longitude/latitude ranges
        self.min_longitude = None
        self.max_longitude = None
        self.min_latitude = None
        self.max_latitude = None

        # Longitude/latitude grid
        self.gridline_factory = GridLineFactory()
        self.gridline_factory.marked_ticksize = 1.0
        self.gridline_factory.unmarked_ticksize = 0.5
        self.gridline_factory.meridian_line_interval = 15  # 1 hour
        self.gridline_factory.meridian_marked_tick_interval = 5  # 20 minutes
        self.gridline_factory.meridian_tick_interval = 1.25  # 5 minutes
        self.gridline_factory.parallel_line_interval = 10
        self.gridline_factory.parallel_marked_tick_interval = 10
        self.gridline_factory.parallel_tick_interval = 1

        self.parallel_ticks = {'left': True, 'right': True, 'bottom': False, 'top': False}
        self.meridian_ticks = {'left': False, 'right': False, 'bottom': True, 'top': True}

        self.gridline_thickness = 0.3

    def open(self):
        DrawingArea.open(self)
        if self.box and (self.map_hmargin>0 or self.map_vmargin>0):
            self.draw_map_box()

    def set_projection(self, projection):
        self.projection = projection
        self.calculate_corner_coordinates()

    def inside_maparea(self, p):
        """Check whether the given point lies within the map area"""
        if p.x < self.map_minx or p.x > self.map_maxx or p.y < self.map_miny or p.y > self.map_maxy:
            return False
        else:
            return True

    def map_point(self, spherical_point):
        return self.projection(spherical_point)

    def map_distance(self, distance):
        p1 = self.map_point(SphericalPoint(0, 0))
        p2 = self.map_point(SphericalPoint(0, distance))
        return p1.distance(p2)

    def map_line(self, line):
        p1 = self.map_point(line.p1)
        p2 = self.map_point(line.p2)
        return Line(p1, p2)

    def map_circle(self, circle):
        """This is a parallel circle...."""
        radius = self.map_distance(circle.radius)
        center = self.map_point(circle.center)
        return Circle(center, radius)

    def draw_map_box(self):
        self.draw_rectangle(self.map_box, linewidth=self.gridline_thickness)

    def line_intersect_borders(self, line):
        borderpos = [
            (self.map_left_border, 'left'),
            (self.map_top_border, 'top'),
            (self.map_right_border, 'right'),
            (self.map_bottom_border, 'bottom')
        ]

        crossings = []
        labelpositions = []

        for b, pos in borderpos:
            c = b.inclusive_intersect_line(line)
            if len(c) == 1:
                if c[0] not in crossings:
                    crossings.append(c[0])
                    labelpositions.append(pos)

        return zip(crossings, labelpositions)

    def circle_intersect_borders(self, circle):
        borderdict = {
            'left': self.map_left_border,
            'top': self.map_top_border,
            'right': self.map_right_border,
            'bottom': self.map_bottom_border
        }

        crossings = []
        borders = []
        angles = []
        center = circle.center

        for bordername, border in borderdict.items():
            ccs = circle.inclusive_intersect_line(border)
            for c in ccs:
                if c not in crossings:
                    crossings.append(c)
                    borders.append(bordername)
                    angle = math.degrees(math.atan2(c.y - center.y, c.x - center.x))
                    angles.append(angle)

        ordered_crossings = sorted(zip(angles, crossings, borders))

        return ordered_crossings

    def calculate_corner_coordinates(self):
        self.map_llcoordinates = self.projection(self.map_llcorner, True)
        self.map_ulcoordinates = self.projection(self.map_ulcorner, True)
        self.map_urcoordinates = self.projection(self.map_urcorner, True)
        self.map_lrcoordinates = self.projection(self.map_lrcorner, True)

    def draw_meridians(self, origin_offsets={}):
        start_longitude = self.gridline_factory.meridian_tick_interval * math.ceil(self.min_longitude / self.gridline_factory.meridian_tick_interval)
        for longitude in numpy.arange(start_longitude, self.max_longitude, self.gridline_factory.meridian_tick_interval):
            self.draw_meridian(ensure_angle_range(longitude), origin_offsets)

    def draw_parallels(self):
        start_latitude = self.gridline_factory.parallel_tick_interval * math.ceil(self.min_latitude / self.gridline_factory.parallel_tick_interval)
        for latitude in numpy.arange(start_latitude, self.max_latitude, self.gridline_factory.parallel_tick_interval):
            self.draw_parallel(latitude)

    def draw_meridian(self, longitude):
        pass

    def draw_parallel(self, latitude):
        pass

    def draw_internal_parallel_ticks(self, longitude, angle=90, labels=False, label_angle=None):
        reference_meridian = self.map_meridian(longitude)
        tickangle = reference_meridian.meridian.angle + angle
        start_latitude = self.gridline_factory.parallel_tick_interval * math.ceil(self.min_latitude / self.gridline_factory.parallel_tick_interval)
        for latitude in numpy.arange(start_latitude, self.max_latitude, self.gridline_factory.parallel_tick_interval):
            if latitude in [-90, 90]:
                continue
            p1 = self.projection(SphericalPoint(longitude, latitude))
            if not self.inside_maparea(p1):
                continue
            delta = Point(1, 0).rotate(tickangle)

            if latitude % self.gridline_factory.parallel_line_interval == 0:
                ticksize = 0
            elif latitude % self.gridline_factory.parallel_marked_tick_interval == 0:
                ticksize = self.gridline_factory.marked_ticksize
            else:
                ticksize = self.gridline_factory.unmarked_ticksize

            if ticksize > 0:
                p2 = p1 + ticksize * delta
                self.draw_line(Line(p1, p2), linewidth=self.gridline_thickness)

            if labels and latitude % self.gridline_factory.parallel_line_interval == 0:
                p3 = p1 + 0.75 * delta
                text = "{}\\textdegree".format(int(abs(latitude)))
                if abs < 0:
                    text = "--" + text
                else:
                    text = "+" + text
                if label_angle is None:
                    label_angle = tickangle
                l = Label(p3, text, label_angle, "tiny", angle=0, fill="white")
                self.draw_label(l)

    def draw_constellations(self, dashed='dash pattern=on 1.6pt off 0.8pt'):
        boundaries = get_constellation_boundaries_for_area(self.min_longitude, self.max_longitude, self.min_latitude, self.max_latitude)
        for b in boundaries:
            points = [self.map_point(p) for p in b.interpolated_points]
            self.draw_polygon(points, linewidth=self.gridline_thickness, dashed=dashed)


class AzimuthalEquidistantMapArea(MapArea):
    def __init__(self, p1, p2, hmargin, vmargin, origin=None, north=True, reference_longitude=0, latitude_range=50, celestial=False, box=True):
        MapArea.__init__(self, p1, p2, hmargin=hmargin, vmargin=vmargin, origin=origin, box=box)
        reference_scale = abs(latitude_range / float(self.map_height))
        p = AzimuthalEquidistantProjection(north=north, reference_longitude=reference_longitude, reference_scale=reference_scale, celestial=celestial)
        self.set_projection(p)

        self.min_longitude = 0
        self.max_longitude = 360
        self.north = north
        if self.north:
            self.min_latitude = min([x.latitude for x in [self.map_llcoordinates, self.map_ulcoordinates, self.map_urcoordinates, self.map_lrcoordinates]])
            self.max_latitude = 90
        else:
            self.min_latitude = -90
            self.max_latitude = max([x.latitude for x in [self.map_llcoordinates, self.map_ulcoordinates, self.map_urcoordinates, self.map_lrcoordinates]])

        self.parallel_ticks = {'left': False, 'right': False, 'bottom': False, 'top': False}
        self.meridian_ticks = {'left': True, 'right': True, 'bottom': True, 'top': True}

    def map_parallel(self, latitude):
        c = Circle(SphericalPoint(0, self.projection.origin_latitude), self.projection.origin_latitude - latitude)
        c = self.map_circle(c)

        crossings = self.circle_intersect_borders(c)
        if crossings:
            parallels = []
            for i in range(len(crossings)):
                a1, c1, b1 = crossings[i - 1]
                a2, c2, b2 = crossings[i]
                if a1 > a2:
                    a2 += 360.0
                aavg = math.radians(0.5 * (a1 + a2))
                pavg = c.center + Point(c.radius * math.cos(aavg), c.radius * math.sin(aavg))
                if self.inside_maparea(pavg):
                    arc = Arc(c.center, c.radius, a1, a2)
                    p = self.gridline_factory.parallel(latitude, arc)
                    parallels.append(p)
        else:
            p = self.gridline_factory.parallel(latitude, c)
            parallels = [p]

        return parallels

    def draw_parallel(self, latitude):
        if latitude == 90 or latitude == -90:
            return
        parallels = self.map_parallel(latitude)

        for p in parallels:
            l = p.parallel
            if l:
                self.comment("Parellel {}".format(latitude))
                try:
                    self.draw_arc(l, linewidth=self.gridline_thickness)
                except DrawError:
                    self.draw_circle(l, linewidth=self.gridline_thickness)

            if p.border1 and self.parallel_ticks[p.border1]:
                t1 = p.tick1
                if t1:
                    self.draw_line(t1, linewidth=self.gridline_thickness)
                l1 = p.label1
                if l1:
                    self.draw_label(l1)

            if p.border2 and self.parallel_ticks[p.border2]:
                t2 = p.tick2
                if t2:
                    self.draw_line(t2, linewidth=self.gridline_thickness)
                l2 = p.label2
                if l2:
                    self.draw_label(l2)

    def map_meridian(self, longitude, longitude_offsets={}):
        """Returns the exact line to draw for a meridian"""
        offset = 0
        for l in sorted(longitude_offsets.keys(), reverse=True):
            if longitude % l == 0:
                offset = longitude_offsets[l]
                break

        if self.projection.north:
            p1 = SphericalPoint(longitude, self.projection.origin_latitude - offset)
        else:
            p1 = SphericalPoint(longitude, self.projection.origin_latitude + offset)

        if self.projection.north:
            p2 = SphericalPoint(longitude, self.min_latitude)
        else:
            p2 = SphericalPoint(longitude, self.max_latitude)

        l = self.map_line(Line(p1, p2))
        p2, border2 = self.line_intersect_borders(l)[0]
        l.p2 = p2

        m = self.gridline_factory.meridian(longitude, l)
        m.border2 = border2

        if xor(self.projection.north, not self.projection.celestial):
            m.tickangle2 = -longitude
        else:
            m.tickangle2 = longitude

        return m

    def draw_meridian(self, longitude, origin_offsets={}):
        m = self.map_meridian(longitude, origin_offsets)

        l = m.meridian
        if l:
            self.comment("Meridian {}".format(longitude))
            self.draw_line(l, linewidth=self.gridline_thickness)

        if m.border1 and self.meridian_ticks[m.border1]:
            t1 = m.tick1
            if t1:
                self.draw_line(t1, linewidth=self.gridline_thickness)
            l1 = m.label1
            if l1:
                self.draw_label(l1)

        if m.border2 and self.meridian_ticks[m.border2]:
            t2 = m.tick2
            if t2:
                self.draw_line(t2, linewidth=self.gridline_thickness)
            l2 = m.label2
            if l2:
                self.draw_label(l2)


class EquidistantCylindricalMapArea(MapArea):
    def __init__(self, p1, p2, hmargin, vmargin, center_longitude, origin=None, standard_parallel=20, latitude_range=56, lateral_scale=1.0, celestial=False, box=True):
        MapArea.__init__(self, p1, p2, hmargin=hmargin, vmargin=vmargin, origin=origin, box=box)
        reference_scale = abs(latitude_range / float(self.map_height))
        p = EquidistantCylindricalProjection(center_longitude=center_longitude, standard_parallel=standard_parallel, reference_scale=reference_scale, lateral_scale=lateral_scale, celestial=celestial)
        self.set_projection(p)

        xrange = (latitude_range/lateral_scale) * self.map_width/float(self.map_height)

        self.min_longitude = center_longitude - 0.5 * xrange
        self.max_longitude = center_longitude + 0.5 * xrange
        self.min_latitude = -0.5*latitude_range
        self.max_latitude = 0.5*latitude_range
        self.north = None

    def map_parallel(self, latitude):
        p1 = SphericalPoint(self.min_longitude, latitude)
        p2 = SphericalPoint(self.max_longitude, latitude)
        l = self.map_line(Line(p1, p2))
        if l.p1.x > l.p2.x:
            l.p1, l.p2 = l.p2, l.p1

        p = self.gridline_factory.parallel(latitude, l)
        p.border1 = "left"
        p.border2 = "right"
        p.tickangle1 = 180
        p.tickangle2 = 0
        return p

    def draw_parallel(self, latitude):
        p = self.map_parallel(latitude)
        p.fontsize = "tiny"

        l = p.parallel
        if l:
            self.comment("Parallel {}".format(latitude))
            self.draw_line(l, linewidth=self.gridline_thickness)

        if p.border1 and self.parallel_ticks[p.border1]:
            t1 = p.tick1
            if t1:
                self.draw_line(t1, linewidth=self.gridline_thickness)
            l1 = p.label1
            if l1:
                self.draw_label(l1)

        if p.border2 and self.parallel_ticks[p.border2]:
            t2 = p.tick2
            if t2:
                self.draw_line(t2, linewidth=self.gridline_thickness)
            l2 = p.label2
            if l2:
                self.draw_label(l2)

    def map_meridian(self, longitude):
        p1 = SphericalPoint(longitude, self.min_latitude)
        p2 = SphericalPoint(longitude, self.max_latitude)
        l = self.map_line(Line(p1, p2))

        m = self.gridline_factory.meridian(longitude, l)
        m.border1 = "bottom"
        m.border2 = "top"
        m.tickangle1 = 270
        m.tickangle2 = 90
        return m

    def draw_meridian(self, longitude, origin_offsets={}):
        m = self.map_meridian(longitude)

        l = m.meridian
        if l:
            self.comment("Meridian {}".format(longitude))
            self.draw_line(l, linewidth=self.gridline_thickness)

        if m.border1 and self.meridian_ticks[m.border1]:
            t1 = m.tick1
            if t1:
                self.draw_line(t1, linewidth=self.gridline_thickness)
            l1 = m.label1
            if l1:
                self.draw_label(l1)

        if m.border2 and self.meridian_ticks[m.border2]:
            t2 = m.tick2
            if t2:
                self.draw_line(t2, linewidth=self.gridline_thickness)
            l2 = m.label2
            if l2:
                self.draw_label(l2)


class EquidistantConicMapArea(MapArea):
    def __init__(self, p1, p2, hmargin, vmargin, center, standard_parallel1, standard_parallel2, origin=None, latitude_range=56, celestial=False, box=True):
        MapArea.__init__(self, p1, p2, hmargin=hmargin, vmargin=vmargin, origin=origin, box=box)
        reference_scale = abs(latitude_range / float(self.map_height))
        p = EquidistantConicProjection(center, standard_parallel1=standard_parallel1, standard_parallel2=standard_parallel2, reference_scale=reference_scale, celestial=celestial)
        self.set_projection(p)

        if True:
            self.min_longitude = center[0] - 100
            self.max_longitude = center[0] + 100
            self.min_latitude = -90
            self.max_latitude = 90
        else:
            self.min_longitude = center[0] - 0.5 * xrange
            self.max_longitude = center[0] + 0.5 * xrange
            self.min_latitude = center[1] - 0.5 * latitude_range
            self.max_latitude = center[2] + 0.5 * latitude_range

        if p.reference_latitude > 0:
            self.north = True
        else:
            self.north = False

        self.rotate_parallel_labels = True

    def map_parallel(self, latitude):
        p = SphericalPoint(0, latitude)
        radius = p.distance(self.projection.parallel_circle_center)
        c = Circle(self.projection.parallel_circle_center, radius)
        c = self.map_circle(c)

        crossings = self.circle_intersect_borders(c)
        if crossings:
            parallels = []
            for i in range(len(crossings)):
                a1, c1, b1 = crossings[i - 1]
                a2, c2, b2 = crossings[i]
                if a1 > a2:
                    a2 += 360.0
                aavg = math.radians(0.5 * (a1 + a2))
                pavg = c.center + Point(c.radius * math.cos(aavg), c.radius * math.sin(aavg))
                if self.inside_maparea(pavg):
                    arc = Arc(c.center, c.radius, a1, a2)
                    p = self.gridline_factory.parallel(latitude, arc)

                    p.border1 = b1
                    p.tickangle1 = a1 + 90
                    if self.rotate_parallel_labels:
                        if latitude > 0:
                            p.labelangle1 = a1 + 90
                        else:
                            p.labelangle1 = a1 - 90
                    else:
                        p.labelangle1 = 0

                    p.border2 = b2
                    p.tickangle2 = a2 + 90
                    if self.rotate_parallel_labels:
                        if latitude > 0:
                            p.labelangle2 = a2 + 90
                        else:
                            p.labelangle2 = a2 - 90
                    else:
                        p.labelangle2 = 0
                    parallels.append(p)
        else:
            if self.inside_maparea(c.center):
                p = self.gridline_factory.parallel(latitude, c)
                parallels = [p]
            else:
                parallels = []

        return parallels

    def draw_parallel(self, latitude):
        if latitude == 90 or latitude == -90:
            return

        parallels = self.map_parallel(latitude)

        for p in parallels:
            l = p.parallel

            if l:
                self.comment("Parellel {}".format(latitude))
                try:
                    self.draw_arc(l, linewidth=self.gridline_thickness)
                except DrawError:
                    self.draw_circle(l, linewidth=self.gridline_thickness)

            p.fontsize = "tiny"
            if p.border1 and self.parallel_ticks[p.border1]:
                t1 = p.tick1
                if t1:
                    self.draw_line(t1, linewidth=self.gridline_thickness)
                l1 = p.label1
                if l1:
                    self.draw_label(l1)

            if p.border2 and self.parallel_ticks[p.border2]:
                t2 = p.tick2
                if t2:
                    self.draw_line(t2, linewidth=self.gridline_thickness)
                l2 = p.label2
                if l2:
                    self.draw_label(l2)

    def map_meridian(self, longitude, longitude_offsets={}):
        offset = 0
        for l in sorted(longitude_offsets.keys(), reverse=True):
            if longitude % l == 0:
                offset = longitude_offsets[l]
                break

        if self.projection.reference_latitude > 0:
            p1 = SphericalPoint(longitude, self.min_latitude)
            p2 = SphericalPoint(longitude, self.max_latitude - offset)
        else:
            p1 = SphericalPoint(longitude, self.min_latitude + offset)
            p2 = SphericalPoint(longitude, self.max_latitude)

        l = self.map_line(Line(p1, p2))
        intersections = self.line_intersect_borders(l)
        if not intersections:
            return None
        if len(intersections) == 1:
            if self.inside_maparea(l.p1):
                p2, border2 = intersections[0]
                p1, border1 = l.p1, None
            else:
                p1, border1 = intersections[0]
                p2, border2 = l.p2, None
        else:
            p1, border1 = intersections[0]
            p2, border2 = intersections[1]

        if p1.y < p2.y:
            p1, p2 = p2, p1
            border1, border2 = border2, border1

        l.p1 = p1
        l.p2 = p2

        m = self.gridline_factory.meridian(longitude, l)
        m.border1 = border1
        m.border2 = border2
        m.tickangle1 = l.angle
        m.tickangle2 = l.angle
        return m

    def draw_meridian(self, longitude, origin_offsets={}):
        m = self.map_meridian(longitude, origin_offsets)
        if m is None:
            return

        l = m.meridian
        if l:
            self.comment("Meridian {}".format(longitude))
            self.draw_line(l, linewidth=self.gridline_thickness)

        if m.border1 and self.meridian_ticks[m.border1]:
            t1 = m.tick1
            if t1:
                self.draw_line(t1, linewidth=self.gridline_thickness)
            l1 = m.label1
            if l1:
                self.draw_label(l1)
        if m.border2 and self.meridian_ticks[m.border2]:
            t2 = m.tick2
            if t2:
                self.draw_line(t2, linewidth=self.gridline_thickness)
            l2 = m.label2
            if l2:
                self.draw_label(l2)