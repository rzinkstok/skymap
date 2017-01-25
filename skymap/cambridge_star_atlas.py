import sys
import os
from skymap.tikz import BASEDIR, TikzFigure, DrawingArea
from skymap.map import EquidistantCylindricalMapArea, AzimuthalEquidistantMapArea, EquidistantConicMapArea
from skymap.geometry import Point, Line
from skymap.gridlines import Label


OUTPUT_FOLDER = os.path.join(BASEDIR, "cambridge_star_atlas")

PAPERSIZE = (304, 228)
LEFT_MARGIN = 12
RIGHT_MARGIN = 12
BOTTOM_MARGIN = 14
TOP_MARGIN = 20
MAP_HMARGIN = 6
MAP_VMARGIN = 5

MAP_LLCORNER = Point(LEFT_MARGIN, BOTTOM_MARGIN)
MAP_URCORNER = Point(LEFT_MARGIN + 264, PAPERSIZE[1] - TOP_MARGIN)

LATITUDE_RANGE = 56
AZIMUTHAL_MERIDIAN_OFFSETS = {15: 10, 45: 1, 90: 0}


if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)


def figure(fn):
    return TikzFigure(fn, papersize=PAPERSIZE,
                      left_margin=LEFT_MARGIN, right_margin=RIGHT_MARGIN,
                      bottom_margin=BOTTOM_MARGIN, top_margin=TOP_MARGIN,
                      fontsize=10)


def legend(figure, chart_number):
    l = DrawingArea(f.llcorner + Point(264, 0), f.urcorner, f.llcorner + Point(264, 0))
    figure.add(l)
    l.draw_label(Label(Point(8, 189), "Epoch", 90, "tiny"))
    l.draw_label(Label(Point(8, 185), "\\textbf{2000.0}", 90, "normalsize"))
    l.draw_line(Line(Point(2, 183.5), Point(14, 183.5)))
    l.draw_line(Line(Point(2, 15), Point(14, 15)))
    l.draw_label(Label(Point(8, 11), "Chart number", 90, "tiny"))
    l.draw_label(Label(Point(8, 2), "\\textbf{{{}}}".format(chart_number), 90, "Huge"))


if __name__ == "__main__":
    # North pole
    chart_number = 1
    fn = "{:02}".format(chart_number)
    f = figure(fn)
    m = AzimuthalEquidistantMapArea(MAP_LLCORNER, MAP_URCORNER, latitude_range=LATITUDE_RANGE, hmargin=MAP_HMARGIN, vmargin=MAP_VMARGIN, celestial=True, north=True)
    f.add(m)
    #m.draw_parallel_ticks_on_reference_meridian = True
    m.draw_meridians(origin_offsets=AZIMUTHAL_MERIDIAN_OFFSETS)
    m.draw_parallels()
    m.draw_internal_parallel_ticks(0, labels=True)
    with m.clip(m.clipping_path):
        m.draw_constellations()

    # Legend
    legend(f, chart_number)
    f.render(os.path.join(OUTPUT_FOLDER, "{:02}.pdf".format(chart_number)), open=False)

    # North conic maps
    for i in range(6):
        chart_number = i+2
        center_longitude = 30 + i * 60
        fn = "{:02}".format(chart_number)
        f = figure(fn)
        m = EquidistantConicMapArea(MAP_LLCORNER, MAP_URCORNER, hmargin=MAP_HMARGIN, vmargin=MAP_VMARGIN, center=(center_longitude, 45), standard_parallel1=30, standard_parallel2=60, latitude_range=LATITUDE_RANGE, celestial=True)
        f.add(m)
        m.gridline_factory.parallel_marked_tick_interval = 5
        m.gridline_factory.rotate_parallel_labels = True
        m.gridline_factory.parallel_fontsize = "tiny"
        m.draw_meridians()
        m.draw_parallels()
        m.draw_internal_parallel_ticks(center_longitude)
        with m.clip(m.clipping_path):
            m.draw_constellations()

        # Legend
        legend(f, chart_number)
        f.render(os.path.join(OUTPUT_FOLDER, "{:02}.pdf".format(chart_number)), open=False)

    # Equatorial maps
    for i in range(6):
        chart_number = i+8
        center_longitude = 30 + i * 60
        fn = "{:02}".format(chart_number)
        f = figure(fn)
        m = EquidistantCylindricalMapArea(MAP_LLCORNER, MAP_URCORNER, hmargin=MAP_HMARGIN, vmargin=MAP_VMARGIN, center_longitude=center_longitude, standard_parallel=20, latitude_range=LATITUDE_RANGE, celestial=True)
        f.add(m)
        m.gridline_factory.parallel_marked_tick_interval = 5
        m.gridline_factory.parallel_fontsize = "tiny"
        m.draw_meridians()
        m.draw_parallels()
        with m.clip(m.clipping_path):
            m.draw_constellations()

        # Legend
        legend(f, chart_number)
        f.render(os.path.join(OUTPUT_FOLDER, "{:02}.pdf".format(chart_number)), open=False)

    # South conic maps
    for i in range(6):
        chart_number = i+14
        center_longitude = 30 + i * 60
        fn = "{:02}".format(chart_number)
        f = figure(fn)
        m = EquidistantConicMapArea(MAP_LLCORNER, MAP_URCORNER, hmargin=MAP_HMARGIN, vmargin=MAP_VMARGIN, center=(center_longitude, -45), standard_parallel1=-60, standard_parallel2=-30, latitude_range=LATITUDE_RANGE, celestial=True)
        f.add(m)
        m.gridline_factory.parallel_marked_tick_interval = 5
        m.gridline_factory.parallel_fontsize = "tiny"
        m.gridline_factory.rotate_parallel_labels = True
        m.draw_meridians()
        m.draw_parallels()
        m.draw_internal_parallel_ticks(center_longitude)
        with m.clip(m.clipping_path):
            m.draw_constellations()

        # Legend
        legend(f, chart_number)
        f.render(os.path.join(OUTPUT_FOLDER, "{:02}.pdf".format(chart_number)), open=False)

    # South pole
    chart_number = 20
    fn = "{:02}".format(chart_number)
    f = figure(fn)
    m = AzimuthalEquidistantMapArea(MAP_LLCORNER, MAP_URCORNER, latitude_range=LATITUDE_RANGE, hmargin=MAP_HMARGIN, vmargin=MAP_VMARGIN, celestial=True, north=False)
    f.add(m)
    m.draw_meridians(origin_offsets=AZIMUTHAL_MERIDIAN_OFFSETS)
    m.draw_parallels()
    m.draw_internal_parallel_ticks(0, labels=True)
    with m.clip(m.clipping_path):
        m.draw_constellations()

    # Legend
    legend(f, chart_number)
    f.render(os.path.join(OUTPUT_FOLDER, "{:02}.pdf".format(chart_number)), open=False)
