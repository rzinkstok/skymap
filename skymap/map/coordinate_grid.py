import math
from astropy.coordinates import Longitude
import astropy.units as u
from skymap.geometry import Point, Line, Label, SkyCoordDeg
from skymap.tikz import TikzPictureClipper, FontSize


class GridLineConfig(object):
    """Config for either the meridians or the parallels in the map"""

    def __init__(self):
        # Meridian/parallel specific
        self.tick_interval = None
        self.marked_tick_interval = None
        self.line_interval = None
        self.tick_borders = None
        self.rotate_labels = False
        self.labeltextfunc = None
        self.fontsize = "tiny"

        # General
        self.marked_ticksize = None
        self.unmarked_ticksize = None
        self.fixed_tick_reach = False
        self.label_distance = None
        self.center_labels = False


class CoordinateGridConfig(object):
    def __init__(self):
        self.linewidth = 0.25

        # Meridians
        self.meridian_tick_interval = 1.25
        self.meridian_marked_tick_interval = 5
        self.meridian_line_interval = 15
        self.meridian_tick_borders = ["bottom", "top"]

        # Parallels
        self.parallel_tick_interval = 1
        self.parallel_marked_tick_interval = 5
        self.parallel_line_interval = 10
        self.parallel_tick_borders = ["left", "right", "center"]

        # Tick size
        self.marked_ticksize = 1
        self.unmarked_ticksize = 0.5
        self.fixed_tick_reach = True

        # Labels
        self.label_distance = 1.5 * self.marked_ticksize

        self.rotate_meridian_labels = False
        self.meridian_labeltextfunc = None
        self.meridian_fontsize = "scriptsize"
        self.meridian_center_labels = False

        self.rotate_parallel_labels = True
        self.parallel_labeltextfunc = None
        self.parallel_fontsize = "tiny"
        self.parallel_center_labels = False

    @property
    def meridian_config(self):
        mc = GridLineConfig()
        mc.tick_interval = self.meridian_tick_interval
        mc.marked_tick_interval = self.meridian_marked_tick_interval
        mc.line_interval = self.meridian_line_interval
        mc.tick_borders = self.meridian_tick_borders
        mc.rotate_labels = self.rotate_meridian_labels
        mc.labeltextfunc = self.meridian_labeltextfunc
        mc.fontsize = self.meridian_fontsize
        mc.center_labels = self.meridian_center_labels
        mc.marked_ticksize = self.marked_ticksize
        mc.unmarked_ticksize = self.unmarked_ticksize
        mc.fixed_tick_reach = self.fixed_tick_reach
        mc.label_distance = self.label_distance
        return mc

    @property
    def parallel_config(self):
        pc = GridLineConfig()
        pc.tick_interval = self.parallel_tick_interval
        pc.marked_tick_interval = self.parallel_marked_tick_interval
        pc.line_interval = self.parallel_line_interval
        pc.tick_borders = self.parallel_tick_borders
        pc.rotate_labels = self.rotate_parallel_labels
        pc.labeltextfunc = self.parallel_labeltextfunc
        pc.fontsize = self.parallel_fontsize
        pc.center_labels = self.parallel_center_labels
        pc.marked_ticksize = self.marked_ticksize
        pc.unmarked_ticksize = self.unmarked_ticksize
        pc.fixed_tick_reach = self.fixed_tick_reach
        pc.label_distance = self.label_distance
        return pc


