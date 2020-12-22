import os
from skymap.tikz import Tikz, PaperMargin, PaperSize
from skymap.map import (
    MapLegend,
    MapArea,
    MapBorderConfig,
    CoordinateGridConfig,
    EquidistantConicProjection,
    EquidistantCylindricalProjection,
    AzimuthalEquidistantProjection,
)
from skymap.geometry import Point, Line, Label, SkyCoordDeg


BASEDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_FOLDER = os.path.join(BASEDIR, "pdf", "cambridge_star_atlas")
LATITUDE_RANGE = 56
GALACTIC_ECLIPTIC_DASH_PATTERN = "densely dashed"
LEGEND_WIDTH = 16


class CambridgeStarAtlasPage(Tikz):
    def __init__(self, name):
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


class ChartConfig(object):
    def __init__(self, center_longitude, center_latitude):
        self.center_longitude = center_longitude
        self.center_latitude = center_latitude


class CambridgeStarAtlasMap(MapArea):
    def __init__(self, tikz, chart_number):
        p1 = tikz.llcorner
        p2 = tikz.urcorner - Point(LEGEND_WIDTH, 0)

        chart_config = self.get_chart_config(chart_number)
        center_longitude = chart_config.center_longitude
        center_latitude = chart_config.center_latitude

        border_config = MapBorderConfig(True, True, 0.25, 0.5, 6, 5)
        reference_scale = LATITUDE_RANGE / (p2.y - p1.y - 2 * border_config.vmargin)

        coordinate_grid_config = self.get_coordinate_grid_config(center_latitude)

        latitude_range_func = None
        if center_latitude == 90 or center_latitude == -90:
            latitude_range_func = self.latitude_range_func

        projection = self.get_projection(
            center_longitude, center_latitude, reference_scale
        )

        MapArea.__init__(
            self,
            tikz,
            p1,
            p2,
            border_config,
            coordinate_grid_config,
            projection,
            center_longitude,
            center_latitude,
            None,
            None,
            latitude_range_func,
        )

    def get_chart_config(self, chart_number):
        if chart_number < 1:
            raise ValueError
        if chart_number == 1:
            return ChartConfig(0, 90)
        if chart_number == 20:
            return ChartConfig(0, -90)
        if chart_number < 8:
            return ChartConfig(30 + (chart_number - 2) * 60, 45)
        if chart_number < 14:
            return ChartConfig(30 + (chart_number - 8) * 60, 0)
        if chart_number < 20:
            return ChartConfig(30 + (chart_number - 14) * 60, -45)
        else:
            raise ValueError

    def get_projection(self, center_longitude, center_latitude, reference_scale):
        if center_latitude == 0:
            return EquidistantCylindricalProjection(
                center_longitude,
                reference_scale=reference_scale,
                horizontal_stretch=0.958_695,
                celestial=True,
            )
        elif center_latitude == 90 or center_latitude == -90:
            return AzimuthalEquidistantProjection(
                reference_longitude=center_longitude,
                reference_scale=reference_scale,
                celestial=True,
                north=center_latitude > 0,
            )
        else:
            if center_latitude > 0:
                standard_parallel1 = 30
                standard_parallel2 = 60
            else:
                standard_parallel1 = -60
                standard_parallel2 = -30

            return EquidistantConicProjection(
                SkyCoordDeg(center_longitude, center_latitude),
                standard_parallel1,
                standard_parallel2,
                reference_scale=reference_scale,
                celestial=True,
            )

    def get_coordinate_grid_config(self, center_latitude):
        coordinate_grid_config = CoordinateGridConfig()
        if center_latitude == 90 or center_latitude == -90:
            coordinate_grid_config.parallel_tick_borders = ["center"]
            coordinate_grid_config.meridian_tick_borders = [
                "left",
                "bottom",
                "right",
                "top",
            ]
            coordinate_grid_config.parallel_center_labels = True
            coordinate_grid_config.parallel_marked_tick_interval = 10
            coordinate_grid_config.fixed_tick_reach = False
            coordinate_grid_config.parallel_fontsize = "tiny"

        return coordinate_grid_config

    def latitude_range_func(self, longitude, min_latitude, max_latitude):
        """Used for azimuthal maps"""
        d = {15: 10, 45: 1, 90: 0}
        offset = 0
        avg_latitude = 0.5 * (min_latitude + max_latitude)

        for l in sorted(d.keys(), reverse=True):
            if longitude % l == 0:
                offset = d[l]
                break

        if avg_latitude < 0:
            return min_latitude + offset, max_latitude
        else:
            return min_latitude, max_latitude - offset


if __name__ == "__main__":
    for chart_number in range(1, 21):
        name = f"{chart_number:02d}"
        c = CambridgeStarAtlasPage(name)
        CambridgeStarAtlasLegend(c, chart_number)
        CambridgeStarAtlasMap(c, chart_number)
        c.render(os.path.join(OUTPUT_FOLDER, f"{name}.pdf"))
