import sys
import os
from skymap.tikz import BASEDIR, TikzFigure, DrawingArea
from skymap.map import EquidistantCylindricalMapArea, AzimuthalEquidistantMapArea, EquidistantConicMapArea
from skymap.geometry import Point, Line, SphericalPoint
from skymap.gridlines import Label


OUTPUT_FOLDER = os.path.join(BASEDIR, "skyatlas2000")

PAPERSIZE = (465, 343)
LEFT_MARGIN = 17
RIGHT_MARGIN = 17
BOTTOM_MARGIN = 8
TOP_MARGIN = 10
MAP_HMARGIN = 7
MAP_VMARGIN = 7

MAP_LLCORNER = Point(LEFT_MARGIN, BOTTOM_MARGIN)
MAP_URCORNER = Point(PAPERSIZE[0]-RIGHT_MARGIN, BOTTOM_MARGIN + 299)

LATITUDE_RANGE = 40
CONIC_MERIDIAN_OFFSETS = {15: 10, 30: 2}


if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)


def figure(fn):
    return TikzFigure(fn, papersize=PAPERSIZE,
                      left_margin=LEFT_MARGIN, right_margin=RIGHT_MARGIN,
                      bottom_margin=BOTTOM_MARGIN, top_margin=TOP_MARGIN,
                      fontsize=10)


def legend(figure, chart_number):
    p1 = figure.ulcorner + Point(0, -22)
    p2 = figure.ulcorner + Point(23, 0)
    l = DrawingArea(p1, p2, p1)
    figure.add(l)

    p1 = figure.ulcorner + Point(25, -22)
    p2 = figure.urcorner + Point(-25, 0)
    l = DrawingArea(p1, p2, p1)
    figure.add(l)

    p1 = figure.urcorner + Point(-23, -22)
    p2 = figure.urcorner
    l = DrawingArea(p1, p2, p1)
    figure.add(l)
    p = Point(11.5, 16)
    l.draw_label(Label(p, "CHART NUMBER", 90, "footnotesize"))
    p = Point(11.4, 0)
    l.draw_label(Label(p, "\\textbf{{{}}}".format(chart_number), 90, "HUGE"))

