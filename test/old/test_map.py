import unittest
import os
from skymap.geometry import Point, HourAngle, Line
from skymap.map import EquidistantConicMapArea, DrawingArea
from skymap.projections import UnitProjection
from skymap.tikz import TikzFigure, BASEDIR
from skymap.gridlines import GridLineLabel
from skymap.constellations import constellations_in_area


OUTPUT_FOLDER = os.path.join(BASEDIR, "test")

PAPERSIZE = (226, 304)
LEGEND_WIDTH = 197
LEGEND_HEIGHT = 14
EDGE_MARGIN = 11
SPINE_MARGIN = PAPERSIZE[0] - LEGEND_WIDTH - EDGE_MARGIN
BOTTOM_MARGIN = 11

TOP_MARGIN = 22
MAP_HMARGIN = 0
MAP_VMARGIN = 0


LMAP_LLCORNER = Point(EDGE_MARGIN, BOTTOM_MARGIN)
LMAP_URCORNER = Point(PAPERSIZE[0] - SPINE_MARGIN, PAPERSIZE[1] - TOP_MARGIN)

RMAP_LLCORNER = Point(SPINE_MARGIN, BOTTOM_MARGIN)
RMAP_URCORNER = Point(PAPERSIZE[0] - SPINE_MARGIN, PAPERSIZE[1] - TOP_MARGIN)

AZIMUTHAL_OFFSETS = {15: 2, 30: 1, 90: 0}

MM_PER_DEGREE = 18.5
ECLIPTIC_DASH_PATTERN = 'densely dashed'
GALACTIC_DASH_PATTERN = 'densely dash dot'
ECLIPTIC_LINEWIDTH = 0.35
GALACTIC_LINEWIDTH = 0.35


def meridian_label(longitude):
    h = HourAngle()
    h.from_degrees(longitude)
    return "{:02}\\raisebox{{0.3em}}{{\\tiny h}}{:02}\\raisebox{{0.3em}}{{\\tiny m}}".format(h.hours, h.minutes)


def rightlegend(figure, chart_number, min_longitude, max_longitude, min_latitude, max_latitude):
    # Lower legend box
    p1 = figure.llcorner
    p2 = figure.llcorner + Point(LEGEND_WIDTH, LEGEND_HEIGHT)
    l = DrawingArea(p1, p2, p1, box=False)
    figure.add(l)
    l.draw_bounding_box(0.4)

    # Long/lat ranges
    l.draw_line(Line(Point(138, 1.5), Point(138, LEGEND_HEIGHT - 1.5)))

    minha = HourAngle()
    minha.from_degrees(min_longitude)
    maxha = HourAngle()
    maxha.from_degrees(max_longitude)
    longlabel = "\\condensed\\textbf{{{:02}\\raisebox{{0.35em}}{{\\footnotesize h}}{:02}\\raisebox{{0.35em}}{{\\footnotesize m}} to {:02}\\raisebox{{0.35em}}{{\\small h}}{:02}\\raisebox{{0.35em}}{{\\small m}}}}".format(minha.hours, minha.minutes, maxha.hours, maxha.minutes)
    l.draw_label(GridLineLabel(Point(158, 6.75), longlabel, 90, "LARGE"))

    latlabel = "\\condensed\\textbf{{"
    if min_latitude >= 0:
        latlabel += "+{:02}".format(min_latitude)
    else:
        latlabel += "--{:02}".format(abs(min_latitude))
    latlabel += "\\textdegree{{}} to "
    if max_latitude >= 0:
        latlabel += "+{:02}".format(max_latitude)
    else:
        latlabel += "--{:02}".format(abs(max_latitude))
    latlabel += "\\textdegree}}"
    l.draw_label(GridLineLabel(Point(158, 1), latlabel, 90, "LARGE"))

    # Constellations
    l.draw_line(Line(Point(178, 1.5), Point(178, LEGEND_HEIGHT-1.5)))

    constellations = constellations_in_area(min_longitude, max_longitude, min_latitude, max_latitude, nsamples=10000)
    l.draw_label(GridLineLabel(Point(187.5, 5.0), "\\condensed\\textbf{{{}}}".format(constellations[0].upper()), 90, "LARGE"))
    if len(constellations) > 1:
        l.draw_label(GridLineLabel(Point(187.5, 1.5), "\\condensed\\textbf{{{}}}".format(", ".join(constellations[1:4]).upper()), 90, "small"))


    # Chart number
    p1 = figure.urcorner + Point(-EDGE_MARGIN, TOP_MARGIN - 17)
    p2 = p1 + Point(2 * EDGE_MARGIN, 17)
    l = DrawingArea(p1, p2, box=False)
    figure.add(l)
    l.draw_label(GridLineLabel(Point(EDGE_MARGIN, -1.5), "\\textbf{{{}}}".format(chart_number), 90, "huge"))

    # Thumb index
    # p1 = figure.urcorner + Point(EDGE_MARGIN - 10, TOP_MARGIN - 137 - 17)
    # p2 = p1 + Point(10, 17)
    # l = DrawingArea(p1, p2, box=False)
    # figure.add(l)
    # if max_latitude >= 0:
    #     maxlatlabel = "+{:02}\\textdegree".format(max_latitude)
    # else:
    #     maxlatlabel = "--{:02}\\textdegree".format(abs(max_latitude))
    # if min_latitude >= 0:
    #     minlatlabel = "+{:02}\\textdegree".format(min_latitude)
    # else:
    #     minlatlabel = "--{:02}\\textdegree".format(abs(min_latitude))
    # l.fill_rectangle(Rectangle(Point(0, 0), Point(10, 17)), "black")
    # l.draw_label(Label(Point(5, 0.3), "\\condensed\\textbf{{{}}}".format(minlatlabel), 90, "large", color="white"))
    # l.draw_label(Label(Point(5, 11.6), "\\condensed\\textbf{{{}}}".format(maxlatlabel), 90, "large", color="white"))