class GridLine(object):
    def __init__(
        self,
        coordinate,
        curve,
        borders,
        tickangles,
        config,
        center_point=None,
        center_tickangle=None,
    ):
        self.coordinate = coordinate
        self._curve = curve
        self.border1, self.border2 = borders
        self.tickangle1, self.tickangle2 = tickangles
        self.labelpos1 = None
        self.labelpos2 = None
        self.center_point = center_point
        self.center_tickangle = center_tickangle

        self.config = config

        self.labeltextfunc = None

    @property
    def curve(self):
        if self.coordinate % self.config.line_interval == 0:
            return self._curve
        return None

    def tickdelta(self, angle, border):
        a = math.radians(angle)
        if self.config.fixed_tick_reach:
            if border == "right":
                delta = Point(1, math.tan(a))
            elif border == "left":
                delta = Point(-1, math.tan(math.pi - a))
            elif border == "top":
                delta = Point(math.tan(math.pi / 2 - a), 1)
            elif border == "bottom":
                delta = Point(math.tan(a - 3 * math.pi / 2), -1)
            elif border == "center":
                delta = Point(math.cos(a), math.sin(a))
            else:
                raise ValueError(f"Invalid border: {border}")
        else:
            delta = Point(math.cos(a), math.sin(a))
        return delta

    def tick(self, point, angle, border):
        if self.coordinate % self.config.marked_tick_interval == 0:
            ticklength = self.config.marked_ticksize
        elif self.coordinate % self.config.tick_interval == 0:
            ticklength = self.config.unmarked_ticksize
        else:
            return None

        if ticklength == 0:
            return None

        delta = self.tickdelta(angle, border)
        if delta.norm > 4:
            return None
        p1 = point
        p2 = point + ticklength * delta

        return Line(p1, p2)

    @property
    def tick1(self):
        if self.tickangle1 is None or self.border1 is None or self._curve.p1 is None:
            return None
        if self.border1 not in self.config.tick_borders:
            return None
        return self.tick(self._curve.p1, self.tickangle1, self.border1)

    @property
    def tick2(self):
        if self.tickangle2 is None or self.border2 is None or self._curve.p2 is None:
            return None
        if self.border2 not in self.config.tick_borders:
            return None
        return self.tick(self._curve.p2, self.tickangle2, self.border2)

    @property
    def centertick(self):
        if "center" not in self.config.tick_borders or self.center_point is None:
            return None
        if self.coordinate % self.config.line_interval == 0:
            return None
        return self.tick(self.center_point, self.center_tickangle, "center")

    @property
    def label1(self):
        # if self._curve.p1 is None or self.border1 is None or self.tickangle1 is None:
        #    return None
        if self.border1 not in self.config.tick_borders:
            return None

        if self.border1 == "right":
            angle = self.tickangle1
        else:
            angle = self.tickangle1 + 180

        delta = self.tickdelta(self.tickangle1, self.border1)
        if delta.norm > 4:
            return None
        point = self._curve.p1 + self.config.label_distance * delta

        return self.label(point, self.border1, angle, self.labelpos1)

    @property
    def label2(self):
        # if self._curve.p2 is None or self.border2 is None or self.tickangle2 is None:
        #    return None
        if self.border2 not in self.config.tick_borders:
            return None

        if self.border2 == "left":
            angle = self.tickangle2 + 180
        else:
            angle = self.tickangle2

        delta = self.tickdelta(self.tickangle2, self.border2)
        if delta.norm > 4:
            return None
        point = self._curve.p2 + self.config.label_distance * delta
        return self.label(point, self.border2, angle, self.labelpos2)

    @property
    def centerlabel(self):
        if "center" not in self.config.tick_borders or self.center_point is None:
            return None
        if not self.config.center_labels:
            return None

        delta = self.tickdelta(self.center_tickangle, "center")
        if delta.norm > 4:
            return None

        point = self.center_point + 0.375 * self.config.label_distance * delta
        return self.label(point, "center", 0, "above")

    def label(self, point, border, angle, pos):
        if self.coordinate % self.config.marked_tick_interval != 0:
            return None

        if not self.config.rotate_labels:
            angle = 0

        if pos is None:
            if border == "right":
                pos = "right"
            elif border == "left":
                pos = "left"
            elif border == "top":
                pos = "above"
            elif border == "bottom":
                pos = "below"
            else:
                raise ValueError(f"Invalid border: {border}")

        return Label(
            point,
            self.labeltext,
            self.config.fontsize,
            position=pos,
            angle=angle,
            fill="white",
        )

    @property
    def labeltext(self):
        return ""


