import sys
import os
from skymap.tikz import BASEDIR, TikzFigure, DrawingArea
from skymap.map import EquidistantCylindricalMapArea, AzimuthalEquidistantMapArea, EquidistantConicMapArea
from skymap.geometry import Point, Line, SphericalPoint, HourAngle, Rectangle
from skymap.gridlines import Label
from skymap.constellations import constellations_in_area


OUTPUT_FOLDER = os.path.join(BASEDIR, "uranometria")

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

CONICS = [
    {
        "min_latitude": 73,
        "max_latitude": 85,
        "longitude_range": 35,
        "longitude_step": -60,
        "meridian_interval": 5,
        "offset": 14
    },
    {
        "min_latitude": 62,
        "max_latitude": 74,
        "longitude_range": 20,
        "longitude_step": -36,
        "meridian_interval": 2,
        "offset": 14
    },
    {
        "min_latitude": 51,
        "max_latitude": 63,
        "longitude_range": 16,
        "longitude_step": -30,
        "meridian_interval": 2,
        "offset": 14
    },
    {
        "min_latitude": 40,
        "max_latitude": 52,
        "longitude_range": 13,
        "longitude_step": -24,
        "meridian_interval": 1,
        "offset": 16
    },
    {
        "min_latitude": 29,
        "max_latitude": 41,
        "longitude_range": 11,
        "longitude_step": -20,
        "meridian_interval": 1,
        "offset": 18
    },
    {
        "min_latitude": 17,
        "max_latitude": 30,
        "longitude_range": 11,
        "longitude_step": -20,
        "meridian_interval": 1,
        "offset": 10
    },
    {
        "min_latitude": 5,
        "max_latitude": 18,
        "longitude_range": 10,
        "longitude_step": -18,
        "meridian_interval": 1,
        "offset": 12
    },
]


if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)


def azimuthal_meridian_label(longitude):
    h = HourAngle()
    h.from_degrees(longitude)
    return "{:02}\\raisebox{{0.3em}}{{\\tiny h}}".format(h.hours)


def meridian_label(longitude):
    h = HourAngle()
    h.from_degrees(longitude)
    return "{:02}\\raisebox{{0.3em}}{{\\tiny h}}{:02}\\raisebox{{0.3em}}{{\\tiny m}}".format(h.hours, h.minutes)


# Full page figures
def leftfigure(fn):
    return TikzFigure(fn, papersize=PAPERSIZE,
                      left_margin=EDGE_MARGIN, right_margin=SPINE_MARGIN,
                      bottom_margin=BOTTOM_MARGIN, top_margin=TOP_MARGIN,
                      fontsize=10)


def rightfigure(fn):
    return TikzFigure(fn, papersize=PAPERSIZE,
                      left_margin=SPINE_MARGIN, right_margin=EDGE_MARGIN,
                      bottom_margin=BOTTOM_MARGIN, top_margin=TOP_MARGIN,
                      fontsize=10)


# Bottom legends
def leftlegend(figure, chart_number):
    p1 = figure.llcorner
    p2 = figure.llcorner + Point(LEGEND_WIDTH, LEGEND_HEIGHT)
    l = DrawingArea(p1, p2, p1, box=False)
    figure.add(l)
    l.draw_bounding_box(0.4)

    p1 = figure.llcorner + Point(-EDGE_MARGIN, PAPERSIZE[1] - BOTTOM_MARGIN - 17)
    p2 = figure.llcorner + Point(EDGE_MARGIN, PAPERSIZE[1] - BOTTOM_MARGIN)
    l = DrawingArea(p1, p2, box=False)
    figure.add(l)
    l.draw_label(Label(Point(EDGE_MARGIN, -1.5), "\\textbf{{{}}}".format(chart_number), 90, "huge"))


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
    l.draw_label(Label(Point(158, 6.75), longlabel, 90, "LARGE"))

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
    l.draw_label(Label(Point(158, 1), latlabel, 90, "LARGE"))

    # Constellations
    l.draw_line(Line(Point(178, 1.5), Point(178, LEGEND_HEIGHT-1.5)))

    constellations = constellations_in_area(min_longitude, max_longitude, min_latitude, max_latitude, nsamples=10000)
    l.draw_label(Label(Point(187.5, 5.0), "\\condensed\\textbf{{{}}}".format(constellations[0].upper()), 90, "LARGE"))
    if len(constellations) > 1:
        l.draw_label(Label(Point(187.5, 1.5), "\\condensed\\textbf{{{}}}".format(", ".join(constellations[1:4]).upper()), 90, "small"))


    # Chart number
    p1 = figure.urcorner + Point(-EDGE_MARGIN, TOP_MARGIN - 17)
    p2 = p1 + Point(2 * EDGE_MARGIN, 17)
    l = DrawingArea(p1, p2, box=False)
    figure.add(l)
    l.draw_label(Label(Point(EDGE_MARGIN, -1.5), "\\textbf{{{}}}".format(chart_number), 90, "huge"))

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