class MapTest(unittest.TestCase):
    def setUp(self):
        self.m = Map(UnitProjection(), (297.0, 210.0), 20, 20)

    def test_to_map_coordinates(self):
        dx = float(297 - 40) / (210 - 40)
        self.assertEqual(self.m.map_point(Point(0, 0)), Point(148.5, 105.0))
        self.assertEqual(self.m.map_point(Point(dx, 1)), Point(277, 190))
        self.assertEqual(self.m.map_point(Point(-dx, 1)), Point(20, 190))
        self.assertEqual(self.m.map_point(Point(-dx, -1)), Point(20, 20))
        self.assertEqual(self.m.map_point(Point(dx, -1)), Point(277, 20))

    def test_inside_viewport(self):
        self.assertTrue(self.m.inside_viewport(Point(100, 100)))
        self.assertFalse(self.m.inside_viewport(Point(100, 250)))


class UranometriaTest(unittest.TestCase):
    def test_map(self):
        conic = {
                "min_latitude": 51,
                "max_latitude": 63,
                "longitude_range": 16,
                "longitude_step": -30,
                "meridian_interval": 2,
                "offset": 14
            }

        center_longitude = 210
        chart_number = 23
        delta = None

        # Left page
        chart_side = 'right'
        min_longitude  = center_longitude - conic['longitude_range']
        max_longitude = center_longitude
        min_latitude = conic['min_latitude']
        max_latitude = conic['max_latitude']
        meridian_interval = conic['meridian_interval']
        offset = conic['offset']

        latitude_range = max_latitude - min_latitude
        center_latitude = min_latitude + 0.5 * latitude_range

        if delta is not None:
            offset += delta

        fn = "{:02}B".format(chart_number)
        f = TikzFigure(fn, papersize=PAPERSIZE,
                              left_margin=SPINE_MARGIN, right_margin=EDGE_MARGIN,
                              bottom_margin=BOTTOM_MARGIN, top_margin=TOP_MARGIN,
                              fontsize=10)
        map_llcorner = RMAP_LLCORNER + Point(0, LEGEND_HEIGHT + offset)
        map_urcorner = map_llcorner + Point(LEGEND_WIDTH, latitude_range * MM_PER_DEGREE)
        center_longitude = max_longitude
        map_origin = map_llcorner + Point(0, 0.5 * latitude_range * MM_PER_DEGREE)

        sp1 = min_latitude + int(round(latitude_range / 6.0))
        sp2 = min_latitude + int(round(5.0 * latitude_range / 6.0))
        m = EquidistantConicMapArea(map_llcorner, map_urcorner, hmargin=MAP_HMARGIN, vmargin=MAP_VMARGIN,
                                        center=(center_longitude, center_latitude), standard_parallel1=sp1, standard_parallel2=sp2,
                                        latitude_range=latitude_range, origin=map_origin, celestial=True, box=False)

        f.add(m)

        m.bordered = True #False

        m.gridline_factory.meridian_line_interval = meridian_interval
        m.gridline_factory.meridian_marked_tick_interval = meridian_interval
        m.gridline_factory.meridian_tick_interval = meridian_interval
        m.gridline_factory.parallel_line_interval = 1
        m.gridline_factory.parallel_marked_tick_interval = 1
        m.gridline_factory.parallel_tick_interval = 1

        m.gridline_factory.marked_ticksize = 0
        m.gridline_factory.unmarked_ticksize = 0
        m.gridline_factory.fixed_tick_reach = False

        m.gridline_factory.label_distance = 1

        m.gridline_factory.rotate_parallel_labels = True

        m.gridline_factory.rotate_meridian_labels = True
        m.gridline_factory.meridian_labeltextfunc = meridian_label
        m.gridline_factory.rotate_poles = True
        m.gridline_factory.pole_marker_size = 1

        m.min_longitude = min_longitude
        m.max_longitude = max_longitude
        m.min_latitude = min_latitude
        m.max_latitude = max_latitude

        m.draw_meridians()
        m.draw_parallels()
        with m.clip(m.clipping_path):
            m.draw_constellations(linewidth=0.3)
            m.draw_ecliptic(linewidth=ECLIPTIC_LINEWIDTH, tickinterval=1, dashed=ECLIPTIC_DASH_PATTERN, poles=True)
            m.draw_galactic(linewidth=GALACTIC_LINEWIDTH, tickinterval=1, dashed=GALACTIC_DASH_PATTERN, poles=True)

        # Legend
        rightlegend(f, chart_number, center_longitude - conic['longitude_range'],
                    center_longitude + conic['longitude_range'], conic['min_latitude'], conic['max_latitude'])
        f.render(os.path.join(OUTPUT_FOLDER, "{:02}B.pdf".format(chart_number)), open=False)
        print "Map ready"