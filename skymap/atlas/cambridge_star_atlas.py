from skymap.tikz import Tikz, PaperMargin, PaperSize
from skymap.map import MapLegend, MapArea, MapBorders, EquidistantConicProjection
from skymap.geometry import Point, Line, Label, SkyCoordDeg

# OUTPUT_FOLDER = os.path.join(BASEDIR, "cambridge_star_atlas")


LATITUDE_RANGE = 56
AZIMUTHAL_MERIDIAN_OFFSETS = {15: 10, 45: 1, 90: 0}
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


class CambridgeStarAtlasMap(MapArea):
    def __init__(self, tikz, chart_number):
        # Determine these using the chart number
        p1 = tikz.llcorner
        p2 = tikz.urcorner - Point(LEGEND_WIDTH, 0)
        center_longitude = 210
        center_latitude = 45
        borders = MapBorders(True, True, 6, 5)
        reference_scale = 56 / (p2.y - p1.y - 2 * borders.vmargin)
        projection = EquidistantConicProjection(
            center=SkyCoordDeg(center_longitude, center_latitude),
            standard_parallel1=30,
            standard_parallel2=60,
            reference_scale=reference_scale,
            celestial=True,
        )

        MapArea.__init__(
            self,
            tikz,
            p1,
            p2,
            borders,
            projection,
            center_longitude,
            center_latitude,
            None,
            None,
        )


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
