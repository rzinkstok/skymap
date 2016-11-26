import math

from geometry import Point, distance, intersection_line_circle, intersection_line_line


class StereographicCylinder(object):
    def __init__(self, standard_parallel, source_distance_scale):
        self.standard_parallel_rad = math.radians(standard_parallel)
        self.source_distance_scale = source_distance_scale

        self.min_longitude = None
        self.max_longitude = None
        self.orig_longitude = None
        self.orig_longitude_rad = None
        self.min_latitude = None
        self.max_latitude = None

        self.min_x = None
        self.max_x = None
        self.extent_x = None
        self.min_y = None
        self.max_y = None
        self.extent_y = None

        self.map_offset_x = None
        self.map_offset_y = None
        self.map_size_x = None
        self.map_size_y = None

    def set_longitude_limits(self, min_longitude, max_longitude):
        self.min_longitude = min_longitude
        self.max_longitude = max_longitude
        if self.max_longitude > self.min_longitude:
            self.orig_longitude = 0.5*(min_longitude+max_longitude)
        else:
            self.orig_longitude = 0.5*(min_longitude+max_longitude) - 180
        print "Origin longitude:", self.orig_longitude
        self.orig_longitude_rad = math.radians(self.orig_longitude)
        self.min_x, dummy = self._project(self.min_longitude, 0)
        self.max_x, dummy = self._project(self.max_longitude, 0)
        self.extent_x = self.max_x - self.min_x
        print "Min x:", self.min_x
        print "Max x:", self.max_x

    def set_latitude_limits(self, min_latitude, max_latitude):
        self.min_latitude = min_latitude
        self.max_latitude = max_latitude
        dummy, self.min_y = self._project(0, self.min_latitude)
        dummy, self.max_y = self._project(0, self.max_latitude)
        self.extent_y = self.max_y - self.min_y

    @property
    def lowest_latitude(self):
        return self.min_latitude

    def set_map_size(self, size_x, size_y):
        self.map_size_x = size_x
        self.map_size_y = size_y

    def set_map_offset(self, offset_x, offset_y):
        self.map_offset_x = offset_x
        self.map_offset_y = offset_y

    def to_map_coordinates(self, x, y):
        map_x = self.map_offset_x + self.map_size_x - self.map_size_x*(x-self.min_x)/self.extent_x
        map_y = self.map_offset_y + self.map_size_y*(y-self.min_y)/self.extent_y
        return map_x, map_y

    def _project(self, longitude, latitude):
        # longitude, latitude: in degrees
        # longitude: east-west
        # latitude: north-south
        longitude_rad = math.radians(longitude)
        if longitude_rad < 0:
            longitude_rad += 2*math.pi
        latitude_rad = math.radians(latitude)
        x = longitude_rad-self.orig_longitude_rad
        if x > math.pi:
            x -= 2*math.pi
        y = math.sin(latitude_rad) * (math.cos(self.standard_parallel_rad) + self.source_distance_scale)/(math.cos(latitude_rad) + self.source_distance_scale)
        return x, y

    def project_to_map(self, longitude, latitude):
        x, y = self._project(longitude, latitude)
        return Point(self.to_map_coordinates(x, y))

    def points_for_parallel(self, latitude):
        p1 = self.project_to_map(self.min_longitude, latitude)
        p2 = self.project_to_map(self.max_longitude, latitude)
        return p1, p2, "rt", "lft"

    def points_for_meridian(self, longitude):
        p1 = self.project_to_map(longitude, self.min_latitude)
        p2 = self.project_to_map(longitude, self.max_latitude)
        return p1, p2, "bot", "top"

    def inside_viewport(self, p):
        if p.x < self.map_offset_x or p.x > self.map_offset_x+self.map_size_x or p.y < self.map_offset_y or p.y > self.map_offset_y+self.map_size_y:
            return False
        else:
            return True


