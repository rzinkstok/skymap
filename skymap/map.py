import os
import math
import numpy
from operator import xor, attrgetter
from skymap.tikz import DrawingArea, DrawError
from skymap.geometry import Point, SphericalPoint, Line, Circle, Arc, Rectangle, ensure_angle_range
from skymap.projections import AzimuthalEquidistantProjection, EquidistantCylindricalProjection, EquidistantConicProjection, UnitProjection
from skymap.gridlines import GridLineFactory, GridLineLabel
from skymap.constellations import get_constellation_boundaries_for_area
from skymap.coordinates import ecliptic_to_equatorial, galactic_to_equatorial


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

        self.bordered = True

        # Longitude/latitude grid
        self.gridline_factory = GridLineFactory()
        self.gridline_factory.marked_ticksize = 1.0
        self.gridline_factory.unmarked_ticksize = 0.5
        self.gridline_factory.meridian_line_interval = 15        # 1 hour
        self.gridline_factory.meridian_marked_tick_interval = 5  # 20 minutes
        self.gridline_factory.meridian_tick_interval = 1.25      # 5 minutes
        self.gridline_factory.parallel_line_interval = 10
        self.gridline_factory.parallel_marked_tick_interval = 10
        self.gridline_factory.parallel_tick_interval = 1

        self.parallel_ticks = {'left': True, 'right': True, 'bottom': False, 'top': False}
        self.meridian_ticks = {'left': False, 'right': False, 'bottom': True, 'top': True}

    def open(self):
        DrawingArea.open(self)
        if self.box and (self.map_hmargin > 0 or self.map_vmargin > 0):
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

    def inside_coordinate_range(self, p):
        return (self.min_longitude <= p.longitude <= self.max_longitude) and (self.min_latitude <= p.latitude <= self.max_latitude)

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
        self.draw_rectangle(self.map_box, linewidth=self.gridline_factory.gridline_thickness)

    def draw_clipping_path(self):
        path = self.clipping_path
        self.draw_path(path)

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

    def draw_meridians(self, origin_offsets={}, include_endpoint=True):
        start_longitude = self.gridline_factory.meridian_tick_interval * math.ceil(self.min_longitude / self.gridline_factory.meridian_tick_interval)
        if include_endpoint:
            stop_longitude = self.max_longitude + 0.5*self.gridline_factory.meridian_tick_interval
        else:
            stop_longitude = self.max_longitude
        for longitude in numpy.arange(start_longitude, stop_longitude, self.gridline_factory.meridian_tick_interval):
            self.draw_meridian(ensure_angle_range(longitude), origin_offsets)

    def draw_parallels(self, include_endpoint=True):
        start_latitude = self.gridline_factory.parallel_tick_interval * math.ceil(self.min_latitude / self.gridline_factory.parallel_tick_interval)
        if include_endpoint:
            stop_latitude = self.max_latitude + 0.5 * self.gridline_factory.parallel_tick_interval
        else:
            stop_latitude = self.max_latitude
        for latitude in numpy.arange(start_latitude, stop_latitude, self.gridline_factory.parallel_tick_interval):
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
                self.draw_line(Line(p1, p2), linewidth=self.gridline_factory.gridline_thickness)

            if labels and latitude % self.gridline_factory.parallel_line_interval == 0:
                p3 = p1 + 0.75 * delta
                text = "{}\\textdegree".format(int(abs(latitude)))
                if abs < 0:
                    text = "--" + text
                else:
                    text = "+" + text
                if label_angle is None:
                    label_angle = tickangle
                l = GridLineLabel(p3, text, label_angle, "tiny", angle=0, fill="white")
                self.draw_label(l)

    def draw_constellations(self, linewidth=0.3, dashed='dash pattern=on 1.6pt off 0.8pt'):
        self.comment("Constellation boundaries")
        min_longitude = self.min_longitude
        max_longitude = self.max_longitude
        if max_longitude - min_longitude < 90:
            min_longitude -= 45
            max_longitude += 45

        min_latitude = 45 * math.floor(self.min_latitude / 45.0)
        max_latitude = 45 * math.ceil(self.max_latitude / 45.0)
        if min_latitude < -90:
            min_latitude = -90
        if max_latitude > 90:
            max_latitude = 90
        boundaries = get_constellation_boundaries_for_area(min_longitude, max_longitude, min_latitude, max_latitude)
        for b in boundaries:
            points = [self.map_point(p) for p in b.interpolated_points]
            self.draw_polygon(points, linewidth=linewidth, dashed=dashed)

    def draw_coordinate_system(self, transformation, linewidth=0.3, dashed='dashed', tickinterval=None, poles=False):
        points = []
        for longitude in numpy.arange(0, 360.1, 0.251):
            p = transformation(SphericalPoint(longitude, 0))
            points.append(SphericalPoint(self.projection.reduce_longitude(p.longitude), p.latitude))

        points_to_draw = []
        for i in range(len(points)):
            prev_p = points[i-1]
            p = points[i]
            if i + 1 == len(points):
                next_p = points[0]
            else:
                next_p = points[i+1]

            if self.bordered:
                prev_p = self.map_point(prev_p)
                p = self.map_point(p)
                next_p = self.map_point(next_p)

                if self.inside_maparea(prev_p) or self.inside_maparea(p) or self.inside_maparea(next_p):
                    points_to_draw.append(p)
            else:
                prevpinside = self.inside_coordinate_range(prev_p)
                pinside = self.inside_coordinate_range(p)
                nextpinside = self.inside_coordinate_range(next_p)
                if prevpinside or pinside or nextpinside:
                    points_to_draw.append(self.map_point(p))

        points_to_draw = sorted(points_to_draw, key=attrgetter('x'))
        if points_to_draw:
            self.draw_polygon(points_to_draw, linewidth=linewidth, dashed=dashed)

        # Ticks
        if tickinterval is not None:
            for i in range(360/int(tickinterval)):
                l = i * tickinterval
                p = transformation(SphericalPoint(l, 0))
                p.longitude = self.projection.reduce_longitude(p.longitude)
                if self.bordered:
                    p = self.map_point(p)
                    if not self.inside_maparea(p):
                        continue
                else:
                    if not self.inside_coordinate_range(p):
                        continue
                    p = self.map_point(p)

                v = self.map_point(transformation(SphericalPoint(l+1, 0))) - p
                v = v.rotate(90)/v.norm
                tp1 = p + 0.5 * v
                tp2 = p - 0.5 * v
                lp = p + 0.8 * v
                tick = Line(tp1, tp2)
                self.draw_line(tick, linewidth=linewidth)
                self.draw_label(GridLineLabel(lp, "\\textit{{{}\\textdegree}}".format(l), 270, "miniscule", angle=tick.angle - 90, fill="white"))

        # Poles
        if poles:
            p = transformation(SphericalPoint(0, 90))
            np = self.map_point(p)
            if self.gridline_factory.rotate_poles:
                delta1 = self.map_point(p + SphericalPoint(1, 0)) - np
                delta2 = self.map_point(p + SphericalPoint(0, 1)) - np
            else:
                delta1 = Point(1, 0)
                delta2 = Point(0, 1)

            delta1 *= self.gridline_factory.pole_marker_size/delta1.norm
            delta2 *= self.gridline_factory.pole_marker_size/delta2.norm

            if self.inside_maparea(np):
                bl1 = Line(np + 1.25 * delta1, np - 1.25 * delta1)
                l1 = Line(np + delta1, np - delta1)
                bl2 = Line(np + 1.25 * delta2, np - 1.25 * delta2)
                l2 = Line(np + delta2, np - delta2)
                self.draw_line(bl1, linewidth=3 * linewidth, color="white")
                self.draw_line(bl2, linewidth=3 * linewidth, color="white")
                self.draw_line(l1, linewidth=self.gridline_factory.gridline_thickness)
                self.draw_line(l2, linewidth=self.gridline_factory.gridline_thickness)

            p = transformation(SphericalPoint(0, -90))
            sp = self.map_point(p)
            if self.gridline_factory.rotate_poles:
                delta1 = self.map_point(p + SphericalPoint(1, 0)) - sp
                delta2 = self.map_point(p + SphericalPoint(0, 1)) - sp
            else:
                delta1 = Point(1, 0)
                delta2 = Point(0, 1)

            delta1 *= self.gridline_factory.pole_marker_size / delta1.norm
            delta2 *= self.gridline_factory.pole_marker_size / delta2.norm

            if self.inside_maparea(sp):
                bl1 = Line(sp + 1.25 * delta1, sp - 1.25 * delta1)
                l1 = Line(sp + delta1, sp - delta1)
                bl2 = Line(sp + 1.25 * delta2, sp - 1.25 * delta2)
                l2 = Line(sp + delta2, sp - delta2)
                self.draw_line(bl1, linewidth=3 * linewidth, color="white")
                self.draw_line(bl2, linewidth=3 * linewidth, color="white")
                self.draw_line(l1, linewidth=self.gridline_factory.gridline_thickness)
                self.draw_line(l2, linewidth=self.gridline_factory.gridline_thickness)

    def draw_ecliptic(self, linewidth=0.3, dashed='dashed', tickinterval=None, poles=False):
        self.comment("Ecliptic")
        self.draw_coordinate_system(ecliptic_to_equatorial, linewidth, dashed, tickinterval, poles)

    def draw_galactic(self, linewidth=0.3, dashed='dashed', tickinterval=None, poles=False):
        self.comment("Galactic equator")
        self.draw_coordinate_system(galactic_to_equatorial, linewidth, dashed, tickinterval, poles)


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

    @property
    def clipping_path(self):
        if self.bordered:
            return self.map_box.path
        else:
            if self.north:
                boundary = self.map_parallel(self.min_latitude)[0].parallel
            else:
                boundary = self.map_parallel(self.max_latitude)[0].parallel

            return boundary.path

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
                    self.draw_arc(l, linewidth=self.gridline_factory.gridline_thickness)
                except DrawError:
                    self.draw_circle(l, linewidth=self.gridline_factory.gridline_thickness)

            if p.border1 and self.parallel_ticks[p.border1]:
                t1 = p.tick1
                if t1:
                    self.draw_line(t1, linewidth=self.gridline_factory.gridline_thickness)
                l1 = p.label1
                if l1:
                    self.draw_label(l1)

            if p.border2 and self.parallel_ticks[p.border2]:
                t2 = p.tick2
                if t2:
                    self.draw_line(t2, linewidth=self.gridline_factory.gridline_thickness)
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
        if self.bordered:
            p2, border2 = self.line_intersect_borders(l)[0]
            l.p2 = p2
        else:
            border2 = "bottom"

        m = self.gridline_factory.meridian(longitude, l)
        m.border2 = border2

        if xor(self.projection.north, not self.projection.celestial):
            m.tickangle2 = -longitude + self.projection.reference_longitude
        else:
            m.tickangle2 = longitude - self.projection.reference_longitude

        if self.gridline_factory.rotate_meridian_labels:
            m.labelpos2 = 270
            m.labelangle2 = l.angle+90
        else:
            pass

        return m

    def draw_meridian(self, longitude, origin_offsets={}):
        m = self.map_meridian(longitude, origin_offsets)

        l = m.meridian
        if l:
            self.comment("Meridian {}".format(longitude))
            self.draw_line(l, linewidth=self.gridline_factory.gridline_thickness)

        if m.border1 and self.meridian_ticks[m.border1]:
            t1 = m.tick1
            if t1:
                self.draw_line(t1, linewidth=self.gridline_factory.gridline_thickness)
            l1 = m.label1
            if l1:
                self.draw_label(l1)

        if m.border2 and self.meridian_ticks[m.border2]:
            t2 = m.tick2
            if t2:
                self.draw_line(t2, linewidth=self.gridline_factory.gridline_thickness)
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

    @property
    def clipping_path(self):
        if self.bordered:
            return self.map_box.path
        else:
            first_parallel = self.map_parallel(self.min_latitude).parallel
            last_parallel = self.map_parallel(self.max_latitude).parallel
            return first_parallel.path + "--" + last_parallel.reverse_path + "--cycle"

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

        l = p.parallel
        if l:
            self.comment("Parallel {}".format(latitude))
            self.draw_line(l, linewidth=self.gridline_factory.gridline_thickness)

        if p.border1 and self.parallel_ticks[p.border1]:
            t1 = p.tick1
            if t1:
                self.draw_line(t1, linewidth=self.gridline_factory.gridline_thickness)
            l1 = p.label1
            if l1:
                self.draw_label(l1)

        if p.border2 and self.parallel_ticks[p.border2]:
            t2 = p.tick2
            if t2:
                self.draw_line(t2, linewidth=self.gridline_factory.gridline_thickness)
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
            self.draw_line(l, linewidth=self.gridline_factory.gridline_thickness)

        if m.border1 and self.meridian_ticks[m.border1]:
            t1 = m.tick1
            if t1:
                self.draw_line(t1, linewidth=self.gridline_factory.gridline_thickness)
            l1 = m.label1
            if l1:
                self.draw_label(l1)

        if m.border2 and self.meridian_ticks[m.border2]:
            t2 = m.tick2
            if t2:
                self.draw_line(t2, linewidth=self.gridline_factory.gridline_thickness)
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

    @property
    def clipping_path(self):
        if self.bordered:
            return self.map_box.path
        else:
            first_parallel = self.map_parallel(self.min_latitude)[0].parallel
            last_parallel = self.map_parallel(self.max_latitude)[0].parallel
            return first_parallel.path + "--" + last_parallel.reverse_path + "--cycle"

    def map_parallel(self, latitude):
        p = SphericalPoint(0, latitude)
        radius = p.distance(self.projection.parallel_circle_center)
        center = self.projection.parallel_circle_center
        c = Circle(center, radius)
        c = self.map_circle(c)

        if self.bordered:
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
                        if self.gridline_factory.rotate_parallel_labels:
                            if latitude > 0:
                                p.labelangle1 = a1 + 90
                            else:
                                p.labelangle1 = a1 - 90
                        else:
                            p.labelangle1 = 0

                        p.border2 = b2
                        p.tickangle2 = a2 + 90
                        if self.gridline_factory.rotate_parallel_labels:
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
        else:
            if self.projection.reference_latitude > 0:
                start_angle = self.map_meridian(self.min_longitude).meridian.angle + 180
                stop_angle = self.map_meridian(self.max_longitude).meridian.angle + 180
            else:
                start_angle = self.map_meridian(self.max_longitude).meridian.angle
                stop_angle = self.map_meridian(self.min_longitude).meridian.angle
            a = Arc(c.center, c.radius, start_angle, stop_angle)
            p = self.gridline_factory.parallel(latitude, a)

            if self.projection.reference_latitude > 0:
                p.border1 = 'right'
            else:
                p.border1 = 'left'

            p.tickangle1 = start_angle + 90

            if self.gridline_factory.rotate_parallel_labels:
                if self.projection.reference_latitude > 0:
                    p.labelangle1 = start_angle + 90
                else:
                    p.labelangle1 = start_angle - 90
            else:
                p.labelangle1 = 0

            if self.projection.reference_latitude > 0:
                p.border2 = 'left'
            else:
                p.border2 = 'right'

            p.tickangle2 = stop_angle - 90

            if self.gridline_factory.rotate_parallel_labels:
                if self.projection.reference_latitude > 0:
                    p.labelangle2 = stop_angle + 90
                else:
                    p.labelangle2 = stop_angle - 90
            else:
                p.labelangle2 = 0

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
                    self.draw_arc(l, linewidth=self.gridline_factory.gridline_thickness)
                except DrawError:
                    self.draw_circle(l, linewidth=self.gridline_factory.gridline_thickness)

            if p.border1 and self.parallel_ticks[p.border1]:
                t1 = p.tick1
                if t1:
                    self.draw_line(t1, linewidth=self.gridline_factory.gridline_thickness)
                l1 = p.label1
                if l1:
                    self.draw_label(l1)

            if p.border2 and self.parallel_ticks[p.border2]:
                t2 = p.tick2
                if t2:
                    self.draw_line(t2, linewidth=self.gridline_factory.gridline_thickness)
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
        if self.bordered:
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
        else:
            border1 = "bottom"
            border2 = "top"

        m = self.gridline_factory.meridian(longitude, l)
        m.border1 = border1
        m.border2 = border2
        m.tickangle1 = l.angle + 180
        m.tickangle2 = l.angle
        if self.gridline_factory.rotate_meridian_labels:
            m.labelangle1 = l.angle - 90
            m.labelangle2 = l.angle - 90
        return m

    def draw_meridian(self, longitude, origin_offsets={}):
        m = self.map_meridian(longitude, origin_offsets)
        if m is None:
            return

        l = m.meridian
        if l:
            self.comment("Meridian {}".format(longitude))
            self.draw_line(l, linewidth=self.gridline_factory.gridline_thickness)

        if m.border1 and self.meridian_ticks[m.border1]:
            t1 = m.tick1
            if t1:
                self.draw_line(t1, linewidth=self.gridline_factory.gridline_thickness)
            l1 = m.label1
            if l1:
                self.draw_label(l1)
        if m.border2 and self.meridian_ticks[m.border2]:
            t2 = m.tick2
            if t2:
                self.draw_line(t2, linewidth=self.gridline_factory.gridline_thickness)
            l2 = m.label2
            if l2:
                self.draw_label(l2)