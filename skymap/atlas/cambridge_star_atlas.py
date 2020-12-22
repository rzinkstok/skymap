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

# OUTPUT_FOLDER = os.path.join(BASEDIR, "cambridge_star_atlas")


LATITUDE_RANGE = 56
AZIMUTHAL_MERIDIAN_OFFSETS = {15: 10, 45: 1, 90: 0}
GALACTIC_ECLIPTIC_DASH_PATTERN = "densely dashed"
LEGEND_WIDTH = 16


def azimuthal_latitude_range(longitude):
    d = {15: 10, 45: 1, 90: 0}
    offset = 0
    for l in sorted(d.keys(), reverse=True):
        if longitude % l == 0:
            offset = d[l]
            break

    return 90 - offset


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
        self.draw_label(Label(Point(8, 189), text="Epoch", fontsize="tiny"))
        self.draw_label(
            Label(Point(8, 185), text="2000.0", fontsize="normalsize", bold=True)
        )
        self.draw_line(Line(Point(2, 183.5), Point(14, 183.5)))
        self.draw_line(Line(Point(2, 15), Point(14, 15)))
        self.draw_label(Label(Point(8, 11), text="Chart number", fontsize="tiny"))
        self.draw_label(
            Label(Point(8, 2), f"{self.chart_number}", bold=True, fontsize="Huge")
        )


class ChartConfig(object):
    def __init__(self, center_longitude, center_latitude):
        self.center_longitude = center_longitude
        self.center_latitude = center_latitude