class LambertConformalConic(object):
    def __init__(self, standard_parallel1, standard_parallel2, origin_longitude, origin_latitude):
        print standard_parallel1, standard_parallel2, origin_latitude
        if standard_parallel1 < 0 or standard_parallel2 < 0 or origin_latitude < 0:
            raise ValueError("Only positive latitudes are allowed!")
        self.standard_parallel1 = standard_parallel1
        self.standard_parallel2 = standard_parallel2
        self.origin_longitude = origin_longitude
        self.origin_latitude = origin_latitude

        self.map_pole = None

        self.min_longitude = None
        self.max_longitude = None
        self._min_latitude = None
        self._max_latitude = None
        self._lowest_latitude = None

        self.map_offset_x = None
        self.map_offset_y = None
        self.map_size_x = None
        self.map_size_y = None

    def set_latitude_limits(self, min_latitude, max_latitude):
        if min_latitude < 0 or max_latitude < 0:
            raise ValueError("Only positive latitudes are allowed!")
        self._min_latitude = min_latitude
        self._max_latitude = max_latitude

    @property
    def min_latitude(self):
        return self.min_latitude

    @property
    def max_latitude(self):
        return self._max_latitude

    @property
    def lowest_latitude(self):
        return self._lowest_latitude

    def set_map_size(self, size_x, size_y):
        self.map_size_x = size_x
        self.map_size_y = size_y

    def set_map_offset(self, offset_x, offset_y):
        self.map_offset_x = offset_x
        self.map_offset_y = offset_y

    def calculate_map_pole(self):
        self.map_pole = self.project_to_map(0, 90)
        dummy, self._lowest_latitude = self.project_from_map(self.map_offset_x, self.map_offset_y)
        self.min_longitude, dummy = self.project_from_map(self.map_offset_x + self.map_size_x, self.map_offset_y + self.map_size_y)
        self.max_longitude, dummy = self.project_from_map(self.map_offset_x, self.map_offset_y + self.map_size_y)

        if self.min_longitude < 0:
            self.min_longitude += 360.0
        if self.max_longitude < 0:
            self.max_longitude += 360.0

    def to_map_coordinates(self, x, y):
        m = 200.0
        return -m*x + 0.5*self.map_size_x + self.map_offset_x, m*y + self.map_offset_y

    def from_map_coordinates(self, map_x, map_y):
        m = 200.0
        return -(map_x - 0.5*self.map_size_x - self.map_offset_x)/m, (map_y-self.map_offset_y)/m

    def _project(self, longitude, latitude):
        # longitude, latitude: in degrees
        # longitude: east-west
        # latitude: north-south

        longitude_rad = math.radians(longitude)
        latitude_rad = math.radians(latitude)

        sp1r = math.radians(self.standard_parallel1)
        sp2r = math.radians(self.standard_parallel2)
        orig_longitude_rad = math.radians(self.origin_longitude)
        orig_latitude_rad = math.radians(self.origin_latitude)

        cos1 = math.cos(sp1r)
        cos2 = math.cos(sp2r)
        sp1r_4 = math.pi/4 + sp1r/2
        sp2r_4 = math.pi/4 + sp2r/2
        tan1_4 = math.tan(sp1r_4)
        tan2_4 = math.tan(sp2r_4)

        n = math.log(cos1/cos2)/math.log(tan2_4/tan1_4)
        f = cos1*pow(math.tan(sp1r_4), n)/n
        rho0 = f/pow(math.tan(math.pi/4 + orig_latitude_rad/2), n)

        if longitude_rad-orig_longitude_rad > math.pi:
            theta = n*(longitude_rad-orig_longitude_rad - 2*math.pi)
        else:
            theta = n*(longitude_rad-orig_longitude_rad)

        rho = f/pow(math.tan(math.pi/4 + latitude_rad/2), n)

        x = rho*math.sin(theta)
        y = rho0 - rho * math.cos(theta)

        return x, y

    def project_to_map(self, longitude, latitude, invert_latitude=False):
        x, y = self._project(longitude, latitude)
        return Point(self.to_map_coordinates(x, y))

    def project_from_map(self, map_x, map_y):
        x, y = self.from_map_coordinates(map_x, map_y)
        longitude, latitude = self._inverse_project(x, y)
        return longitude, latitude

    def _inverse_project(self, x, y):
        sp1r = math.radians(self.standard_parallel1)
        sp2r = math.radians(self.standard_parallel2)
        orig_longitude_rad = math.radians(self.origin_longitude)
        orig_latitude_rad = math.radians(self.origin_latitude)

        cos1 = math.cos(sp1r)
        cos2 = math.cos(sp2r)
        sp1r_4 = math.pi/4 + sp1r/2
        sp2r_4 = math.pi/4 + sp2r/2
        tan1_4 = math.tan(sp1r_4)
        tan2_4 = math.tan(sp2r_4)

        n = math.log(cos1/cos2)/math.log(tan2_4/tan1_4)
        f = cos1*pow(math.tan(sp1r_4), n)/n
        rho0 = f/pow(math.tan(math.pi/4 + orig_latitude_rad/2), n)

        rho = math.sqrt(x**2 + (rho0 - y)**2)
        rho = math.copysign(rho, n)
        theta = math.atan(x/(rho0-y))

        latitude = 2*math.atan(pow(f/rho, 1/n)) - math.pi/2.0
        longitude = theta/n + orig_longitude_rad

        return math.degrees(longitude), math.degrees(latitude)

    def points_for_meridian(self, longitude):
        # meridian
        lp1 = self.project_to_map(longitude, self._min_latitude, invert_latitude=False)
        lp2 = self.project_to_map(longitude, self._max_latitude, invert_latitude=False)

        # lower border of map:
        p1 = Point(self.map_offset_x, self.map_offset_y)
        p2 = p1 + Point(1, 0)
        new_p1 = intersection_line_line(lp1, lp2, p1, p2)
        pos1 = "bot"

        if new_p1.x > self.map_offset_x + self.map_size_x:
            # right border of map
            p1 = Point(self.map_offset_x+self.map_size_x, self.map_offset_y)
            p2 = p1 + Point(0, 1)
            new_p1 = intersection_line_line(lp1, lp2, p1, p2)
            pos1 = None

        if new_p1.x < self.map_offset_x:
            # left border of map
            p1 = Point(self.map_offset_x, self.map_offset_y)
            p2 = p1 + Point(0, 1)
            new_p1 = intersection_line_line(lp1, lp2, p1, p2)
            pos1 = None

        # upper border of map:
        p1 = Point(self.map_offset_x, self.map_offset_y+self.map_size_y)
        p2 = p1 + Point(1, 0)
        new_p2 = intersection_line_line(lp1, lp2, p1, p2)
        pos2 = "top"

        if new_p2.x > self.map_offset_x + self.map_size_x:
            # right border of map
            p1 = Point(self.map_offset_x + self.map_size_x, self.map_offset_y)
            p2 = p1 + Point(0, 1)
            new_p2 = intersection_line_line(lp1, lp2, p1, p2)
            pos2 = None

        if new_p2.x < self.map_offset_x:
            # left border of map
            p1 = Point(self.map_offset_x, self.map_offset_y)
            p2 = p1 + Point(0, 1)
            new_p2 = intersection_line_line(lp1, lp2, p1, p2)
            pos2 = None

        return new_p1, new_p2, pos1, pos2

    def radius_for_parallel(self, latitude):
        p1 = self.project_to_map(self.origin_longitude, latitude)
        radius = distance(p1, self.map_pole)

        valid_intersections = []

        # Left border
        bp1 = Point(self.map_offset_x, self.map_offset_y)
        bp2 = Point(self.map_offset_x, self.map_offset_y+self.map_size_y)
        intersections = intersection_line_circle(bp1, bp2, self.map_pole, radius)
        for i in intersections:
            if self.map_offset_y < i[1] < self.map_offset_y+self.map_size_y:
                angle = math.degrees(math.atan((i[0]-self.map_pole[0])/(-i[1]+self.map_pole[1])))
                valid_intersections.append((i, "lft", angle))

        # Right border
        bp1 = (self.map_offset_x+self.map_size_x, self.map_offset_y)
        bp2 = (self.map_offset_x+self.map_size_x, self.map_offset_y+self.map_size_y)
        intersections = intersection_line_circle(bp1, bp2, self.map_pole, radius)
        for i in intersections:
            if self.map_offset_y < i[1] < self.map_offset_y+self.map_size_y:
                angle = math.degrees(math.atan((i[0]-self.map_pole[0])/(-i[1]+self.map_pole[1])))
                valid_intersections.append((i, "rt", angle))

        return radius, valid_intersections

    def inside_viewport(self, p):
        if p.x < self.map_offset_x or p.x > self.map_offset_x+self.map_size_x or p.y < self.map_offset_y or p.y > self.map_offset_y+self.map_size_y:
            return False
        else:
            return True