# Azimuthal map areas
def azimuthal_map(chart_number, chart_side, north, delta=None):
    offset = 23
    latitude_range = 12
    if north:
        reference_longitude = 270
    else:
        reference_longitude = 90

    if delta is not None:
        origin_x = 5 * MM_PER_DEGREE + delta
    else:
        origin_x = 5 * MM_PER_DEGREE

    if chart_side == 'left':
        fn = "{:02}A".format(chart_number)
        f = leftfigure(fn)
        map_llcorner = LMAP_LLCORNER + Point(7, LEGEND_HEIGHT + offset)
        map_urcorner = map_llcorner + Point(10 * MM_PER_DEGREE, latitude_range * MM_PER_DEGREE)
        map_origin = map_llcorner + Point(origin_x, 0.5 * latitude_range * MM_PER_DEGREE)
    else:
        fn = "{:02}B".format(chart_number)
        f = rightfigure(fn)
        map_lrcorner = RMAP_LLCORNER + Point(LEGEND_WIDTH - 7, 0) + Point(0, LEGEND_HEIGHT + offset)
        map_llcorner = map_lrcorner + Point(-10 * MM_PER_DEGREE, 0)
        map_urcorner = map_lrcorner + Point(0, latitude_range * MM_PER_DEGREE)
        map_origin = map_lrcorner + Point(-origin_x, 0.5 * latitude_range * MM_PER_DEGREE)

    m = AzimuthalEquidistantMapArea(map_llcorner, map_urcorner, hmargin=MAP_HMARGIN, vmargin=MAP_VMARGIN,
                                    origin=map_origin, north=north,
                                    reference_longitude=reference_longitude, latitude_range=latitude_range,
                                    celestial=True, box=False)

    if delta is None:
        if chart_side == "left":
            if north:
                p1 = m.projection(SphericalPoint(90, 84))
            else:
                p1 = m.projection(SphericalPoint(270, -84))
            delta = map_llcorner.x - (map_origin.x + p1.x)
        else:
            if north:
                p1 = m.projection(SphericalPoint(270, 84))
            else:
                p1 = m.projection(SphericalPoint(90, -84))
            delta = -(map_lrcorner.x - (map_origin.x + p1.x))
        return azimuthal_map(chart_number, chart_side, north, delta)

    f.add(m)

    m.bordered = False

    m.gridline_factory.meridian_line_interval = 15
    m.gridline_factory.meridian_marked_tick_interval = 15
    m.gridline_factory.meridian_tick_interval = 15
    m.gridline_factory.parallel_line_interval = 1
    m.gridline_factory.parallel_marked_tick_interval = 1
    m.gridline_factory.parallel_tick_interval = 1

    m.gridline_factory.marked_ticksize = 0
    m.gridline_factory.unmarked_ticksize = 0
    m.gridline_factory.fixed_tick_reach = False

    m.gridline_factory.label_distance = 1

    m.gridline_factory.rotate_meridian_labels = True
    m.gridline_factory.meridian_labeltextfunc = azimuthal_meridian_label

    m.min_longitude = 0
    m.max_longitude = 360
    if north:
        m.min_latitude = 84
        m.max_latitude = 90
    else:
        m.min_latitude = -90
        m.max_latitude = -84

    return f, m


