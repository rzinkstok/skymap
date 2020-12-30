import os
from skymap.tikz import Tikz, PaperMargin, PaperSize, PDF_FOLDER
from skymap.map import (
    MapLegend,
    MapArea,
    MapConfig,
    CoordinateGridConfig,
    EquidistantCylindricalProjection,
    EquidistantConicProjection,
)
from skymap.geometry import Point, Rectangle, Label


OUTPUT_FOLDER = os.path.join(PDF_FOLDER, "skyatlas2000")
LATITUDE_RANGE = 40.001
CONSTELLATION_DASH_PATTERN = "densely dotted"
ECLIPTIC_DASH_PATTERN = "densely dashed"
GALACTIC_DASH_PATTERN = "densely dash dot"


class SkyAtlas2000Page(Tikz):
    def __init__(self, name="none"):
        Tikz.__init__(
            self,
            name=name,
            papersize=PaperSize(width=465, height=343),
            margins=PaperMargin(left=17, bottom=8, right=17, top=10),
            normalsize=10,
        )


class SkyAtlas2000Legend(MapLegend):
    def __init__(self, tikz, chart_number):
        self.chart_number = chart_number
        MapLegend.__init__(
            self, tikz, tikz.ulcorner + Point(25, -22), tikz.urcorner + Point(-25, 0)
        )

    def draw(self):
        # Draw the corner boxes
        self.draw_rectangle(
            Rectangle(self.llcorner + Point(-25, 0), self.llcorner + Point(-2, 22))
        )
        self.draw_rectangle(
            Rectangle(self.lrcorner + Point(2, 0), self.lrcorner + Point(25, 22))
        )
        p = self.lrcorner + Point(13.5, 16)
        self.draw_label(Label(p, text="CHART NUMBER", fontsize="footnotesize"))
        p = self.lrcorner + Point(13.5, 0)
        self.draw_label(
            Label(p, text=f"\\textbf{{{self.chart_number}}}", fontsize="HUGE")
        )


def latitude_range_func(longitude, min_latitude, max_latitude):
    """Used for azimuthal maps"""
    offsets = {15: 10, 30: 2}
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


if __name__ == "__main__":
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    p = SkyAtlas2000Page()

    cc = CoordinateGridConfig()
    cc.rotate_parallel_labels = False
    cc.parallel_fontsize = "scriptsize"
    cc.rotate_poles = False
    cc.pole_marker_size = 2.5
    cc.galactic_pen_style = "densely dash dot"
    cc.galactic_tick_interval = 5
    cc.ecliptic_pen_style = "densely dashed"
    cc.ecliptic_tick_interval = 5

    mc = MapConfig()
    mc.llcorner = p.llcorner
    mc.urcorner = p.lrcorner + Point(0, 299)
    mc.origin = None
    mc.draw_inner_border = True
    mc.draw_outer_border = True
    mc.inner_border_linewidth = 0.25
    mc.outer_border_linewidth = 0.5
    mc.border_vmargin = 7
    mc.border_hmargin = 7
    mc.latitude_range = LATITUDE_RANGE
    mc.horizontal_stretch = 1.0
    mc.coordinate_grid_config = cc
    mc.clip_at_border = True

    for chart_number in range(1, 27):
        name = f"{chart_number:02d}"
        print()
        print(f"Chart {name}")
        p = p.new(name)
        SkyAtlas2000Legend(p, chart_number)

        if chart_number < 4:
            # North pole conics
            mc.center_longitude = 90 + 0.8485 + (chart_number - 1) * 120
            mc.center_latitude = 70
            mc.projection_class = EquidistantConicProjection
            mc.latitude_range_func = latitude_range_func
            mc.standard_parallel1 = 55
            mc.standard_parallel2 = 90
            mc.coordinate_grid_config.meridian_tick_borders = [
                "left",
                "bottom",
                "right",
            ]
            mc.coordinate_grid_config.parallel_tick_borders = ["top"]
            mc.origin = mc.map_llcorner + Point(132, 0.5 * mc.map_height)
            mc.coordinate_grid_config.polar_tick = True

        elif chart_number < 10:
            # North conics
            mc.center_longitude = 30 + (chart_number - 4) * 60
            mc.center_latitude = 37
            mc.latitude_range_func = None
            mc.standard_parallel1 = 25
            mc.standard_parallel2 = 47
            mc.coordinate_grid_config.meridian_tick_borders = ["bottom", "top"]
            mc.coordinate_grid_config.parallel_tick_borders = ["left", "right"]
            mc.origin = None
            mc.coordinate_grid_config.polar_tick = False

        elif chart_number < 18:
            # Equatorials
            mc.center_longitude = 30 + (chart_number - 10) * 45
            mc.center_latitude = 0
            mc.projection_class = EquidistantCylindricalProjection
            mc.horizontal_stretch = mc.reference_scale / (60.001 / mc.map_width)

        elif chart_number < 24:
            # South conics
            mc.center_longitude = 30 + (chart_number - 18) * 60
            mc.center_latitude = -37
            mc.standard_parallel1 = -47
            mc.standard_parallel2 = -25
            mc.projection_class = EquidistantConicProjection
            mc.horizontal_stretch = 1.0

        elif chart_number < 27:
            # South pole conics
            mc.center_longitude = 90 + 0.8485 + (chart_number - 24) * 120
            mc.center_latitude = -70
            mc.standard_parallel1 = -90
            mc.standard_parallel2 = -55
            mc.latitude_range_func = latitude_range_func
            mc.coordinate_grid_config.meridian_tick_borders = ["left", "top", "right"]
            mc.coordinate_grid_config.parallel_tick_borders = ["bottom"]
            mc.origin = mc.map_llcorner + Point(mc.map_width - 132, 0.5 * mc.map_height)
            mc.coordinate_grid_config.polar_tick = True

        MapArea(p, mc)
        p.render(os.path.join(OUTPUT_FOLDER, f"{name}.pdf"))
