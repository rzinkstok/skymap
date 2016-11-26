import math


class StereographicCylinder(object):
    def __init__(self, standard_parallel, source_distance_scale):
        self.standard_parallel_rad = 2*math.pi*standard_parallel/360.0
        self.source_distance_scale = source_distance_scale

    def set_longitude_limits(self, min_longitude, max_longitude):
        self.min_longitude = min_longitude
        self.max_longitude = max_longitude
        if self.max_longitude > self.min_longitude:
            self.orig_longitude = 0.5*(min_longitude+max_longitude)
        else:
            self.orig_longitude = 0.5*(min_longitude+max_longitude) - 180
        print "Origin longitude:", self.orig_longitude
        self.orig_longitude_rad = 2*math.pi*self.orig_longitude/360.0
        self.min_x, dummy = self.project(self.min_longitude, 0)
        self.max_x, dummy = self.project(self.max_longitude, 0)
        self.extent_x = self.max_x - self.min_x
        print "Min x:", self.min_x
        print "Max x:", self.max_x

    def set_latitude_limits(self, min_latitude, max_latitude):
        self.min_latitude = min_latitude
        self.max_latitude = max_latitude
        dummy, self.min_y = self.project(0, self.min_latitude)
        dummy, self.max_y = self.project(0, self.max_latitude)
        self.extent_y = self.max_y - self.min_y

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

    def project(self, longitude, latitude):
        # longitude, latitude: in degrees
        # longitude: east-west
        # latitude: north-south
        longitude_rad = 2*math.pi*longitude/360.0
        if longitude_rad < 0:
            longitude_rad += 2*math.pi
        latitude_rad = 2*math.pi*latitude/360.0
        x = longitude_rad-self.orig_longitude_rad
        if x > math.pi:
            x -= 2*math.pi
        y = math.sin(latitude_rad) * (math.cos(self.standard_parallel_rad) + self.source_distance_scale)/(math.cos(latitude_rad) + self.source_distance_scale)
        return x, y

    def project_to_map(self, longitude, latitude):
        x, y = self.project(longitude, latitude)
        return self.to_map_coordinates(x, y)

    def points_for_parallel(self, latitude):
        p1 = self.project_to_map(self.min_longitude, latitude)
        p2 = self.project_to_map(self.max_longitude, latitude)
        return p1, p2, "rt", "lft"

    def points_for_meridian(self, longitude):
        p1 = self.project_to_map(longitude, self.min_latitude)
        p2 = self.project_to_map(longitude, self.max_latitude)
        return p1, p2, "bot", "top"

    def inside_viewport(self, x, y):
        if x < self.map_offset_x or x > self.map_offset_x+self.map_size_x or y < self.map_offset_y or y > self.map_offset_y+self.map_size_y:
            return False
        else:
            return True


