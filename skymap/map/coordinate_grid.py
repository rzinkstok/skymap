import math
from astropy.coordinates import Longitude
import astropy.units as u
from skymap.geometry import (
    Point,
    Line,
    Label,
    Circle,
    Arc,
    SkyCoordDeg,
    ensure_angle_range,
)
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
        self.flip_labels = False
        self.labeltextfunc = None
        self.fontsize = "tiny"

        # General
        self.center_longitude = None
        self.center_latitude = None
        self.marked_ticksize = None
        self.unmarked_ticksize = None
        self.fixed_tick_reach = False
        self.label_distance = None
        self.internal_labels = False


class CoordinateGridConfig(object):
    def __init__(self):
        self.linewidth = 0.25
        self.center_longitude = None
        self.center_latitude = None

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
        self.flip_meridian_labels = False
        self.meridian_labeltextfunc = None
        self.meridian_fontsize = "scriptsize"
        self.meridian_internal_labels = False
        self.internal_label_latitude = None

        self.rotate_parallel_labels = True
        self.parallel_labeltextfunc = None
        self.parallel_fontsize = "tiny"
        self.parallel_internal_labels = False
        self.internal_label_longitude = None

        # Poles
        self.polar_tick = False
        self.rotate_poles = True
        self.pole_marker_size = 1

    @property
    def meridian_config(self):
        mc = GridLineConfig()
        mc.center_longitude = self.center_longitude
        mc.center_latitude = self.center_latitude
        mc.tick_interval = self.meridian_tick_interval
        mc.marked_tick_interval = self.meridian_marked_tick_interval
        mc.line_interval = self.meridian_line_interval
        mc.tick_borders = self.meridian_tick_borders
        mc.rotate_labels = self.rotate_meridian_labels
        mc.flip_labels = self.flip_meridian_labels
        mc.labeltextfunc = self.meridian_labeltextfunc
        mc.fontsize = self.meridian_fontsize
        mc.internal_labels = self.meridian_internal_labels
        mc.marked_ticksize = self.marked_ticksize
        mc.unmarked_ticksize = self.unmarked_ticksize
        mc.fixed_tick_reach = self.fixed_tick_reach
        mc.label_distance = self.label_distance
        return mc

    @property
    def parallel_config(self):
        pc = GridLineConfig()
        pc.center_longitude = self.center_longitude
        pc.center_latitude = self.center_latitude
        pc.tick_interval = self.parallel_tick_interval
        pc.marked_tick_interval = self.parallel_marked_tick_interval
        pc.line_interval = self.parallel_line_interval
        pc.tick_borders = self.parallel_tick_borders
        pc.rotate_labels = self.rotate_parallel_labels
        pc.labeltextfunc = self.parallel_labeltextfunc
        pc.fontsize = self.parallel_fontsize
        pc.internal_labels = self.parallel_internal_labels
        pc.marked_ticksize = self.marked_ticksize
        pc.unmarked_ticksize = self.unmarked_ticksize
        pc.fixed_tick_reach = self.fixed_tick_reach
        pc.label_distance = self.label_distance
        return pc


class GridLine(object):
    def __init__(
        self, coordinate, curve, borders, internal_point, internal_tickangle, config
    ):
        self.coordinate = coordinate
        self._curve = curve
        self.border1, self.border2 = borders
        self.internal_point = internal_point
        self.internal_tickangle = internal_tickangle

        self.config = config

        self.labeltextfunc = self.config.labeltextfunc

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
            elif border == "internal":
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
        if (
            self.border1 is None
            or not hasattr(self._curve, "p1")
            or self._curve.p1 is None
        ):
            return None
        if self.border1 not in self.config.tick_borders:
            return None
        return self.tick(self._curve.p1, self.tickangle1, self.border1)

    @property
    def tick2(self):
        if (
            self.border2 is None
            or not hasattr(self._curve, "p2")
            or self._curve.p2 is None
        ):
            return None
        if self.border2 not in self.config.tick_borders:
            return None
        return self.tick(self._curve.p2, self.tickangle2, self.border2)

    @property
    def internal_tick(self):
        if "internal" not in self.config.tick_borders or self.internal_point is None:
            return None
        if self.coordinate % self.config.line_interval == 0:
            return None

        return self.tick(self.internal_point, self.internal_tickangle, "internal")

    @property
    def internal_label(self):
        if "internal" not in self.config.tick_borders or self.internal_point is None:
            return None
        if not self.config.internal_labels:
            return None

        delta = self.tickdelta(self.internal_tickangle, "internal")
        if delta.norm > 4:
            return None

        if self.internal_tickangle == 0:
            pos = "right"
        elif self.internal_tickangle == 90:
            pos = "above"
        else:
            return None

        point = self.internal_point + 0.375 * self.config.label_distance * delta

        return self.label(point, 0, pos)

    def label(self, point, labelangle, pos):
        if self.coordinate % self.config.marked_tick_interval != 0:
            return None

        if not self.config.rotate_labels:
            labelangle = 0

        return Label(
            point,
            self.labeltext,
            self.config.fontsize,
            position=pos,
            angle=labelangle,
            fill="white",
        )

    @property
    def labeltext(self):
        return ""


