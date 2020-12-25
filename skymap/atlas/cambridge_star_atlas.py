import os
from skymap.tikz import Tikz, PaperMargin, PaperSize, PDF_FOLDER
from skymap.map import (
    MapLegend,
    MapArea,
    MapConfig,
    CoordinateGridConfig,
    EquidistantConicProjection,
    EquidistantCylindricalProjection,
    AzimuthalEquidistantProjection,
)
from skymap.geometry import Point, Line, Label


OUTPUT_FOLDER = os.path.join(PDF_FOLDER, "cambridge_star_atlas")
LATITUDE_RANGE = 56
GALACTIC_ECLIPTIC_DASH_PATTERN = "densely dashed"
LEGEND_WIDTH = 16


class CambridgeStarAtlasPage(Tikz):
    def __init__(self, name="none"):
        Tikz.__init__(
            self,
            name=name,
            papersize=PaperSize(width=304, height=228),
            margins=PaperMargin(left=12, bottom=14, right=12, top=20),
            normalsize=10,
        )


class CambridgeStarAtlasLegend(MapLegend):
    def __init__(self, tikz, chart_number):
        self.chart_number = chart_number
        MapLegend.__init__(self, tikz, tikz.llcorner + Point(264, 0), tikz.urcorner)

    def draw(self):
        center = 0.5 * LEGEND_WIDTH
        self.draw_label(Label(Point(center, 189), text="Epoch", fontsize="tiny"))
        self.draw_label(
            Label(Point(center, 185), text="2000.0", fontsize="normalsize", bold=True)
        )
        self.draw_line(Line(Point(2, 183.5), Point(LEGEND_WIDTH - 2, 183.5)))
        self.draw_line(Line(Point(2, 15), Point(LEGEND_WIDTH - 2, 15)))
        self.draw_label(Label(Point(center, 11), text="Chart number", fontsize="tiny"))
        self.draw_label(
            Label(Point(center, 2), f"{self.chart_number}", bold=True, fontsize="Huge")
        )


def latitude_range_func(longitude, min_latitude, max_latitude):
    """Used for azimuthal maps"""
    offsets = {15: 10, 45: 1, 90: 0}
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
    p = CambridgeStarAtlasPage()
    cc = CoordinateGridConfig()
    mc = MapConfig()
    mc.llcorner = p.llcorner
    mc.urcorner = p.urcorner - Point(LEGEND_WIDTH, 0)
    mc.origin = None
    mc.draw_inner_border = True
    mc.draw_outer_border = True
    mc.inner_border_linewidth = 0.25
    mc.outer_border_linewidth = 0.5
    mc.border_vmargin = 5
    mc.border_hmargin = 6
    mc.latitude_range = LATITUDE_RANGE
    mc.horizontal_stretch = 1.0
    mc.coordinate_grid_config = cc

    for chart_number in range(1, 21):
        name = f"{chart_number:02d}"
        p = p.new(name)
        CambridgeStarAtlasLegend(p, chart_number)

        if chart_number < 2:
            mc.center_longitude = 0
            mc.center_latitude = 90
            mc.projection_class = AzimuthalEquidistantProjection
            mc.latitude_range_func = latitude_range_func
            mc.coordinate_grid_config.meridian_tick_borders = [
                "left",
                "right",
                "top",
                "bottom",
            ]
            mc.coordinate_grid_config.parallel_tick_borders = ["center"]
            mc.coordinate_grid_config.parallel_center_labels = True
            mc.coordinate_grid_config.parallel_marked_tick_interval = 10

        elif chart_number < 8:
            mc.center_longitude = 30 + (chart_number - 2) * 60
            mc.center_latitude = 45
            mc.projection_class = EquidistantConicProjection
            mc.standard_parallel1 = 30
            mc.standard_parallel2 = 60
            mc.coordinate_grid_config.meridian_tick_borders = ["top", "bottom"]
            mc.coordinate_grid_config.parallel_tick_borders = [
                "left",
                "center",
                "right",
            ]
            mc.coordinate_grid_config.parallel_center_labels = False
            mc.coordinate_grid_config.parallel_marked_tick_interval = 5
            mc.coordinate_grid_config.fixed_tick_reach = True
            mc.latitude_range_func = None

        elif chart_number < 14:
            mc.center_longitude = 30 + (chart_number - 8) * 60
            mc.center_latitude = 0
            mc.projection_class = EquidistantCylindricalProjection

        elif chart_number < 20:
            mc.center_longitude = 30 + (chart_number - 14) * 60
            mc.center_latitude = -45
            mc.projection_class = EquidistantConicProjection
            mc.standard_parallel1 = -60
            mc.standard_parallel2 = -30

        elif chart_number < 21:
            mc.center_longitude = 0
            mc.center_latitude = -90
            mc.projection_class = AzimuthalEquidistantProjection
            mc.latitude_range_func = latitude_range_func
            mc.coordinate_grid_config.meridian_tick_borders = [
                "left",
                "right",
                "top",
                "bottom",
            ]
            mc.coordinate_grid_config.parallel_tick_borders = ["center"]
            mc.coordinate_grid_config.parallel_center_labels = True
            mc.coordinate_grid_config.parallel_marked_tick_interval = 10

        MapArea(p, mc)
        p.render(os.path.join(OUTPUT_FOLDER, f"{name}.pdf"))
