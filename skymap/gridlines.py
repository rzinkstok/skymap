from skymap.geometry import Point, Line, HourAngle
import math


class Label(object):
    def __init__(self, point, text, position, fontsize, angle=0, fill=None):
        self.point = point
        self.text = text
        self.position = position
        self._angle = angle
        self.fontsize = fontsize
        self.fill = fill

    @property
    def angle(self):
        if self._angle is not None:
            return self._angle
        return 0


class GridLineFactory(object):
    def __init__(self):
        self.meridian_tick_interval = 1.25
        self.meridian_marked_tick_interval = 5
        self.meridian_line_interval = 15

        self.parallel_tick_interval = 1
        self.parallel_marked_tick_interval = 5
        self.parallel_line_interval = 10

        self.marked_ticksize = 1
        self.unmarked_ticksize = 0.5

        self.label_distance = 2 * self.marked_ticksize
        self.rotate_meridian_labels = False
        self.meridian_labeltextfunc = None
        self.meridian_fontsize = "scriptsize"

        self.rotate_parallel_labels = False
        self.parallel_labeltextfunc = None
        self.parallel_fontsize = "scriptsize"

    def meridian(self, longitude, meridian):
        m = Meridian(longitude, meridian)
        m.tick_interval = self.meridian_tick_interval
        m.marked_tick_interval = self.meridian_marked_tick_interval
        m.line_interval = self.meridian_line_interval
        m.marked_ticksize = self.marked_ticksize
        m.unmarked_ticksize = self.unmarked_ticksize
        m.label_distance = self.label_distance
        m.rotate_label = self.rotate_meridian_labels
        m.labeltextfunc = self.meridian_labeltextfunc
        m.fontsize = self.meridian_fontsize
        return m

    def parallel(self, latitude, parallel):
        p = Parallel(latitude, parallel)
        p.tick_interval = self.parallel_tick_interval
        p.marked_tick_interval = self.parallel_marked_tick_interval
        p.line_interval = self.parallel_line_interval
        p.marked_ticksize = self.marked_ticksize
        p.unmarked_ticksize = self.unmarked_ticksize
        p.label_distance = self.label_distance
        p.rotate_label = self.rotate_parallel_labels
        p.labeltextfunc = self.parallel_labeltextfunc
        p.fontsize = self.parallel_fontsize
        return p


class GridLine(object):
    def __init__(self):
        # Must be added
        self.tickangle1 = None
        self.tickangle2 = None

        self.border1 = None
        self.border2 = None

        self.labelangle1 = None
        self.labelangle2 = None

        self.labelpos1 = None
        self.labelpos2 = None

        self.fontsize = None

        # Settings
        self.tick_interval = None
        self.marked_tick_interval = None
        self.line_interval = None

        self.marked_ticksize = None
        self.unmarked_ticksize = None

        self.label_distance = None
        self.rotate_label = None
        self.labeltextfunc = None

    @property
    def tick1(self):
        if self.tickangle1 is None or self.border1 is None or self.p1 is None:
            return None
        return self.tick(self.p1, self.tickangle1, self.border1)

    @property
    def tick2(self):
        if self.tickangle2 is None or self.border2 is None or self.p2 is None:
            return None
        return self.tick(self.p2, self.tickangle2, self.border2)

    @property
    def reference_tick(self):
        if self.reference_tickangle is None or self.reference_tick_p is None:
            return None
        return self.tick(self.reference_tick_p, self.reference_tick_angle)

    def tickdelta(self, angle, border):
        a = math.radians(angle)
        if border == 'right':
            delta = Point(1, math.tan(a))
        elif border == 'left':
            delta = Point(-1, math.tan(math.pi - a))
        elif border == 'top':
            delta = Point(math.tan(math.pi / 2 - a), 1)
        elif border == 'bottom':
            delta = Point(math.tan(a - 3 * math.pi / 2), -1)
        else:
            raise ValueError("Invalid border: {}".format(border))
        return delta

    def tick(self, point, angle, border):
        if self.coordinate % self.marked_tick_interval == 0:
            ticklength = self.marked_ticksize
        elif self.coordinate % self.tick_interval == 0:
            ticklength = self.unmarked_ticksize
        else:
            return None

        if ticklength == 0:
            return None

        delta = self.tickdelta(angle, border)
        if delta.distance(Point(0,0)) > 4:
            return None
        p1 = point
        p2 = point + ticklength * delta

        return Line(p1, p2)

    @property
    def label1(self):
        if self.p1 is None or self.border1 is None or self.tickangle1 is None:
            return None
        angle = self.labelangle1
        delta = self.tickdelta(self.tickangle1, self.border1)
        if delta.distance(Point(0,0)) > 4:
            return None
        point = self.p1 + self.label_distance * delta
        return self.label(point, self.border1, angle, self.labelpos1)

    @property
    def label2(self):
        if self.p2 is None or self.border2 is None or self.tickangle2 is None:
            return None
        angle = self.labelangle2
        delta = self.tickdelta(self.tickangle2, self.border2)
        if delta.distance(Point(0,0)) > 4:
            return None
        point = self.p2 + self.label_distance * delta
        return self.label(point, self.border2, angle, self.labelpos2)

    def label(self, point, border, angle, pos):
        if self.coordinate % self.marked_tick_interval != 0:
            return None

        if pos is None:
            if border == 'right':
                pos = 0
            elif border == 'left':
                pos = 180
            elif border == 'top':
                pos = 90
            elif border == 'bottom':
                pos = 270
            else:
                raise ValueError("Invalid border: {}".format(border))

        text = self.labeltext()

        return Label(point, text, pos, self.fontsize, angle, fill='white')


class Meridian(GridLine):
    def __init__(self, longitude, meridian):
        GridLine.__init__(self)
        self.longitude = longitude
        self._meridian = meridian
        try:
            self.p1 = meridian.p1
            self.p2 = meridian.p2
        except AttributeError:
            self.p1 = None
            self.p2 = None
        self.coordinate = self.longitude

    @property
    def meridian(self):
        if self.longitude % self.line_interval == 0:
            return self._meridian
        return None

    def labeltext(self):
        if self.labeltextfunc is not None:
            return self.labeltextfunc(self.longitude)
        h = HourAngle()
        h.from_degrees(self.longitude)
        if h.minutes == 0:
            text = "\\textbf{{{}}}\\raisebox{{0.3em}}{{\\tiny h}}".format(h.hours)
        else:
            text = "{}\\raisebox{{0.3em}}{{\\nano m}}".format(h.minutes)
            self.fontsize = "tiny"
        return text


class Parallel(GridLine):
    def __init__(self, latitude, parallel):
        GridLine.__init__(self)
        self.latitude = latitude
        self._parallel = parallel

        try:
            self.p1 = parallel.p1
            self.p2 = parallel.p2
        except AttributeError:
            self.p1 = None
            self.p2 = None
        self.coordinate = self.latitude

    @property
    def parallel(self):
        if self.latitude % self.line_interval == 0:
            return self._parallel
        return None

    def labeltext(self):
        if self.labeltextfunc is not None:
            return self.labeltextfunc(self.latitude)
        if self.latitude < 0:
            return "--{}\\textdegree".format(abs(int(self.latitude)))
        elif self.latitude > 0:
            return "+{}\\textdegree".format(int(self.latitude))
        return "0\\textdegree"