if __name__ == "__main__":
    # North pole
    for i in range(3):
        center_longitude = 90 + 0.8485 + i * 120
        chart_number = i + 1
        fn = "{:02}".format(chart_number)
        f = figure(fn)
        center_latitude = 70
        map_origin = Point(MAP_LLCORNER.x + MAP_HMARGIN + 132, 0.5 * (MAP_LLCORNER.y + MAP_URCORNER.y) + 0.01)
        m = EquidistantConicMapArea(MAP_LLCORNER, MAP_URCORNER, hmargin=MAP_HMARGIN, vmargin=MAP_VMARGIN, origin=map_origin, center=(center_longitude, center_latitude), standard_parallel1=55, standard_parallel2=90, latitude_range=LATITUDE_RANGE, celestial=True)
        f.add(m)

        m.gridline_factory.parallel_fontsize = "tiny"

        # Set the ticks on the correct axes
        m.meridian_ticks['left'] = True
        m.meridian_ticks['right'] = True
        m.meridian_ticks['bottom'] = True
        m.meridian_ticks['top'] = False
        m.parallel_ticks['left'] = False
        m.parallel_ticks['right'] = False
        m.parallel_ticks['bottom'] = False
        m.parallel_ticks['top'] = True
        m.rotate_parallel_labels = False

        # Draw the grid
        m.draw_meridians(origin_offsets=CONIC_MERIDIAN_OFFSETS)
        m.draw_parallels()

        # Draw the +90 degrees parallel tick
        p1 = Point(0, 0.5*(MAP_URCORNER.y - MAP_LLCORNER.y - 2*MAP_VMARGIN))
        p2 = p1 + Point(0, m.gridline_factory.marked_ticksize)
        p3 = p1 + Point(0, m.gridline_factory.label_distance)
        m.draw_line(Line(p1, p2), linewidth=m.gridline_thickness)
        m.draw_label(Label(p3, "+90\\textdegree", 90, "tiny"))

        with m.clip(m.clipping_path):
            m.draw_constellations()

        # Legend
        legend(f, chart_number)
        f.render(os.path.join(OUTPUT_FOLDER, "{:02}.pdf".format(chart_number)), open=False)

    # North conic maps
    for i in range(6):
        center_longitude = 30 + i * 60
        chart_number = i + 4
        fn = "{:02}".format(chart_number)
        f = figure(fn)
        m = EquidistantConicMapArea(MAP_LLCORNER, MAP_URCORNER, hmargin=MAP_HMARGIN, vmargin=MAP_VMARGIN,
                                    center=(center_longitude, 37), standard_parallel1=25, standard_parallel2=47,
                                    latitude_range=LATITUDE_RANGE, celestial=True)
        f.add(m)
        m.gridline_factory.parallel_marked_tick_interval = 5
        m.gridline_factory.parallel_fontsize = "tiny"
        m.gridline_factory.rotate_parallel_labels = True
        m.draw_meridians()
        m.draw_parallels()
        with m.clip(m.clipping_path):
            m.draw_constellations()

        # Legend
        legend(f, chart_number)
        f.render(os.path.join(OUTPUT_FOLDER, "{:02}.pdf".format(chart_number)), open=False)

    # Equatorial maps
    for i in range(8):
        chart_number = i + 10
        center_longitude = 30 + i * 45
        fn = "{:02}".format(chart_number)
        f = figure(fn)
        m = EquidistantCylindricalMapArea(MAP_LLCORNER, MAP_URCORNER, hmargin=MAP_HMARGIN, vmargin=MAP_VMARGIN,
                                          center_longitude=center_longitude, standard_parallel=14,
                                          latitude_range=LATITUDE_RANGE, lateral_scale=0.9754, celestial=True)
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
        center_longitude = 30 + i * 60
        chart_number = i + 18
        fn = "{:02}".format(chart_number)
        f = figure(fn)
        m = EquidistantConicMapArea(MAP_LLCORNER, MAP_URCORNER, hmargin=MAP_HMARGIN, vmargin=MAP_VMARGIN,
                                    center=(center_longitude, -37), standard_parallel1=-47, standard_parallel2=-25,
                                    latitude_range=LATITUDE_RANGE, celestial=True)
        f.add(m)
        m.gridline_factory.parallel_marked_tick_interval = 5
        m.gridline_factory.rotate_parallel_labels = True
        m.gridline_factory.parallel_fontsize = "tiny"
        m.draw_meridians()
        m.draw_parallels()
        with m.clip(m.clipping_path):
            m.draw_constellations()

        # Legend
        legend(f, chart_number)
        f.render(os.path.join(OUTPUT_FOLDER, "{:02}.pdf".format(chart_number)), open=False)

    # South pole
    for i in range(3):
        center_longitude = 30 - 0.8485 + i * 120
        chart_number = i + 24
        fn = "{:02}".format(chart_number)
        f = figure(fn)
        center_latitude = -70
        map_origin = Point(MAP_URCORNER.x - MAP_HMARGIN - 132, 0.5 * (MAP_LLCORNER.y + MAP_URCORNER.y) - 0.01)
        m = EquidistantConicMapArea(MAP_LLCORNER, MAP_URCORNER, hmargin=MAP_HMARGIN, vmargin=MAP_VMARGIN, origin=map_origin, center=(center_longitude, center_latitude), standard_parallel1=-90, standard_parallel2=-55, latitude_range=LATITUDE_RANGE, celestial=True)
        f.add(m)

        m.gridline_factory.parallel_fontsize = "tiny"
        # Set the ticks on the correct axes
        m.meridian_ticks['left'] = True
        m.meridian_ticks['right'] = True
        m.meridian_ticks['bottom'] = False
        m.meridian_ticks['top'] = True
        m.parallel_ticks['left'] = False
        m.parallel_ticks['right'] = False
        m.parallel_ticks['bottom'] = True
        m.parallel_ticks['top'] = False
        m.rotate_parallel_labels = False

        # Draw the grid
        m.draw_meridians(origin_offsets=CONIC_MERIDIAN_OFFSETS)
        m.draw_parallels()

        m.fill_circle(map_origin, 2)
        # Draw the -90 degrees parallel tick
        p1 = Point(0, -0.5*(MAP_URCORNER.y - MAP_LLCORNER.y - 2*MAP_VMARGIN))
        p2 = p1 + Point(0, -m.gridline_factory.marked_ticksize)
        p3 = p1 + Point(0, -m.gridline_factory.label_distance)
        m.draw_line(Line(p1, p2), linewidth=m.gridline_thickness)
        m.draw_label(Label(p3, "--90\\textdegree", 270, "tiny"))

        with m.clip(m.clipping_path):
            m.draw_constellations()

        # Legend
        legend(f, chart_number)
        f.render(os.path.join(OUTPUT_FOLDER, "{:02}.pdf".format(chart_number)), open=False)