class Meridian(GridLine):
    def __init__(
        self,
        longitude,
        curve,
        borders,
        tickangles,
        config,
        center_point=None,
        center_tickangle=None,
    ):
        GridLine.__init__(
            self,
            longitude,
            curve,
            borders,
            tickangles,
            config,
            center_point,
            center_tickangle,
        )
        self.longitude = self.coordinate

    @property
    def labeltext(self):
        if self.labeltextfunc is not None:
            return self.labeltextfunc(self.longitude)
        h, m, s = Longitude(self.longitude, u.degree).hms

        if m == 0:
            text = f"\\textbf{{{int(h)}}}\\raisebox{{0.3em}}{{\\tiny h}}"
        else:
            sfont = FontSize().smaller(self.config.fontsize)
            xsfont = FontSize().smaller(self.config.fontsize, 2)
            text = f"\\{sfont} {int(m)}\\raisebox{{0.3em}}{{\\{xsfont} m}}"
        return text


class Parallel(GridLine):
    def __init__(
        self,
        latitude,
        curve,
        borders,
        tickangles,
        config,
        center_point=None,
        center_tickangle=None,
    ):
        GridLine.__init__(
            self,
            latitude,
            curve,
            borders,
            tickangles,
            config,
            center_point,
            center_tickangle,
        )
        self.latitude = self.coordinate

    @property
    def labeltext(self):
        if self.labeltextfunc is not None:
            return self.labeltextfunc(self.latitude)
        if self.latitude < 0:
            return f"--{abs(int(self.latitude))}\\textdegree"
        elif self.latitude > 0:
            return f"+{int(self.latitude)}\\textdegree"
        return "0\\textdegree"


class CoordinateGridFactory(object):
    def __init__(
        self,
        coordinate_grid_config,
        projection,
        borderdict,
        clipper,
        longitude_range,
        latitude_range,
        latitude_range_func=None,
    ):
        self.config = coordinate_grid_config
        self.projection = projection
        self.borderdict = borderdict
        self.clipper = clipper
        self.min_longitude, self.max_longitude = longitude_range
        self.min_latitude, self.max_latitude = latitude_range
        self.latitude_range_func = latitude_range_func

    @property
    def meridians(self):
        config = self.config.meridian_config
        interval = config.tick_interval
        current_longitude = math.ceil(self.min_longitude / interval) * interval
        while current_longitude < self.max_longitude:
            # print(f"Meridian at {current_longitude}")
            if self.latitude_range_func:
                min_latitude, max_latitude = self.latitude_range_func(
                    current_longitude, self.min_latitude, self.max_latitude
                )
            else:
                min_latitude, max_latitude = self.min_latitude, self.max_latitude

            meridian = self.projection.meridian(
                current_longitude, min_latitude, max_latitude
            )

            meridian_parts, borders, angles = self.clipper.clip(meridian)
            for m, b, a in zip(meridian_parts, borders, angles):
                yield Meridian(current_longitude, m, b, a, config)

            current_longitude += interval

    @property
    def parallels(self):
        config = self.config.parallel_config
        interval = config.tick_interval
        current_latitude = math.ceil(self.min_latitude / interval) * interval

        center_meridian = self.projection.meridian(
            self.projection.center_longitude, self.min_latitude, self.max_latitude
        )

        if hasattr(self.projection, "north") and not self.projection.north:
            center_angle = center_meridian.angle + 90
        else:
            center_angle = center_meridian.angle - 90

        while current_latitude <= self.max_latitude:
            # print(f"Parallel at {current_latitude}")
            parallel = self.projection.parallel(
                current_latitude, self.min_longitude, self.max_longitude
            )

            center_point = self.projection.project(
                SkyCoordDeg(self.projection.center_longitude, current_latitude)
            )
            clipper = TikzPictureClipper(self.borderdict)
            if not clipper.point_inside(center_point):
                center_point = None

            parallel_parts, borders, angles = self.clipper.clip(parallel)
            for p, b, a in zip(parallel_parts, borders, angles):
                yield Parallel(
                    current_latitude, p, b, a, config, center_point, center_angle
                )

            current_latitude += interval