# Conic map areas
def conic_map(chart_number, chart_side, min_longitude, max_longitude, min_latitude, max_latitude, meridian_interval, offset, delta=None):
    latitude_range = max_latitude - min_latitude
    center_latitude = min_latitude + 0.5 * latitude_range

    if delta is not None:
        offset += delta

    if chart_side == 'left':
        fn = "{:02}A".format(chart_number)
        f = leftfigure(fn)
        map_llcorner = LMAP_LLCORNER + Point(0, LEGEND_HEIGHT + offset)
        map_urcorner = map_llcorner + Point(LEGEND_WIDTH, latitude_range * MM_PER_DEGREE)
        center_longitude = min_longitude
        map_origin = map_llcorner + Point(LEGEND_WIDTH, 0.5 * latitude_range * MM_PER_DEGREE)
    else:
        fn = "{:02}B".format(chart_number)
        f = rightfigure(fn)
        map_llcorner = RMAP_LLCORNER + Point(0, LEGEND_HEIGHT + offset)
        map_urcorner = map_llcorner + Point(LEGEND_WIDTH, latitude_range * MM_PER_DEGREE)
        center_longitude = max_longitude
        map_origin = map_llcorner + Point(0, 0.5 * latitude_range * MM_PER_DEGREE)

    sp1 = min_latitude + int(round(latitude_range / 6.0))
    sp2 = min_latitude + int(round(5.0 * latitude_range / 6.0))

    m = EquidistantConicMapArea(map_llcorner, map_urcorner, hmargin=MAP_HMARGIN, vmargin=MAP_VMARGIN,
                                center=(center_longitude, center_latitude), standard_parallel1=sp1, standard_parallel2=sp2,
                                latitude_range=latitude_range, origin=map_origin, celestial=True, box=False)

    # Determine correct origin for south conic maps
    if center_latitude < 0 and delta is None:
        p1 = m.projection(SphericalPoint(max_longitude, min_latitude))
        p2 = m.projection(SphericalPoint(min_longitude, min_latitude))
        delta = abs(p1.y - p2.y)
        return conic_map(chart_number, chart_side, min_longitude, max_longitude, min_latitude, max_latitude, meridian_interval, offset, delta)

    f.add(m)

    m.bordered = False

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

    m.min_longitude = min_longitude
    m.max_longitude = max_longitude
    m.min_latitude = min_latitude
    m.max_latitude = max_latitude

    return f, m


def equatorial_map(chart_number, chart_side, min_longitude, max_longitude, max_latitude, meridian_interval, offset):
    latitude_range = 2 * max_latitude

    if chart_side == 'left':
        fn = "{:02}A".format(chart_number)
        f = leftfigure(fn)
        map_llcorner = LMAP_LLCORNER + Point(0, LEGEND_HEIGHT + offset)
        map_urcorner = map_llcorner + Point(LEGEND_WIDTH, latitude_range * MM_PER_DEGREE)
        center_longitude = min_longitude
        map_origin = map_llcorner + Point(LEGEND_WIDTH, 0.5 * latitude_range * MM_PER_DEGREE)
    else:
        fn = "{:02}B".format(chart_number)
        f = rightfigure(fn)
        map_llcorner = RMAP_LLCORNER + Point(0, LEGEND_HEIGHT + offset)
        map_urcorner = map_llcorner + Point(LEGEND_WIDTH, latitude_range * MM_PER_DEGREE)
        center_longitude = max_longitude
        map_origin = map_llcorner + Point(0, 0.5 * latitude_range * MM_PER_DEGREE)

    sp = 2*max_latitude/3.0

    m = EquidistantCylindricalMapArea(map_llcorner, map_urcorner, MAP_HMARGIN, MAP_VMARGIN, center_longitude, map_origin, sp, latitude_range, celestial=True, box=False)
    f.add(m)

    m.bordered = False

    m.gridline_factory.meridian_line_interval = meridian_interval
    m.gridline_factory.meridian_marked_tick_interval = meridian_interval
    m.gridline_factory.meridian_tick_interval = meridian_interval
    m.gridline_factory.parallel_line_interval = 1
    m.gridline_factory.parallel_marked_tick_interval = 1
    m.gridline_factory.parallel_tick_interval = 1

    m.gridline_factory.marked_ticksize = 0
    m.gridline_factory.unmarked_ticksize = 0

    m.gridline_factory.label_distance = 1

    m.gridline_factory.rotate_parallel_labels = True

    m.gridline_factory.rotate_meridian_labels = True
    m.gridline_factory.meridian_labeltextfunc = meridian_label

    m.min_longitude = min_longitude
    m.max_longitude = max_longitude
    m.min_latitude = -max_latitude
    m.max_latitude = max_latitude

    return f, m

