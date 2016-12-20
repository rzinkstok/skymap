import os
from skymap.geometry import Point, SphericalPoint, Line, Polygon, Circle, Arc, HourAngle
from skymap.metapost import MetaPostFigure
from skymap.projections import AzimuthalEquidistantProjection, EquidistantCylindricalProjection, EquidistantConicProjection


class Map(object):
    def __init__(self, projection, paper_size, margin_lr, margin_bt):
        self.set_projection(projection)
        self.set_paper_size(paper_size)
        self.set_margins(margin_lr, margin_bt)

        self.min_longitude = None
        self.max_longitude = None
        self.min_latitude = None
        self.max_latitude = None

        self.set_origin(Point(self.paper_width/2.0, self.paper_height/2.0))
        self.set_vertical_scale(2.0)

        self.draw_parallel_ticks_on_vertical_axis = True
        self.draw_parallel_ticks_on_horizontal_axis = False
        self.draw_meridian_ticks_on_vertical_axis = False
        self.draw_meridian_ticks_on_horizontal_axis = True

    # Init functions
    def set_projection(self, projection):
        self.projection = projection

    def set_paper_size(self, paper_size):
        self.paper_width = paper_size[0]
        self.paper_height = paper_size[1]

    def set_margins(self, margin_lr,  margin_bt):
        try:
            self.margin_left, self.margin_right = margin_lr
        except TypeError:
            self.margin_left = margin_lr
            self.margin_right = margin_lr
        try:
            self.margin_bottom, self.margin_top = margin_bt
        except TypeError:
            self.margin_bottom = margin_bt
            self.margin_top = margin_bt

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

    def set_vertical_scale(self, scale):
        self.conversion = scale/self.map_size_y

        self.extent_x = self.conversion * self.map_size_x
        self.min_x = self.conversion * (self.margin_left - self.origin.x)
        self.max_x = self.min_x + self.extent_x

        self.extent_y = self.conversion * self.map_size_y
        self.min_y = self.conversion * (self.margin_bottom - self.origin.y)
        self.max_y = self.min_y + self.extent_y

    def inside_viewport(self, p):
        """Check whether the given point lies within the map area"""
        if p.x < self.margin_left or p.x > self.margin_left+self.map_size_x or p.y < self.margin_bottom or p.y > self.margin_bottom+self.map_size_y:
            return False
        else:
            return True

    def map_distance(self, distance):
        p1 = self.map_point(SphericalPoint(0, 0))
        p2 = self.map_point(SphericalPoint(0, distance))
        return p1.distance(p2)

    def map_point(self, spherical_point):
        p = self.projection.project(spherical_point)
        map_x = self.margin_left + self.map_size_x * (p.x - self.min_x) / self.extent_x
        map_y = self.margin_bottom + self.map_size_y * (p.y - self.min_y) / self.extent_y
        return Point(map_x, map_y)

    def map_line(self, line):
        p1 = self.map_point(line.p1)
        p2 = self.map_point(line.p2)
        return Line(p1, p2)

    def map_circle(self, circle):
        """This is a parallel circle...."""
        center = self.map_point(circle.center)
        radius = self.map_distance(circle.radius)
        return Circle(center, radius)


class AzimuthalEquidistantMap(Map):
    def __init__(self, paper_size, margin_lr, margin_bt, north=True, reference_longitude=0, reference_scale=25, celestial=False):
        p = AzimuthalEquidistantProjection(north=north, celestial=celestial, reference_longitude=reference_longitude, reference_scale=reference_scale)

        Map.__init__(self, p, paper_size, margin_lr, margin_bt)

        self.min_longitude = 0
        self.max_longitude = 360
        self.north = north
        if self.north:
            self.min_latitude = 30
            self.max_latitude = 90
        else:
            self.min_latitude = -90
            self.max_latitude = -30

        self.draw_parallel_ticks_on_vertical_axis = False
        self.draw_meridian_ticks_on_vertical_axis = True

    def map_parallel(self, latitude):
        parallel = Circle(SphericalPoint(0, self.projection.origin_latitude), self.projection.origin_latitude - latitude)
        return self.map_circle(parallel)

    def map_meridian(self, longitude):
        if longitude%90 == 0.0:
            p1 = SphericalPoint(0, self.projection.origin_latitude)
        elif longitude%45 == 0.0:
            if self.projection.north:
                p1 = SphericalPoint(longitude, 89)
            else:
                p1 = SphericalPoint(longitude, -89)
        else:
            if self.projection.north:
                p1 = SphericalPoint(longitude, 80)
            else:
                p1 = SphericalPoint(longitude, -80)
        p2 = SphericalPoint(longitude, 0)

        return self.map_line(Line(p1, p2))


class EquidistantCylindricalMap(Map):
    def __init__(self, paper_size, margin_lr, margin_bt, center_longitude, standard_parallel=20, reference_scale=25, celestial=False):
        try:
            margin_bottom = margin_bt[0]
        except TypeError:
            margin_bottom = margin_bt
        margin_lr = 0.5 * (paper_size[0] - (paper_size[1] - 2 * margin_bottom) * 1.5)

        p = EquidistantCylindricalProjection(celestial=celestial, standard_parallel=standard_parallel, center_longitude=center_longitude, reference_scale=reference_scale)

        Map.__init__(self, p, paper_size, margin_lr, margin_bt)

        xrange = self.projection.reference_scale * self.map_size_x / self.map_size_y + 20
        yrange = self.projection.reference_scale + 15
        self.min_longitude = center_longitude - xrange
        self.max_longitude = center_longitude + xrange
        self.min_latitude = -yrange
        self.max_latitude = yrange
        self.north = None

    def map_parallel(self, latitude):
        p1 = SphericalPoint(self.projection.center_longitude - 2 * self.projection.reference_scale, latitude)
        p2 = SphericalPoint(self.projection.center_longitude + 2 * self.projection.reference_scale, latitude)
        return self.map_line(Line(p1, p2))

    def map_meridian(self, longitude):
        p1 = SphericalPoint(longitude, -90)
        p2 = SphericalPoint(longitude, +90)
        return self.map_line(Line(p1, p2))


class EquidistantConicMap(Map):
    def __init__(self, paper_size, margin_lr, margin_bt, center, standard_parallel1=30, standard_parallel2=60, reference_scale=25, celestial=False):
        p = EquidistantConicProjection(center, standard_parallel1=standard_parallel1, standard_parallel2=standard_parallel2, reference_scale=reference_scale, celestial=celestial)
        Map.__init__(self, p, paper_size, margin_lr, margin_bt)

        self.min_longitude = center[0] - 100
        self.max_longitude = center[0] + 100
        if p.reference_latitude > 0:
            self.north = True
            self.min_latitude = -5
            self.max_latitude = 90
        else:
            self.north = False
            self.min_latitude = -90
            self.max_latitude = +5

    def map_parallel(self, latitude):
        # Circle around origin
        p = SphericalPoint(0, latitude)
        radius = p.distance(self.projection.parallel_circle_center)
        return self.map_circle(Circle(self.projection.parallel_circle_center, radius))

    def map_meridian(self, longitude):
        # Line from origin
        if self.projection.reference_latitude > 0:
            p = SphericalPoint(longitude, -30)
        else:
            p = SphericalPoint(longitude, 30)
        return self.map_line(Line(self.projection.parallel_circle_center, p))
