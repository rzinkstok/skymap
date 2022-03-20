import os
import copy
from astropy.coordinates import Longitude
import astropy.units as u

from skymap.tikz import Tikz, PaperMargin, PaperSize, PDF_FOLDER
from skymap.map import (
    MapLegend,
    MapArea,
    MapConfig,
    CoordinateGridConfig,
    AzimuthalEquidistantProjection,
    EquidistantCylindricalProjection,
    EquidistantConicProjection,
)
from skymap.geometry import Point, Rectangle, Label, SkyCoordDeg


OUTPUT_FOLDER = os.path.join(PDF_FOLDER, "uranometria")
LEGEND_WIDTH = 197
LEGEND_HEIGHT = 14

PAPERSIZE = PaperSize(width=226, height=304)

EDGE_MARGIN = 11
SPINE_MARGIN = PAPERSIZE.width - LEGEND_WIDTH - EDGE_MARGIN
BOTTOM_MARGIN = 11
TOP_MARGIN = 22

LEFT_PAGE_MARGINS = PaperMargin(
    left=EDGE_MARGIN, bottom=BOTTOM_MARGIN, right=SPINE_MARGIN, top=TOP_MARGIN
)
RIGHT_PAGE_MARGINS = PaperMargin(
    left=SPINE_MARGIN, bottom=BOTTOM_MARGIN, right=EDGE_MARGIN, top=TOP_MARGIN
)


MAP_HMARGIN = 0
MAP_VMARGIN = 0

LMAP_LLCORNER = Point(EDGE_MARGIN, BOTTOM_MARGIN)
LMAP_URCORNER = Point(PAPERSIZE.width - SPINE_MARGIN, PAPERSIZE.height - TOP_MARGIN)

RMAP_LLCORNER = Point(SPINE_MARGIN, BOTTOM_MARGIN)
RMAP_URCORNER = Point(PAPERSIZE.width - SPINE_MARGIN, PAPERSIZE.height - TOP_MARGIN)

AZIMUTHAL_OFFSETS = {15: 2, 30: 1, 90: 0}

MM_PER_DEGREE = 18.5
ECLIPTIC_DASH_PATTERN = "densely dashed"
GALACTIC_DASH_PATTERN = "densely dash dot"
ECLIPTIC_LINEWIDTH = 0.35
GALACTIC_LINEWIDTH = 0.35

# The vertical offset is not the same for north and south conics!
CONICS = [
    {
        "min_latitude": 73,
        "max_latitude": 85,
        "longitude_range": 35,
        "longitude_step": -60,
        "meridian_interval": 5,
        "offset": 14,
    },
    {
        "min_latitude": 62,
        "max_latitude": 74,
        "longitude_range": 20,
        "longitude_step": -36,
        "meridian_interval": 2,
        "offset": 14,
    },
    {
        "min_latitude": 51,
        "max_latitude": 63,
        "longitude_range": 16,
        "longitude_step": -30,
        "meridian_interval": 2,
        "offset": 14,
    },
    {
        "min_latitude": 40,
        "max_latitude": 52,
        "longitude_range": 13,
        "longitude_step": -24,
        "meridian_interval": 1,
        "offset": 16,
    },
    {
        "min_latitude": 29,
        "max_latitude": 41,
        "longitude_range": 11,
        "longitude_step": -20,
        "meridian_interval": 1,
        "offset": 18,
    },
    {
        "min_latitude": 17,
        "max_latitude": 30,
        "longitude_range": 11,
        "longitude_step": -20,
        "meridian_interval": 1,
        "offset": 10,
    },
    {
        "min_latitude": 5,
        "max_latitude": 18,
        "longitude_range": 10,
        "longitude_step": -18,
        "meridian_interval": 1,
        "offset": 12,
    },
]


class UranometriaPage(Tikz):
    def __init__(self, name="none", left=True):
        if left:
            margins = LEFT_PAGE_MARGINS
        else:
            margins = RIGHT_PAGE_MARGINS
        Tikz.__init__(
            self, name=name, papersize=PAPERSIZE, margins=margins, normalsize=10
        )