class InvertedLambertConformalConic(LambertConformalConic):
    def __init__(self, standard_parallel1, standard_parallel2, origin_longitude, origin_latitude):
        if standard_parallel1 > 0 or standard_parallel2 > 0 or origin_latitude > 0:
            raise ValueError("Only negative latitudes are allowed!")
        new_standard_parallel1 = -standard_parallel2
        new_standard_parallel2 = -standard_parallel1
        origin_latitude = -origin_latitude
        print "SP1:", new_standard_parallel1
        print "SP2:", new_standard_parallel2
        print "OrigLat:", origin_latitude
        LambertConformalConic.__init__(self, new_standard_parallel1, new_standard_parallel2, origin_longitude, origin_latitude)

    def set_latitude_limits(self, min_latitude, max_latitude):
        if min_latitude > 0 or max_latitude > 0:
            raise ValueError("Only negative latitudes are allowed!")
        new_min_latitude = -max_latitude
        new_max_latitude = -min_latitude
        LambertConformalConic.set_latitude_limits(self, new_min_latitude, new_max_latitude)

    @property
    def min_latitude(self):
        return -self.min_latitude

    @property
    def max_latitude(self):
        return -self._max_latitude

    @property
    def lowest_latitude(self):
        return -self._lowest_latitude

    def radius_for_parallel(self, latitude):
        # No transformation needed!
        return LambertConformalConic.radius_for_parallel(self, latitude)

    def project_to_map(self, longitude, latitude, invert_latitude=True):
        if invert_latitude:
            if latitude >= 0:
                raise ValueError("Only negative latitudes are allowed!")
            latitude = -latitude
        else:
            if latitude <= 0:
                raise ValueError("Only positive latitudes are allowed!")
        return LambertConformalConic.project_to_map(self, longitude, latitude)

    def project_from_map(self, map_x, map_y):
        longitude, latitude = LambertConformalConic.project_from_map(self, map_x, map_y)
        latitude = -latitude
        return longitude, latitude

    def calculate_map_pole(self):
        self.map_pole = self.project_to_map(0, -90)
        dummy, self._lowest_latitude = self.project_from_map(self.map_offset_x, self.map_offset_y+self.map_size_y)
        self._lowest_latitude = -self._lowest_latitude
        self.min_longitude, dummy = self.project_from_map(self.map_offset_x + self.map_size_x, self.map_offset_y)
        self.max_longitude, dummy = self.project_from_map(self.map_offset_x, self.map_offset_y)

        if self.min_longitude < 0:
            self.min_longitude += 360.0
        if self.max_longitude < 0:
            self.max_longitude += 360.0

    def to_map_coordinates(self, x, y):
        m = 200.0
        map_x = -m*x + 0.5*self.map_size_x + self.map_offset_x
        map_y = self.map_size_y + self.map_offset_y - m*y
        return map_x, map_y

    def from_map_coordinates(self, map_x, map_y):
        m = 200.0
        x = -(map_x - 0.5*self.map_size_x - self.map_offset_x)/m
        y = (self.map_size_y + self.map_offset_y - map_y)/m
        return x, y