if __name__ == "__main__":
    chart_number = 1

    # North azimuthal maps
    # Left page
    f, m = azimuthal_map(chart_number, 'left', True)
    p1 = Point(-PAPERSIZE[0], -PAPERSIZE[1])
    p2 = Point(m.map_box.p2.x, PAPERSIZE[1])
    with m.clip(Rectangle(p1, p2).path):
        m.draw_meridians(origin_offsets=AZIMUTHAL_OFFSETS)
        m.draw_parallels()

    with m.clip(m.clipping_path):
        m.draw_constellations(linewidth=0.3)
        m.draw_ecliptic(linewidth=ECLIPTIC_LINEWIDTH, tickinterval=1, dashed=ECLIPTIC_DASH_PATTERN, poles=True)
        m.draw_galactic(linewidth=GALACTIC_LINEWIDTH, tickinterval=1, dashed=GALACTIC_DASH_PATTERN, poles=True)

    # Legend
    leftlegend(f, chart_number)
    f.render(os.path.join(OUTPUT_FOLDER, "{:02}A.pdf".format(chart_number)), open=False)

    # Right page
    f, m = azimuthal_map(chart_number, 'right', True)
    p1 = Point(m.map_box.p1.x, -PAPERSIZE[1])
    p2 = Point(PAPERSIZE[0], PAPERSIZE[1])
    with m.clip(Rectangle(p1, p2).path):
        m.draw_meridians(origin_offsets=AZIMUTHAL_OFFSETS)
        m.draw_parallels()

    with m.clip(m.clipping_path):
        m.draw_constellations(linewidth=0.3)
        m.draw_ecliptic(linewidth=ECLIPTIC_LINEWIDTH, tickinterval=1, dashed=ECLIPTIC_DASH_PATTERN, poles=True)
        m.draw_galactic(linewidth=GALACTIC_LINEWIDTH, tickinterval=1, dashed=GALACTIC_DASH_PATTERN, poles=True)

    # Legend
    rightlegend(f, chart_number, 0, 360, 84, 90)
    f.render(os.path.join(OUTPUT_FOLDER, "{:02}B.pdf".format(chart_number)), open=False)

    # North conic maps
    for conic in CONICS:
        n = 360/abs(conic['longitude_step'])
        for i in range(n):
            center_longitude = i * conic['longitude_step']
            chart_number += 1

            # Left page
            chart_side = 'left'
            f, m = conic_map(
                chart_number, chart_side,
                center_longitude, center_longitude + conic['longitude_range'],
                conic['min_latitude'], conic['max_latitude'],
                conic['meridian_interval'], conic['offset']
            )

            m.draw_meridians()
            m.draw_parallels()
            with m.clip(m.clipping_path):
                m.draw_constellations(linewidth=0.3)
                m.draw_ecliptic(linewidth=ECLIPTIC_LINEWIDTH, tickinterval=1, dashed=ECLIPTIC_DASH_PATTERN, poles=True)
                m.draw_galactic(linewidth=GALACTIC_LINEWIDTH, tickinterval=1, dashed=GALACTIC_DASH_PATTERN, poles=True)

            # Legend
            leftlegend(f, chart_number)
            f.render(os.path.join(OUTPUT_FOLDER, "{:02}A.pdf".format(chart_number)), open=False)

            # Right page
            chart_side = 'right'
            f, m = conic_map(
                chart_number, chart_side,
                center_longitude - conic['longitude_range'], center_longitude,
                conic['min_latitude'], conic['max_latitude'],
                conic['meridian_interval'], conic['offset']
            )

            m.draw_meridians()
            m.draw_parallels()
            with m.clip(m.clipping_path):
                m.draw_constellations(linewidth=0.3)
                m.draw_ecliptic(linewidth=ECLIPTIC_LINEWIDTH, tickinterval=1, dashed=ECLIPTIC_DASH_PATTERN, poles=True)
                m.draw_galactic(linewidth=GALACTIC_LINEWIDTH, tickinterval=1, dashed=GALACTIC_DASH_PATTERN, poles=True)

            # Legend
            rightlegend(f, chart_number, center_longitude - conic['longitude_range'], center_longitude + conic['longitude_range'], conic['min_latitude'], conic['max_latitude'])
            f.render(os.path.join(OUTPUT_FOLDER, "{:02}B.pdf".format(chart_number)), open=False)

    # Equatorial maps
    # chart_number = 100
    longitude_step = -18
    longitude_range = 10
    max_latitude = 6
    meridian_interval = 1
    offset = 22
    n = 360/abs(longitude_step)

    for i in range(n):
        center_longitude = i * longitude_step
        chart_number += 1

        # Left page
        chart_side = "left"
        f, m = equatorial_map(
            chart_number, chart_side,
            center_longitude, center_longitude + longitude_range,
            max_latitude,
            meridian_interval, offset
        )

        m.draw_meridians()
        m.draw_parallels()
        with m.clip(m.clipping_path):
            m.draw_constellations(linewidth=0.3)
            m.draw_ecliptic(linewidth=ECLIPTIC_LINEWIDTH, tickinterval=1, dashed=ECLIPTIC_DASH_PATTERN, poles=True)
            m.draw_galactic(linewidth=GALACTIC_LINEWIDTH, tickinterval=1, dashed=GALACTIC_DASH_PATTERN, poles=True)

        # Legend
        leftlegend(f, chart_number)
        f.render(os.path.join(OUTPUT_FOLDER, "{:02}A.pdf".format(chart_number)), open=False)

        # Right page
        chart_side = "right"
        f, m = equatorial_map(
            chart_number, chart_side,
            center_longitude - longitude_range, center_longitude,
            max_latitude,
            meridian_interval, offset
        )

        m.draw_meridians()
        m.draw_parallels()
        with m.clip(m.clipping_path):
            m.draw_constellations(linewidth=0.3)
            m.draw_ecliptic(linewidth=ECLIPTIC_LINEWIDTH, tickinterval=1, dashed=ECLIPTIC_DASH_PATTERN, poles=True)
            m.draw_galactic(linewidth=GALACTIC_LINEWIDTH, tickinterval=1, dashed=GALACTIC_DASH_PATTERN, poles=True)

        # Legend
        rightlegend(f, chart_number, center_longitude - longitude_range, center_longitude + longitude_range, -max_latitude, max_latitude)
        f.render(os.path.join(OUTPUT_FOLDER, "{:02}B.pdf".format(chart_number)), open=False)

    # South conic maps
    #chart_number = 120
    for conic in reversed(CONICS):
        n = 360/abs(conic['longitude_step'])
        for i in range(n):
            center_longitude = i * conic['longitude_step']
            chart_number += 1

            # Left page
            chart_side = 'left'

            f, m = conic_map(
                chart_number, chart_side,
                center_longitude, center_longitude + conic['longitude_range'],
                -conic['max_latitude'], -conic['min_latitude'],
                conic['meridian_interval'], conic['offset']
            )

            # Determine correct map origin

            m.draw_meridians()
            m.draw_parallels()
            with m.clip(m.clipping_path):
                m.draw_constellations(linewidth=0.3)
                m.draw_ecliptic(linewidth=ECLIPTIC_LINEWIDTH, tickinterval=1, dashed=ECLIPTIC_DASH_PATTERN, poles=True)
                m.draw_galactic(linewidth=GALACTIC_LINEWIDTH, tickinterval=1, dashed=GALACTIC_DASH_PATTERN, poles=True)

            # Legend
            leftlegend(f, chart_number)
            f.render(os.path.join(OUTPUT_FOLDER, "{:02}A.pdf".format(chart_number)), open=False)

            # Right page
            chart_side = 'right'
            f, m = conic_map(
                chart_number, chart_side,
                center_longitude - conic['longitude_range'], center_longitude,
                -conic['max_latitude'], -conic['min_latitude'],
                conic['meridian_interval'], conic['offset']
            )

            m.draw_meridians()
            m.draw_parallels()
            with m.clip(m.clipping_path):
                m.draw_constellations(linewidth=0.3)
                m.draw_ecliptic(linewidth=ECLIPTIC_LINEWIDTH, tickinterval=1, dashed=ECLIPTIC_DASH_PATTERN, poles=True)
                m.draw_galactic(linewidth=GALACTIC_LINEWIDTH, tickinterval=1, dashed=GALACTIC_DASH_PATTERN, poles=True)

            # Legend
            rightlegend(f, chart_number, center_longitude - conic['longitude_range'], center_longitude + conic['longitude_range'], -conic['min_latitude'], -conic['max_latitude'])
            f.render(os.path.join(OUTPUT_FOLDER, "{:02}B.pdf".format(chart_number)), open=False)

    # South azimuthal maps
    #chart_number = 220
    chart_number += 1
    # Left page
    f, m = azimuthal_map(chart_number, 'left', False)
    p1 = Point(-PAPERSIZE[0], -PAPERSIZE[1])
    p2 = Point(m.map_box.p2.x, PAPERSIZE[1])
    with m.clip(Rectangle(p1, p2).path):
        m.draw_meridians(origin_offsets=AZIMUTHAL_OFFSETS)
        m.draw_parallels()

    with m.clip(m.clipping_path):
        m.draw_constellations(linewidth=0.3)
        m.draw_ecliptic(linewidth=ECLIPTIC_LINEWIDTH, tickinterval=1, dashed=ECLIPTIC_DASH_PATTERN, poles=True)
        m.draw_galactic(linewidth=GALACTIC_LINEWIDTH, tickinterval=1, dashed=GALACTIC_DASH_PATTERN, poles=True)

    # Legend
    leftlegend(f, chart_number)
    f.render(os.path.join(OUTPUT_FOLDER, "{:02}A.pdf".format(chart_number)), open=False)

    # Right page
    f, m = azimuthal_map(chart_number, 'right', False)
    p1 = Point(m.map_box.p1.x, -PAPERSIZE[1])
    p2 = Point(PAPERSIZE[0], PAPERSIZE[1])
    with m.clip(Rectangle(p1, p2).path):
        m.draw_meridians(origin_offsets=AZIMUTHAL_OFFSETS)
        m.draw_parallels()

    with m.clip(m.clipping_path):
        m.draw_constellations(linewidth=0.3)
        m.draw_ecliptic(linewidth=ECLIPTIC_LINEWIDTH, tickinterval=1, dashed=ECLIPTIC_DASH_PATTERN, poles=True)
        m.draw_galactic(linewidth=GALACTIC_LINEWIDTH, tickinterval=1, dashed=GALACTIC_DASH_PATTERN, poles=True)

    # Legend
    rightlegend(f, chart_number, 0, 360, -84, -90)
    f.render(os.path.join(OUTPUT_FOLDER, "{:02}B.pdf".format(chart_number)), open=False)