class UranometriaLegend(MapLegend):
    def __init__(self, tikz, chart_number, left=True):
        self.chart_number = chart_number
        self.left = left
        MapLegend.__init__(
            self,
            tikz,
            tikz.llcorner,
            tikz.llcorner + Point(LEGEND_WIDTH, LEGEND_HEIGHT),
        )

    def draw(self):
        if self.left:
            self.draw_left()
        else:
            self.draw_right()

    def draw_left(self):
        # Draw chart number
        p1 = self.llcorner + Point(0, PAPERSIZE.height - BOTTOM_MARGIN - 18.5)
        self.draw_label(Label(p1, f"\\textbf{{{self.chart_number}}}", "huge"))

    def draw_right(self):
        # Draw chart number
        p1 = self.lrcorner + Point(0, PAPERSIZE.height - BOTTOM_MARGIN - 18.5)
        self.draw_label(Label(p1, f"\\textbf{{{self.chart_number}}}", "huge"))


def azimuthal_meridian_label(longitude):
    h, m, s = Longitude(longitude, u.degree).hms
    return f"{int(h):02d}\\raisebox{{0.3em}}{{\\tiny h}}"


def meridian_label(longitude):
    h, m, s = Longitude(longitude, u.degree).hms
    return f"{int(h):02d}\\raisebox{{0.3em}}{{\\tiny h}}{int(m):02d}\\raisebox{{0.3em}}{{\\tiny m}}"


def latitude_range_func(longitude, min_latitude, max_latitude):
    """Used for azimuthal maps"""
    offsets = {15: 2, 30: 1, 90: 0}
    offset = 0
    avg_latitude = 0.5 * (min_latitude + max_latitude)

    for l in sorted(offsets.keys(), reverse=True):
        if longitude % l == 0:
            offset = offsets[l]
            break

    if avg_latitude < 0:
        return min_latitude + offset, max_latitude
    else:
        return min_latitude, max_latitude - offset


def conic_config(chart_number):
    if chart_number > 120 and chart_number < 220:
        # 121 > 100
        # 122 > 99
        # ...
        # 219 > 2
        c = conic_config(221 - chart_number)
        c["min_latitude"], c["max_latitude"] = -c["max_latitude"], -c["min_latitude"]
        return c

    if chart_number < 2 or chart_number > 100:
        raise ValueError

    n = 1
    for c in CONICS:
        cur_n = 360 / abs(c["longitude_step"])

        if chart_number <= n + cur_n:
            conic = copy.deepcopy(c)
            conic["longitude"] = (chart_number - n - 1) * conic["longitude_step"]
            return conic
        n += cur_n