class CambridgeStarAtlasMap(MapArea):
    def __init__(self, tikz, chart_number):
        # Determine these using the chart number
        chart_configs = {
            1: ChartConfig(90, 90),
            2: ChartConfig(30, 45),
            3: ChartConfig(90, 45),
            5: ChartConfig(210, 45),
            8: ChartConfig(30, 0),
            14: ChartConfig(30, -45),
            15: ChartConfig(90, -45),
            17: ChartConfig(210, -45),
            20: ChartConfig(0, -90),
        }

        chart_config = chart_configs[chart_number]
        p1 = tikz.llcorner
        p2 = tikz.urcorner - Point(LEGEND_WIDTH, 0)
        center_longitude = chart_config.center_longitude
        center_latitude = chart_config.center_latitude

        border_config = MapBorderConfig(True, True, 0.25, 0.5, 6, 5)
        coordinate_grid_config = CoordinateGridConfig()
        reference_scale = 56 / (p2.y - p1.y - 2 * border_config.vmargin)
        latitude_range_func = None

        if center_latitude == 0:
            projection = EquidistantCylindricalProjection(
                center_longitude,
                reference_scale=reference_scale,
                horizontal_stretch=0.958_695,
                celestial=True,
            )

        elif center_latitude == 90 or center_latitude == -90:
            projection = AzimuthalEquidistantProjection(
                reference_scale=reference_scale,
                celestial=True,
                north=center_latitude > 0,
            )
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
            latitude_range_func = self.latitude_range_func

        else:
            standard_parallel1 = 30
            standard_parallel2 = 60
            if center_latitude < 0:
                standard_parallel1, standard_parallel2 = (
                    -standard_parallel2,
                    -standard_parallel1,
                )

            projection = EquidistantConicProjection(
                SkyCoordDeg(center_longitude, center_latitude),
                standard_parallel1,
                standard_parallel2,
                reference_scale=reference_scale,
                celestial=True,
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

    def latitude_range_func(self, longitude, min_latitude, max_latitude):
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


# def figure(fn):
#     return TikzFigure(
#         fn,
#         papersize=PAPERSIZE,
#         left_margin=LEFT_MARGIN,
#         right_margin=RIGHT_MARGIN,
#         bottom_margin=BOTTOM_MARGIN,
#         top_margin=TOP_MARGIN,
#         fontsize=10,
#     )
#
#
# def legend(figure, chart_number):
#     l = DrawingArea(f.llcorner + Point(264, 0), f.urcorner, f.llcorner + Point(264, 0))
#     figure.add(l)
#     l.draw_label(GridLineLabel(Point(8, 189), "Epoch", 90, "tiny"))
#     l.draw_label(GridLineLabel(Point(8, 185), "\\textbf{2000.0}", 90, "normalsize"))
#     l.draw_line(Line(Point(2, 183.5), Point(14, 183.5)))
#     l.draw_line(Line(Point(2, 15), Point(14, 15)))
#     l.draw_label(GridLineLabel(Point(8, 11), "Chart number", 90, "tiny"))
#     l.draw_label(
#         GridLineLabel(Point(8, 2), "\\textbf{{{}}}".format(chart_number), 90, "Huge")
#     )
#
#


# if __name__ == "__main__":
#     if not os.path.exists(OUTPUT_FOLDER):
#         os.makedirs(OUTPUT_FOLDER)
#
#     # North pole
#     chart_number = 1
#     fn = "{:02}".format(chart_number)
#     f = figure(fn)
#
#     m = AzimuthalEquidistantMapArea(
#         MAP_LLCORNER,
#         MAP_URCORNER,
#         hmargin=MAP_HMARGIN,
#         vmargin=MAP_VMARGIN,
#         latitude_range=LATITUDE_RANGE,
#         celestial=True,
#         north=True,
#     )
#     f.add(m)
#
#     m.draw_meridians(origin_offsets=AZIMUTHAL_MERIDIAN_OFFSETS)
#     m.draw_parallels()
#     m.draw_internal_parallel_ticks(0, labels=True)
#     with m.clip(m.clipping_path):
#         m.draw_constellations()
#     m.draw_ecliptic(tickinterval=10, dashed=GALACTIC_ECLIPTIC_DASH_PATTERN, poles=False)
#     m.draw_galactic(tickinterval=10, dashed=GALACTIC_ECLIPTIC_DASH_PATTERN, poles=True)
#
#     # Legend
#     legend(f, chart_number)
#     f.render(os.path.join(OUTPUT_FOLDER, "{:02}.pdf".format(chart_number)), open=False)
#
#     # North conic maps
#     for i in range(6):
#         chart_number = i + 2
#         center_longitude = 30 + i * 60
#         fn = "{:02}".format(chart_number)
#         f = figure(fn)
#
#         m = EquidistantConicMapArea(
#             MAP_LLCORNER,
#             MAP_URCORNER,
#             hmargin=MAP_HMARGIN,
#             vmargin=MAP_VMARGIN,
#             center=(center_longitude, 45),
#             standard_parallel1=30,
#             standard_parallel2=60,
#             latitude_range=LATITUDE_RANGE,
#             celestial=True,
#         )
#         f.add(m)
#
#         m.gridline_factory.parallel_marked_tick_interval = 5
#         m.gridline_factory.rotate_parallel_labels = True
#         m.gridline_factory.parallel_fontsize = "tiny"
#         m.draw_meridians()
#         m.draw_parallels()
#         m.draw_internal_parallel_ticks(center_longitude)
#         with m.clip(m.clipping_path):
#             m.draw_constellations()
#         m.draw_ecliptic(
#             tickinterval=10, dashed=GALACTIC_ECLIPTIC_DASH_PATTERN, poles=False
#         )
#         m.draw_galactic(
#             tickinterval=10, dashed=GALACTIC_ECLIPTIC_DASH_PATTERN, poles=True
#         )
#
#         # Legend
#         legend(f, chart_number)
#         f.render(
#             os.path.join(OUTPUT_FOLDER, "{:02}.pdf".format(chart_number)), open=False
#         )
#
#     # Equatorial maps
#     for i in range(6):
#         chart_number = i + 8
#         center_longitude = 30 + i * 60
#         fn = "{:02}".format(chart_number)
#         f = figure(fn)
#         m = EquidistantCylindricalMapArea(
#             MAP_LLCORNER,
#             MAP_URCORNER,
#             hmargin=MAP_HMARGIN,
#             vmargin=MAP_VMARGIN,
#             center_longitude=center_longitude,
#             standard_parallel=20,
#             latitude_range=LATITUDE_RANGE,
#             lateral_scale=0.958_695,
#             celestial=True,
#         )
#         f.add(m)
#
#         m.gridline_factory.parallel_marked_tick_interval = 5
#         m.gridline_factory.parallel_fontsize = "tiny"
#         m.draw_meridians()
#         m.draw_parallels()
#         m.draw_ecliptic()
#         with m.clip(m.clipping_path):
#             m.draw_constellations()
#         m.draw_ecliptic(
#             tickinterval=10, dashed=GALACTIC_ECLIPTIC_DASH_PATTERN, poles=False
#         )
#         m.draw_galactic(
#             tickinterval=10, dashed=GALACTIC_ECLIPTIC_DASH_PATTERN, poles=True
#         )
#
#         # Legend
#         legend(f, chart_number)
#         f.render(
#             os.path.join(OUTPUT_FOLDER, "{:02}.pdf".format(chart_number)), open=False
#         )
#
#     # South conic maps
#     for i in range(6):
#         chart_number = i + 14
#         center_longitude = 30 + i * 60
#         fn = "{:02}".format(chart_number)
#         f = figure(fn)
#         m = EquidistantConicMapArea(
#             MAP_LLCORNER,
#             MAP_URCORNER,
#             hmargin=MAP_HMARGIN,
#             vmargin=MAP_VMARGIN,
#             center=(center_longitude, -45),
#             standard_parallel1=-60,
#             standard_parallel2=-30,
#             latitude_range=LATITUDE_RANGE,
#             celestial=True,
#         )
#         f.add(m)
#         m.gridline_factory.parallel_marked_tick_interval = 5
#         m.gridline_factory.parallel_fontsize = "tiny"
#         m.gridline_factory.rotate_parallel_labels = True
#         m.draw_meridians()
#         m.draw_parallels()
#         m.draw_internal_parallel_ticks(center_longitude)
#         with m.clip(m.clipping_path):
#             m.draw_constellations()
#         m.draw_ecliptic(
#             tickinterval=10, dashed=GALACTIC_ECLIPTIC_DASH_PATTERN, poles=False
#         )
#         m.draw_galactic(
#             tickinterval=10, dashed=GALACTIC_ECLIPTIC_DASH_PATTERN, poles=True
#         )
#
#         # Legend
#         legend(f, chart_number)
#         f.render(
#             os.path.join(OUTPUT_FOLDER, "{:02}.pdf".format(chart_number)), open=False
#         )
#
#     # South pole
#     chart_number = 20
#     fn = "{:02}".format(chart_number)
#     f = figure(fn)
#     m = AzimuthalEquidistantMapArea(
#         MAP_LLCORNER,
#         MAP_URCORNER,
#         hmargin=MAP_HMARGIN,
#         vmargin=MAP_VMARGIN,
#         latitude_range=LATITUDE_RANGE,
#         celestial=True,
#         north=False,
#     )
#     f.add(m)
#     m.draw_meridians(origin_offsets=AZIMUTHAL_MERIDIAN_OFFSETS)
#     m.draw_parallels()
#     m.draw_internal_parallel_ticks(0, labels=True)
#     with m.clip(m.clipping_path):
#         m.draw_constellations()
#     m.draw_ecliptic(tickinterval=10, dashed=GALACTIC_ECLIPTIC_DASH_PATTERN, poles=False)
#     m.draw_galactic(tickinterval=10, dashed=GALACTIC_ECLIPTIC_DASH_PATTERN, poles=True)
#
#     # Legend
#     legend(f, chart_number)
#     f.render(os.path.join(OUTPUT_FOLDER, "{:02}.pdf".format(chart_number)), open=False)
