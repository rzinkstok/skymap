import math
import numpy

from astropy.coordinates import Longitude
import astropy.units as u

from skymap.geometry import (
    Point,
    Line,
    Label,
    Circle,
    Arc,
    Polygon,
    Clipper,
    SkyCoordDeg,
    ensure_angle_range,
)
from skymap.tikz import FontSize


GALACTIC_FRAME = "galactic"
ECLIPTIC_FRAME = "barycentricmeanecliptic"


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
        self.pole_marker_size = 2.5

        # Coordinate systems
        self.galactic_pen_style = "dashed"
        self.galactic_tick_interval = 10
        self.ecliptic_pen_style = "dashed"
        self.ecliptic_tick_interval = 10

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


class Equator(object):
    LONGITUDES = {}
    LATITUDES = {}
    GALACTIC_LONGITUDES = None
    GALACTIC_LATITUDES = None
    ECLIPTIC_LONGITUDES = None
    ECLIPTIC_LATITUDES = None

    def __init__(self, frame):
        self.frame = frame
        if frame not in self.LONGITUDES:
            self._generate_equator_points()

    def _generate_equator_points(self):
        data = [
            SkyCoordDeg(longitude, 0, frame=self.frame).icrs
            for longitude in numpy.arange(0, 360, 1)
        ]
        longitudes = [x.ra.degree for x in data]
        latitudes = [x.dec.degree for x in data]

        i = longitudes.index(min(longitudes))
        self.LONGITUDES[self.frame] = longitudes[i:] + longitudes[:i]
        self.LATITUDES[self.frame] = latitudes[i:] + latitudes[:i]

    def _latitude(self, longitude):
        longitude = ensure_angle_range(longitude)
        if longitude < self.LONGITUDES[self.frame][0]:
            i = -1
            long1 = self.LONGITUDES[self.frame][-1] - 360.0
            long2 = self.LONGITUDES[self.frame][0]
        elif longitude > self.LONGITUDES[self.frame][-1]:
            i = -1
            long1 = self.LONGITUDES[self.frame][-1]
            long2 = self.LONGITUDES[self.frame][0] + 360
        else:
            i = [x > longitude for x in self.LONGITUDES[self.frame]].index(True) - 1
            long1 = self.LONGITUDES[self.frame][i]
            long2 = self.LONGITUDES[self.frame][i + 1]
        lat1 = self.LATITUDES[self.frame][i]
        lat2 = self.LATITUDES[self.frame][i + 1]
        return lat1 + (lat2 - lat1) * (longitude - long1) / (long2 - long1)

    def _inside_area(
        self, min_longitude, max_longitude, min_latitude, max_latitude, n=100
    ):
        for i in range(n):
            long = min_longitude + (max_longitude - min_longitude) / (n - 1)
            lat = self._latitude(long)
            if min_latitude <= lat <= max_latitude:
                return True
        return False

    def points(self, min_longitude, max_longitude, min_latitude, max_latitude, n=100):
        points = []
        for i in range(n):
            long = min_longitude + i * (max_longitude - min_longitude) / (n - 1)
            lat = self._latitude(long)
            points.append((long, lat))
        return points

    def points_inside_area(
        self, min_longitude, max_longitude, min_latitude, max_latitude, n=100
    ):
        # Get the points that are inside the longitude range
        points = self.points(
            min_longitude, max_longitude, min_latitude, max_latitude, n
        )

        # Find the points inside the area
        inside = [min_latitude <= x[1] <= max_latitude for x in points]
        try:
            index1 = inside.index(True)
        except ValueError:
            return []
        try:
            index2 = inside.index(False, index1)
        except ValueError:
            index2 = len(inside)

        if index1 == 0 and index2 != len(inside) and inside[-1] is True:
            index1a = (
                inside[index2 + 1 :].index(True) + index2
            )  # Do not add 1 so it contains an extra point outside the map area
        else:
            index1a = None

        # Make sure that a single point outside is included on both ends
        index1 = max(index1 - 1, 0)
        index2 = min(index2 + 1, len(points))
        result = points[index1:index2]

        # Make sure the first and last point are on the edge of the map
        x1, y1 = points[0]
        x2, y2 = points[1]
        r = (y2 - y1) / (x2 - x1)
        if y1 > max_latitude:
            points[0] = y1 - (y1 - max_latitude) * r, max_latitude
        if y1 < min_latitude:
            points[0] = y1 + (min_latitude - y1) * r, min_latitude

        if index1a is not None:
            result = (
                points[index1a:-1] + result
            )  # Skip the last point to prevent it overlapping with the first
        return result