if __name__ == "__main__":
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    lp = UranometriaPage(left=True)
    rp = UranometriaPage(left=False)

    cc = CoordinateGridConfig()
    cc.rotate_parallel_labels = True
    cc.parallel_fontsize = "scriptsize"
    cc.meridian_marked_tick_interval = 15
    cc.meridian_tick_interval = 15
    cc.parallel_line_interval = 1
    cc.parallel_marked_tick_interval = 1
    cc.parallel_tick_interval = 1
    cc.marked_ticksize = 0
    cc.unmarked_ticksize = 0
    cc.fixed_tick_reach = False
    cc.label_distance = 1
    cc.rotate_meridian_labels = True
    cc.meridian_labeltextfunc = azimuthal_meridian_label
    cc.rotate_poles = True
    cc.pole_marker_size = 2.5
    cc.galactic_pen_style = "densely dash dot"
    cc.galactic_tick_interval = 1
    cc.ecliptic_pen_style = "densely dashed"
    cc.ecliptic_tick_interval = 1

    mc = MapConfig()
    mc.draw_inner_border = False
    mc.draw_outer_border = False
    mc.border_vmargin = 0
    mc.border_hmargin = 0
    mc.clip_at_border = False
    mc.horizontal_stretch = 1.0
    mc.coordinate_grid_config = cc

    for chart_number in range(1, 221):
        for subchart_number in ["A", "B"]:
            name = f"{chart_number:02d}{subchart_number}"
            print()
            print(f"Chart {name}")
            left = subchart_number == "A"

            if left:
                p = lp.new(name)
            else:
                p = rp.new(name)

            UranometriaLegend(p, chart_number, left=left)

            if chart_number == 1:
                # North pole maps
                mc.center_longitude = 270
                mc.center_latitude = 90
                mc.min_longitude = 0
                mc.max_longitude = 360
                mc.min_latitude = 84
                mc.max_latitude = 90
                mc.latitude_range = 12
                mc.projection_class = AzimuthalEquidistantProjection
                mc.latitude_range_func = latitude_range_func
                mc.coordinate_grid_config.meridian_line_interval = 15
                mc.coordinate_grid_config.meridian_marked_tick_interval = 15
                mc.coordinate_grid_config.meridian_tick_interval = 15
                mc.coordinate_grid_config.meridian_tick_borders = ["bottom"]
                mc.coordinate_grid_config.parallel_tick_borders = ["internal"]
                mc.coordinate_grid_config.parallel_internal_labels = True
                mc.coordinate_grid_config.internal_label_longitude = 0
                mc.coordinate_grid_config.meridian_labeltextfunc = (
                    azimuthal_meridian_label
                )
                mc.coordinate_grid_config.flip_meridian_labels = False

                if left:
                    mc.clipbox = Rectangle(
                        Point(-PAPERSIZE.width, -PAPERSIZE.height),
                        Point(
                            4 * MM_PER_DEGREE
                            + 0.2 * mc.coordinate_grid_config.linewidth,
                            PAPERSIZE.height,
                        ),
                    ).path
                    mc.llcorner = p.llcorner + Point(7, LEGEND_HEIGHT + 23)
                    mc.origin = mc.llcorner + Point(
                        6 * MM_PER_DEGREE, 0.5 * mc.latitude_range * MM_PER_DEGREE
                    )
                else:
                    mc.clipbox = Rectangle(
                        Point(
                            -4 * MM_PER_DEGREE
                            - 0.2 * mc.coordinate_grid_config.linewidth,
                            -PAPERSIZE.height,
                        ),
                        Point(PAPERSIZE.width, PAPERSIZE.height),
                    ).path
                    mc.llcorner = p.lrcorner + Point(
                        -7 - 10 * MM_PER_DEGREE, LEGEND_HEIGHT + 23
                    )
                    mc.origin = mc.llcorner + Point(
                        4 * MM_PER_DEGREE, 0.5 * mc.latitude_range * MM_PER_DEGREE
                    )

                mc.urcorner = mc.llcorner + Point(
                    10 * MM_PER_DEGREE, mc.latitude_range * MM_PER_DEGREE
                )

            elif chart_number == 220:
                # South pole maps
                mc.center_longitude = 90
                mc.center_latitude = -90
                mc.min_longitude = 0
                mc.max_longitude = 360
                mc.min_latitude = -90
                mc.max_latitude = -84
                mc.latitude_range = 12
                mc.projection_class = AzimuthalEquidistantProjection
                mc.latitude_range_func = latitude_range_func
                mc.coordinate_grid_config.meridian_line_interval = 15
                mc.coordinate_grid_config.meridian_marked_tick_interval = 15
                mc.coordinate_grid_config.meridian_tick_interval = 15
                mc.coordinate_grid_config.meridian_tick_borders = ["top"]
                mc.coordinate_grid_config.parallel_tick_borders = ["internal"]
                mc.coordinate_grid_config.parallel_internal_labels = True
                mc.coordinate_grid_config.internal_label_longitude = 0
                mc.coordinate_grid_config.meridian_labeltextfunc = (
                    azimuthal_meridian_label
                )
                mc.coordinate_grid_config.flip_meridian_labels = True

                if left:
                    mc.clipbox = Rectangle(
                        Point(-PAPERSIZE.width, -PAPERSIZE.height),
                        Point(
                            4 * MM_PER_DEGREE
                            + 0.2 * mc.coordinate_grid_config.linewidth,
                            PAPERSIZE.height,
                        ),
                    ).path
                    mc.llcorner = p.llcorner + Point(7, LEGEND_HEIGHT + 23)
                    mc.origin = mc.llcorner + Point(
                        6 * MM_PER_DEGREE, 0.5 * mc.latitude_range * MM_PER_DEGREE
                    )
                else:
                    mc.clipbox = Rectangle(
                        Point(
                            -4 * MM_PER_DEGREE
                            - 0.2 * mc.coordinate_grid_config.linewidth,
                            -PAPERSIZE.height,
                        ),
                        Point(PAPERSIZE.width, PAPERSIZE.height),
                    ).path
                    mc.llcorner = p.lrcorner + Point(
                        -7 - 10 * MM_PER_DEGREE, LEGEND_HEIGHT + 23
                    )
                    mc.origin = mc.llcorner + Point(
                        4 * MM_PER_DEGREE, 0.5 * mc.latitude_range * MM_PER_DEGREE
                    )

                mc.urcorner = mc.llcorner + Point(
                    10 * MM_PER_DEGREE, mc.latitude_range * MM_PER_DEGREE
                )

            elif chart_number > 100 and chart_number < 121:
                # Equatorial maps
                mc.center_longitude = -18 * (chart_number - 101)
                mc.center_latitude = 0
                if left:
                    mc.min_longitude = mc.center_longitude
                    mc.max_longitude = mc.center_longitude + 10
                else:
                    mc.min_longitude = mc.center_longitude - 10
                    mc.max_longitude = mc.center_longitude
                mc.min_latitude = -6
                mc.max_latitude = 6
                mc.latitude_range = 12
                mc.clipbox = None
                mc.projection_class = EquidistantCylindricalProjection
                mc.coordinate_grid_config.meridian_line_interval = 1
                mc.coordinate_grid_config.meridian_unmarked_tick_interval = 1
                mc.coordinate_grid_config.meridian_tick_interval = 1
                mc.coordinate_grid_config.meridian_tick_borders = ["bottom", "top"]
                mc.coordinate_grid_config.parallel_tick_borders = ["left", "right"]
                mc.coordinate_grid_config.parallel_internal_labels = False
                mc.coordinate_grid_config.meridian_labeltextfunc = meridian_label
                mc.coordinate_grid_config.flip_meridian_labels = False

                if left:
                    mc.llcorner = p.llcorner + Point(0, LEGEND_HEIGHT + 22)
                    mc.origin = mc.llcorner + Point(
                        LEGEND_WIDTH, 0.5 * mc.latitude_range * MM_PER_DEGREE
                    )
                else:
                    mc.llcorner = p.llcorner + Point(0, LEGEND_HEIGHT + 22)
                    mc.origin = mc.llcorner + Point(
                        0, 0.5 * mc.latitude_range * MM_PER_DEGREE
                    )

                mc.urcorner = mc.llcorner + Point(
                    LEGEND_WIDTH, mc.latitude_range * MM_PER_DEGREE
                )

            else:
                # Conics
                cc = conic_config(chart_number)

                mc.center_longitude = cc["longitude"]
                mc.center_latitude = 0.5 * (cc["min_latitude"] + cc["max_latitude"])
                if left:
                    mc.min_longitude = mc.center_longitude
                    mc.max_longitude = mc.center_longitude + cc["longitude_range"]
                else:
                    mc.min_longitude = mc.center_longitude - cc["longitude_range"]
                    mc.max_longitude = mc.center_longitude
                mc.min_latitude = cc["min_latitude"]
                mc.max_latitude = cc["max_latitude"]
                mc.latitude_range = cc["max_latitude"] - cc["min_latitude"]
                mc.latitude_range_func = None
                mc.clipbox = None

                mc.projection_class = EquidistantConicProjection
                mc.standard_parallel1 = mc.center_latitude - mc.latitude_range / 3
                mc.standard_parallel2 = mc.center_latitude + mc.latitude_range / 3
                mc.coordinate_grid_config.meridian_line_interval = cc[
                    "meridian_interval"
                ]
                mc.coordinate_grid_config.meridian_marked_tick_interval = cc[
                    "meridian_interval"
                ]
                mc.coordinate_grid_config.meridian_tick_interval = cc[
                    "meridian_interval"
                ]
                mc.coordinate_grid_config.meridian_tick_borders = ["bottom", "top"]
                mc.coordinate_grid_config.parallel_tick_borders = ["left", "right"]
                mc.coordinate_grid_config.parallel_internal_labels = False
                mc.coordinate_grid_config.meridian_labeltextfunc = meridian_label
                mc.coordinate_grid_config.flip_meridian_labels = False

                print("Latitude:", mc.min_latitude, mc.max_latitude)
                print("Longitude:", mc.min_longitude, mc.max_longitude)
                voffset = cc["offset"]
                if mc.center_latitude < 0:
                    # Adjust offset
                    p1 = mc.projection.project(
                        SkyCoordDeg(mc.max_longitude, mc.min_latitude)
                    )
                    p2 = mc.projection.project(
                        SkyCoordDeg(mc.min_longitude, mc.min_latitude)
                    )
                    voffset += abs(p1.y - p2.y)

                if left:
                    mc.llcorner = p.llcorner + Point(0, LEGEND_HEIGHT + voffset)
                    mc.origin = mc.llcorner + Point(
                        LEGEND_WIDTH, 0.5 * mc.latitude_range * MM_PER_DEGREE
                    )
                else:
                    mc.llcorner = p.llcorner + Point(0, LEGEND_HEIGHT + voffset)
                    mc.origin = mc.llcorner + Point(
                        0, 0.5 * mc.latitude_range * MM_PER_DEGREE
                    )

                mc.urcorner = mc.llcorner + Point(
                    LEGEND_WIDTH, mc.latitude_range * MM_PER_DEGREE
                )

            MapArea(p, mc, True)
            p.render(os.path.join(OUTPUT_FOLDER, f"{name}.pdf"))