class Meridian(GridLine):
    """Always in the direction of increasing latitude.

    The curve is the actual plotted line. Its p1 and p2 members are the
    start and end points. The border depends on the projection, and is a choice.
    The tick angles are always the same:
    - tickangle1 = curve.angle - 180
    - tickangle2 = curve.angle
    The label angles are a bit less simple:
    - labelangle1 = tickangla1 + 90
    - labelangle2 = tickangle2 - 90 except for south azimuthal
    - labelangle2 = tickangle2 + 90 for south azimuthal
    """

    def __init__(
        self, longitude, curve, borders, internal_point, internal_tickangle, config
    ):
        GridLine.__init__(
            self, longitude, curve, borders, internal_point, internal_tickangle, config
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

    @property
    def tickangle1(self):
        return ensure_angle_range(self._curve.angle - 180)

    @property
    def tickangle2(self):
        return ensure_angle_range(self._curve.angle)

    @property
    def labelangle1(self):
        return ensure_angle_range(self.tickangle1 + 90)

    @property
    def labelangle2(self):
        if self.config.flip_labels:
            return ensure_angle_range(self.tickangle2 + 90)
        return ensure_angle_range(self.tickangle2 - 90)

    @property
    def labelpos1(self):
        pos = self.border1
        if pos == "top":
            pos = "above"
        if pos == "bottom":
            pos = "below"
        return pos

    @property
    def labelpos2(self):
        if self.config.flip_labels:
            return "below"

        pos = self.border2
        if pos == "top":
            pos = "above"
        if pos == "bottom":
            pos = "below"
        return pos

    @property
    def label1(self):
        if self.border1 not in self.config.tick_borders:
            return None
        delta = self.tickdelta(self.tickangle1, self.border1)
        point = self._curve.p1 + self.config.label_distance * delta
        return self.label(point, self.labelangle1, self.labelpos1)

    @property
    def label2(self):
        if self.border2 not in self.config.tick_borders:
            return None
        delta = self.tickdelta(self.tickangle2, self.border2)
        point = self._curve.p2 + self.config.label_distance * delta
        return self.label(point, self.labelangle2, self.labelpos2)


class Parallel(GridLine):
    def __init__(
        self, latitude, curve, borders, internal_point, internal_tickangle, config
    ):
        GridLine.__init__(
            self, latitude, curve, borders, internal_point, internal_tickangle, config
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

    @property
    def tickangle1(self):
        if hasattr(self._curve, "angle"):
            return ensure_angle_range(self._curve.angle - 180)
        try:
            p = self._curve.p1 - self._curve.center
        except AttributeError:
            return None
        if self.config.center_latitude < 0:
            return ensure_angle_range(p.angle - 90)
        return ensure_angle_range(p.angle + 90)

    @property
    def tickangle2(self):
        if hasattr(self._curve, "angle"):
            return ensure_angle_range(self._curve.angle)
        try:
            p = self._curve.p2 - self._curve.center
        except AttributeError:
            return None
        if self.config.center_latitude < 0:
            return ensure_angle_range(p.angle + 90)
        return ensure_angle_range(p.angle - 90)

    @property
    def labelangle1(self):
        return ensure_angle_range(self.tickangle1)

    @property
    def labelangle2(self):
        return ensure_angle_range(self.tickangle2 + 180)

    @property
    def labelpos1(self):
        pos = self.border1
        if pos == "top":
            pos = "above"
        if pos == "bottom":
            pos = "below"
        return pos

    @property
    def labelpos2(self):
        pos = self.border2
        if pos == "top":
            pos = "above"
        if pos == "bottom":
            pos = "below"
        return pos

    @property
    def label1(self):
        try:
            self._curve.p1
        except AttributeError:
            return None
        if self.border1 not in self.config.tick_borders:
            return None
        delta = self.tickdelta(self.tickangle1, self.border1)
        point = self._curve.p1 + self.config.label_distance * delta
        return self.label(point, self.labelangle1, self.labelpos1)

    @property
    def label2(self):
        try:
            self._curve.p2
        except AttributeError:
            return None
        if self.border2 not in self.config.tick_borders:
            return None
        delta = self.tickdelta(self.tickangle2, self.border2)
        point = self._curve.p2 + self.config.label_distance * delta
        return self.label(point, self.labelangle2, self.labelpos2)


class CoordinateGridFactory(object):
    def __init__(
        self,
        coordinate_grid_config,
        projection,
        borderdict,
        clip_at_border,
        clipper,
        longitude_range,
        latitude_range,
        latitude_range_func=None,
    ):
        self.config = coordinate_grid_config
        self.projection = projection
        self.borderdict = borderdict
        self.clip_at_border = clip_at_border
        self.clipper = clipper
        self.min_longitude, self.max_longitude = longitude_range
        self.min_latitude, self.max_latitude = latitude_range
        self.latitude_range_func = latitude_range_func

    @property
    def meridians(self):
        config = self.config.meridian_config
        interval = config.tick_interval
        current_longitude = math.ceil(self.min_longitude / interval) * interval
        # TODO: this draws the prime meridian twice for e.g. polar maps, where min and max longitudes are the same
        while current_longitude <= self.max_longitude:
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
            if self.clip_at_border:
                meridian_parts, borders = self.clipper.clip(meridian)
                for m, b in zip(meridian_parts, borders):
                    yield Meridian(current_longitude, m, b, None, None, config)
            else:
                yield Meridian(
                    current_longitude, meridian, ["bottom", "top"], None, None, config
                )
            current_longitude += interval

    @property
    def parallels(self):
        config = self.config.parallel_config
        interval = config.tick_interval
        current_latitude = math.ceil(self.min_latitude / interval) * interval

        # Internal ticks and labels
        clipper = TikzPictureClipper(self.borderdict)

        internal_longitude = self.config.center_longitude
        if self.config.internal_label_longitude is not None:
            internal_longitude = self.config.internal_label_longitude

        internal_meridian = self.projection.meridian(
            internal_longitude, self.min_latitude, self.max_latitude
        )
        internal_tickangle = internal_meridian.angle - 90
        if internal_tickangle < 0:
            internal_tickangle += 180

        while current_latitude <= self.max_latitude:
            # print(f"Parallel at {current_latitude}")
            parallel = self.projection.parallel(
                current_latitude, self.min_longitude, self.max_longitude
            )

            internal_point = self.projection.project(
                SkyCoordDeg(internal_longitude, current_latitude)
            )
            if not clipper.point_inside(internal_point):
                internal_point = None

            if self.clip_at_border:
                parallel_parts, borders = self.clipper.clip(parallel)
                for p, b in zip(parallel_parts, borders):
                    yield Parallel(
                        current_latitude,
                        p,
                        b,
                        internal_point,
                        internal_tickangle,
                        config,
                    )
            else:
                if ensure_angle_range(self.min_longitude) != ensure_angle_range(
                    self.max_longitude
                ):
                    # Construct the arc from the endpoints
                    p1 = (
                        self.projection.project(
                            SkyCoordDeg(self.min_longitude, current_latitude)
                        )
                        - parallel.center
                    )
                    p2 = (
                        self.projection.project(
                            SkyCoordDeg(self.max_longitude, current_latitude)
                        )
                        - parallel.center
                    )
                    parallel = Arc(parallel.center, parallel.radius, p1.angle, p2.angle)

                yield Parallel(
                    current_latitude,
                    parallel,
                    ["right", "left"],
                    internal_point,
                    internal_tickangle,
                    config,
                )
            current_latitude += interval

    @property
    def polar_tick(self):
        if not self.config.polar_tick:
            return None
        latitude = 90
        delta = Point(0, 1)
        if self.config.center_latitude < 0:
            delta = Point(0, -1)
            latitude *= -1

        p1 = self.projection.project(SkyCoordDeg(0, latitude))
        p2 = p1 + self.config.marked_ticksize * delta
        return Line(p1, p2)

    @property
    def polar_label(self):
        if not self.config.polar_tick:
            return None
        latitude = 90
        delta = Point(0, 1)
        pos = "above"
        text = "+90\\textdegree"
        if self.config.center_latitude < 0:
            delta = Point(0, -1)
            latitude *= -1
            pos = "below"
            text = "--90\\textdegree"
        p1 = self.projection.project(SkyCoordDeg(0, latitude))
        p2 = p1 + self.config.label_distance * delta
        return Label(
            p2,
            text=text,
            fontsize=self.config.parallel_config.fontsize,
            angle=0,
            position=pos,
            fill="white",
        )