class EquatorialMeridian(object):
    def __init__(self, longitude, tick, label):
        self.longitude = longitude
        self.tick = tick
        self.label = label


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

        longlatborders = {
            "left": Line(
                Point(self.min_longitude, self.min_latitude),
                Point(self.min_longitude, self.max_latitude),
            ),
            "right": Line(
                Point(self.max_longitude, self.min_latitude),
                Point(self.max_longitude, self.max_latitude),
            ),
            "bottom": Line(
                Point(self.min_longitude, self.min_latitude),
                Point(self.max_longitude, self.min_latitude),
            ),
            "top": Line(
                Point(self.min_longitude, self.max_latitude),
                Point(self.max_longitude, self.max_latitude),
            ),
        }
        self.longlat_clipper = Clipper(longlatborders)

    def inside_coordinate_range(self, sp):
        ra = ensure_angle_range(
            sp.ra.degree, 0.5 * (self.min_longitude + self.max_longitude)
        )
        dec = ensure_angle_range(
            sp.dec.degree, 0.5 * (self.min_latitude + self.max_latitude)
        )
        longitude_inside = self.min_longitude <= ra <= self.max_longitude
        latitude_inside = self.min_latitude <= dec <= self.max_latitude
        return longitude_inside and latitude_inside

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
            if not self.clipper.point_inside(internal_point):
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
                if isinstance(parallel, Circle) and ensure_angle_range(
                    self.min_longitude
                ) != ensure_angle_range(self.max_longitude):
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

    def equator(self, frame):
        e = Equator(frame)
        points = e.points_inside_area(
            self.min_longitude, self.max_longitude, self.min_latitude, self.max_latitude
        )
        points = [self.projection.project(SkyCoordDeg(p[0], p[1])) for p in points]
        if not points:
            return None
        polygon = Polygon(points, closed=False)

        if self.clip_at_border:
            polys, borders = self.clipper.clip(polygon)
            if not polys:
                return None
            polygon = polys[0]

        return polygon

    @property
    def galactic_equator(self):
        return self.equator(GALACTIC_FRAME)

    @property
    def ecliptic_equator(self):
        return self.equator(ECLIPTIC_FRAME)

    def equatorial_meridian(self, tick_interval, frame):
        if tick_interval is not None:
            for i in range(int(360 / int(tick_interval))):
                l = i * tick_interval
                sp = SkyCoordDeg(l, 0, frame=frame).icrs
                if self.clip_at_border:
                    p = self.projection.project(sp)
                    if not self.clipper.point_inside(p):
                        continue
                else:
                    if not self.inside_coordinate_range(sp):
                        continue
                    p = self.projection.project(sp)

                v = self.projection.project(SkyCoordDeg(l + 1, 0, frame=frame).icrs) - p
                v = v.rotate(90) / v.norm
                tp1 = p + 0.5 * v
                tp2 = p - 0.5 * v
                lp = p + 0.4 * v
                tick = Line(tp1, tp2)
                label = Label(
                    lp,
                    text=f"\\textit{{{l}\\textdegree}}",
                    fontsize="miniscule",
                    angle=tick.angle - 90,
                    position="below",
                    fill="white",
                )
                yield EquatorialMeridian(l, tick, label)

    @property
    def galactic_meridians(self):
        return self.equatorial_meridian(
            self.config.galactic_tick_interval, GALACTIC_FRAME
        )

    @property
    def ecliptic_meridians(self):
        return self.equatorial_meridian(
            self.config.ecliptic_tick_interval, ECLIPTIC_FRAME
        )

    def pole_markers(self, frame):
        for latitude in [-90, 90]:
            sp = SkyCoordDeg(0, latitude, frame=frame).icrs
            p = self.projection.project(sp)
            if self.config.rotate_poles:
                delta1 = (
                    self.projection.project(
                        SkyCoordDeg(sp.ra.degree + 1, sp.dec.degree)
                    )
                    - p
                )
                delta2 = (
                    self.projection.project(
                        SkyCoordDeg(sp.ra.degree, sp.dec.degree + 1)
                    )
                    - p
                )
            else:
                delta1 = Point(1, 0)
                delta2 = Point(0, 1)

            delta1 *= self.config.pole_marker_size / delta1.norm
            delta2 *= self.config.pole_marker_size / delta2.norm

            if self.clipper.point_inside(p):
                yield Line(p + delta1, p - delta1)
                yield Line(p + delta2, p - delta2)

    @property
    def galactic_poles(self):
        return self.pole_markers(GALACTIC_FRAME)