class LambertConformalConic(object):
    def __init__(self, standard_parallel1, standard_parallel2, origin_longitude, origin_latitude, hemisphere):
        self.standard_parallel1 = standard_parallel1
        self.standard_parallel2 = standard_parallel2
        self.origin_longitude = origin_longitude
        self.origin_latitude = origin_latitude
        self.hemisphere = hemisphere

    def set_latitude_limits(self, min_latitude, max_latitude):
        self.min_latitude = min_latitude
        self.max_latitude = max_latitude
        dummy, self.min_y = self.project(self.origin_longitude, self.min_latitude)
        dummy, self.max_y = self.project(self.origin_longitude, self.max_latitude)
        self.extent_y = self.max_y - self.min_y

    def set_map_size(self, size_x, size_y):
        self.map_size_x = size_x
        self.map_size_y = size_y

    def set_map_offset(self, offset_x, offset_y):
        self.map_offset_x = offset_x
        self.map_offset_y = offset_y

    def calculate_map_pole(self):
        self.map_pole = self.project_to_map(0, 90)

        # Calculate min/max longitude on map?
        if self.hemisphere == "N":
            self.min_longitude, dummy = self.project_from_map(self.map_offset_x + self.map_size_x, self.map_offset_y + self.map_size_y)
            self.max_longitude, dummy = self.project_from_map(self.map_offset_x, self.map_offset_y + self.map_size_y)
            dummy, self.lowest_latitude = self.project_from_map(self.map_offset_x, self.map_offset_y)
        else:
            self.min_longitude, dummy = self.project_from_map(self.map_offset_x + self.map_size_x, self.map_offset_y)
            self.max_longitude, dummy = self.project_from_map(self.map_offset_x, self.map_offset_y)
            dummy, self.lowest_latitude = self.project_from_map(self.map_offset_x, self.map_offset_y + self.map_size_y)

        if self.min_longitude < 0:
            self.min_longitude += 360.0
        if self.max_longitude < 0:
            self.max_longitude += 360.0

    def to_map_coordinates(self, x, y):
        map_x = -self.map_size_x*x + 0.5*self.map_size_x + self.map_offset_x
        if self.hemisphere == "N":
            map_y = self.map_offset_y + self.map_size_y*(y-self.min_y)/self.extent_y
        else:
            map_y = self.map_size_y + self.map_offset_y - self.map_size_y*(y-self.min_y)/self.extent_y
        return map_x, map_y

    def from_map_coordinates(self, map_x, map_y):
        x = (-map_x + 0.5*self.map_size_x + self.map_offset_x)/self.map_size_x
        if self.hemisphere == "N":
            y = self.extent_y*(map_y - self.map_offset_y)/self.map_size_y + self.min_y
        else:
            y = self.extent_y*(self.map_size_y + self.map_offset_y - map_y)/self.map_size_y + self.min_y
        return x, y

    def project(self, longitude, latitude):
        # longitude, latitude: in degrees
        # longitude: east-west
        # latitude: north-south

        longitude_rad = 2*math.pi*longitude/360.0
        latitude_rad = 2*math.pi*latitude/360.0

        sp1r = 2*math.pi*self.standard_parallel1/360.0
        sp2r = 2*math.pi*self.standard_parallel2/360.0
        orig_longitude_rad = 2*math.pi*self.origin_longitude/360.0
        orig_latitude_rad = 2*math.pi*self.origin_latitude/360.0

        cos1 = math.cos(sp1r)
        cos2 = math.cos(sp2r)
        sp1r_4 = math.pi/4 + sp1r/2
        sp2r_4 = math.pi/4 + sp2r/2
        tan1_4 = math.tan(sp1r_4)
        tan2_4 = math.tan(sp2r_4)

        n = math.log(cos1/cos2)/math.log(tan2_4/tan1_4)
        F = cos1*pow(math.tan(sp1r_4), n)/n
        rho0 = F/pow(math.tan(math.pi/4 + orig_latitude_rad/2), n)

        if longitude_rad-orig_longitude_rad > math.pi:
            theta = n*(longitude_rad-orig_longitude_rad - 2*math.pi)
        else:
            theta = n*(longitude_rad-orig_longitude_rad)

        rho = F/pow(math.tan(math.pi/4 + latitude_rad/2), n)

        x = rho*math.sin(theta)
        y = rho0 - rho * math.cos(theta)

        return x, y

    def project_to_map(self, longitude, latitude):
        #if self.hemisphere == "S":
        #    latitude = -latitude
        x, y = self.project(longitude, latitude)
        return self.to_map_coordinates(x, y)

    def project_from_map(self, map_x, map_y):
        x, y = self.from_map_coordinates(map_x, map_y)
        longitude, latitude = self.inverse_project(x, y)
        #if self.hemisphere == "S":
        #    latitude = -latitude
        return longitude, latitude

    def inverse_project(self, x, y):
        sp1r = 2*math.pi*self.standard_parallel1/360.0
        sp2r = 2*math.pi*self.standard_parallel2/360.0
        orig_longitude_rad = 2*math.pi*self.origin_longitude/360.0
        orig_latitude_rad = 2*math.pi*self.origin_latitude/360.0

        cos1 = math.cos(sp1r)
        cos2 = math.cos(sp2r)
        sp1r_4 = math.pi/4 + sp1r/2
        sp2r_4 = math.pi/4 + sp2r/2
        tan1_4 = math.tan(sp1r_4)
        tan2_4 = math.tan(sp2r_4)

        n = math.log(cos1/cos2)/math.log(tan2_4/tan1_4)
        F = cos1*pow(math.tan(sp1r_4), n)/n
        rho0 = F/pow(math.tan(math.pi/4 + orig_latitude_rad/2), n)

        rho = math.sqrt(x**2 + (rho0 - y)**2)
        rho = math.copysign(rho, n)
        theta = math.atan(x/(rho0-y))

        latitude = 2*math.atan(pow(F/rho, 1/n)) - math.pi/2.0
        longitude = theta/n + orig_longitude_rad

        return 360.0*longitude/(2*math.pi), 360.0*latitude/(2*math.pi)


    def points_for_meridian(self, longitude):
        p1 = self.project_to_map(longitude, self.min_latitude)
        p2 = self.project_to_map(longitude, self.max_latitude)

        # meridian (x1y2 - x2y1)
        a1 = p1[1]-p2[1]
        b1 = p2[0]-p1[0]
        c1 = p1[0]*p2[1] - p2[0]*p1[1]

        # lower border of map:
        a2 = 0
        b2 = 1
        c2 = -self.map_offset_y

        y1 = (c1*a2 - c2*a1)/(a1*b2 - a2*b1)
        x1 = (c1*b2 - b1*c2)/(b1*a2 - a1*b2)
        new_p1 = (x1, y1)
        pos1 = "bot"

        if x1 > self.map_offset_x + self.map_size_x:
            #right border of map
            a2 = -1
            b2 = 0
            c2 = self.map_offset_x + self.map_size_x

            y1 = (c1*a2 - c2*a1)/(a1*b2 - a2*b1)
            x1 = (c1*b2 - b1*c2)/(b1*a2 - a1*b2)
            new_p1 = (x1, y1)
            pos1 = None

        if x1 < self.map_offset_x:
            #left border of map
            a2 = -1
            b2 = 0
            c2 = self.map_offset_x

            y1 = (c1*a2 - c2*a1)/(a1*b2 - a2*b1)
            x1 = (c1*b2 - b1*c2)/(b1*a2 - a1*b2)
            new_p1 = (x1, y1)
            pos1 = None

        # upper border of map:
        a2 = 0
        b2 = 1
        c2 = -self.map_offset_y-self.map_size_y

        y2 = (c1*a2 - c2* a1)/(a1*b2 - a2*b1)
        x2 = (c1*b2 - b1*c2)/(b1*a2 - a1*b2)
        new_p2 = (x2, y2)
        pos2 = "top"

        if x2 > self.map_offset_x + self.map_size_x:
            #right border of map
            a2 = -1
            b2 = 0
            c2 = self.map_offset_x + self.map_size_x

            y2 = (c1*a2 - c2*a1)/(a1*b2 - a2*b1)
            x2 = (c1*b2 - b1*c2)/(b1*a2 - a1*b2)
            new_p2 = (x2, y2)
            pos2 = None

        if x2 < self.map_offset_x:
            #left border of map
            a2 = -1
            b2 = 0
            c2 = self.map_offset_x

            y2 = (c1*a2 - c2*a1)/(a1*b2 - a2*b1)
            x2 = (c1*b2 - b1*c2)/(b1*a2 - a1*b2)
            new_p2 = (x2, y2)
            pos2 = None

        return new_p1, new_p2, pos1, pos2

    def distance(self, p1, p2):
        return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

    def intersection_line_circle(self, p1, p2, center, r):
        # ax+by+c = 0
        a = p1[1]-p2[1]
        b = p2[0]-p1[0]
        c = - p1[0]*p2[1] + p2[0]*p1[1]
        cp = c - a*center[0] - b*center[1]

        absq = (a**2 + b**2)

        if absq * r**2 - cp**2 <=0:
            return []

        bigroot = math.sqrt(absq * r**2 - cp**2)

        ksi1 = (a*cp + b*bigroot)/absq
        ksi2 = (a*cp - b*bigroot)/absq
        eta1 = (b*cp - a*bigroot)/absq
        eta2 = (b*cp + a*bigroot)/absq

        x1 = center[0] + ksi1
        x2 = center[0] + ksi2
        y1 = center[1] + eta1
        y2 = center[1] + eta2

        ip1 = (x1, y1)
        ip2 = (x2, y2)

        return ip1, ip2

    def radius_for_parallel(self, latitude):
        p1 = self.project_to_map(self.origin_longitude, latitude)
        #print latitude, "|", p1, "->", self.map_pole, ":", self.distance(p1, self.map_pole)
        radius = self.distance(p1, self.map_pole)

        valid_intersections = []
        label_positions = []

        # Left border
        bp1 = (self.map_offset_x, self.map_offset_y)
        bp2 = (self.map_offset_x, self.map_offset_y+self.map_size_y)
        intersections = self.intersection_line_circle(bp1, bp2, self.map_pole, radius)
        for i in intersections:
            if self.map_offset_y < i[1] < self.map_offset_y+self.map_size_y:
                angle = 360.0*math.atan((i[0]-self.map_pole[0])/(-i[1]+self.map_pole[1]))/(2*math.pi)
                valid_intersections.append((i, "lft", angle))

        # Right border
        bp1 = (self.map_offset_x+self.map_size_x, self.map_offset_y)
        bp2 = (self.map_offset_x+self.map_size_x, self.map_offset_y+self.map_size_y)
        intersections = self.intersection_line_circle(bp1, bp2, self.map_pole, radius)
        for i in intersections:
            if self.map_offset_y < i[1] < self.map_offset_y+self.map_size_y:
                angle = 360.0*math.atan((i[0]-self.map_pole[0])/(-i[1]+self.map_pole[1]))/(2*math.pi)
                valid_intersections.append((i, "rt", angle))

        return radius, valid_intersections

    def inside_viewport(self, x, y):
        if x < self.map_offset_x or x > self.map_offset_x+self.map_size_x or y < self.map_offset_y or y > self.map_offset_y+self.map_size_y:
            return False
        else:
            return True