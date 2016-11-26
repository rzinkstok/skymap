import math

from hyg import select_stars
from projection import StereographicCylinder, LambertConformalConic, InvertedLambertConformalConic
from draw_metapost import MetaPostFigure
from geometry import Point, HourAngle
from constellations import get_constellation_boundaries, get_constellation_boundaries_for_area

FAINTEST_MAGNITUDE = 99 #6.5

def magnitude_to_size(magnitude):
    if magnitude < -0.5:
        magnitude = -0.5
    return 3.7*math.exp(-0.3*magnitude)


def draw_star(mp, star, map_projection):
    # if star.constellation == 'Cet':
    #     if 'alpha' in star.name.lower() or 'beta' in star.name.lower():
    #         print star.name, star.visual_magnitude, magnitude_to_size(star.visual_magnitude)
    #     if 'omicron' in star.name.lower():
    #         print star.name, star.visual_magnitude_max, star.visual_magnitude_min, magnitude_to_size(star.visual_magnitude_max), magnitude_to_size(star.visual_magnitude_min)
    p = map_projection.project_to_map(*star.propagate_position())
    if not map_projection.inside_viewport(p):
        return
    if star.is_variable:
        print "VARIABLE", star.identifier_string, star.proper
        min_size = magnitude_to_size(star.var_min)
        max_size = magnitude_to_size(star.var_max)
        mp.draw_point(p, max_size+0.15, color="white")
        mp.draw_circle(p, 0.5*max_size, linewidth=0.15)
        if star.var_min < FAINTEST_MAGNITUDE:
            mp.draw_point(p, min_size)
        size = max_size
    else:
        size = magnitude_to_size(star.mag)
        mp.draw_point(p, size+0.15, color="white")
        if star.is_multiple:
            print "MULTIPLE", star.identifier_string, star.proper
            mp.draw_line(Point(p[0]-0.5*size-0.2, p[1]), Point(p[0]+0.5*size+0.2, p[1]), linewidth=0.25)
        mp.draw_point(p, size)
    if star.identifier_string.strip():
        mp.draw_text(Point(p.x + 0.5 * size - 0.9, p.y), star.identifier_string, "rt", "tiny", scale=0.75, delay_write=True)
    if star.proper:
        mp.draw_text(Point(p.x, p.y - 0.5 * size + 0.8), star.proper, "bot", "tiny", scale=0.75, delay_write=True)


def draw_constellation_borders(mp, map_projection, color="black"):
    drawn_edges = []
    edges = get_constellation_boundaries_for_area(map_projection.min_longitude, map_projection.max_longitude, map_projection.lowest_latitude, map_projection.max_latitude)
    for e in edges:
        if e.identifier in drawn_edges:
            continue
        points = [map_projection.project_to_map(*p) for p in e.interpolated_points]
        mp.draw_polygon(points, closed=False, dotted=True, color=color)
        drawn_edges.append(e.identifier)
        drawn_edges.append(e.complement)
    return


def draw_constellation_border(mp, map_projection, constellation, drawn_edges, color="black"):
    edges = get_constellation_boundaries(constellation)
    for e in edges:
        if e.identifier in drawn_edges:
            continue
        points = [map_projection.project_to_map(*p) for p in e.interpolated_points]
        mp.draw_polygon(points, closed=False, dotted=True, color=color)
        drawn_edges.append(e.identifier)
        drawn_edges.append(e.complement)
    return drawn_edges


def draw_equatorial_map(start_longitude, stop_longitude, start_latitude, stop_latitude, filename=None, im_width=290, im_height=223):
    sc = StereographicCylinder(standard_parallel=0.7*stop_latitude, source_distance_scale=1)
    sc.set_longitude_limits(start_longitude, stop_longitude)
    sc.set_latitude_limits(start_latitude, stop_latitude)
    sc.set_map_size(im_width-40, im_height-40)
    sc.set_map_offset(20, 20)

    mp = MetaPostFigure("map", "Equatorial star map")

    mp.comment("Constellations")
    draw_constellation_borders(mp, sc)

    mp.comment("Meridians")
    for i in range(72):
        longitude = i * 5
        if start_longitude < stop_longitude:
            if longitude < start_longitude or longitude > stop_longitude:
                continue
        else:
            if start_longitude > longitude > stop_longitude:
                continue
        ha = HourAngle()
        ha.from_degrees(longitude)
        p1, p2, pos1, pos2 = sc.points_for_meridian(longitude)
        tickp1 = p1 + Point(0, -1)
        tickp2 = p2 + Point(0, 1)

        if not longitude % 15:
            marker = "\\textbf{{{0}\\textsuperscript{{h}}}}".format(ha.hours)
            textsize = "small"
            mp.draw_line(p1, p2, "black")

        else:
            marker = "{0}\\textsuperscript{{m}}".format(ha.minutes)
            textsize = "scriptsize"

        mp.draw_line(p1, tickp1, delay_write=True)
        mp.draw_line(p2, tickp2, delay_write=True)

        mp.draw_text(tickp1, marker, pos1, textsize, delay_write=True)
        mp.draw_text(tickp2, marker, pos2, textsize, delay_write=True)

    mp.comment("Parallels")
    for i in range(35):
        latitude = -85 + i * 5
        if latitude < start_latitude or latitude > stop_latitude:
            continue

        p1, p2, pos1, pos2 = sc.points_for_parallel(latitude)
        tickp1 = p1 + Point(1, 0)
        tickp2 = p2 + Point(-1, 0)

        if latitude > 0:
            marker = "+{0}$^{{\\circ}}$".format(latitude)
        else:
            marker = "--{0}$^{{\\circ}}$".format(abs(latitude))

        if not latitude % 10:
            mp.draw_line(p1, p2)

        mp.draw_line(p1, tickp1, delay_write=True)
        mp.draw_line(p2, tickp2, delay_write=True)

        if marker:
            mp.draw_text(tickp1, marker, pos1, "scriptsize", delay_write=True)
            mp.draw_text(tickp2, marker, pos2, "scriptsize", delay_write=True)

    mp.comment("Bounding boxes")
    mp.clip(Point(20, 20), Point(im_width-20, im_height-20))
    mp.draw_rectange(Point(20, 20), Point(im_width-20, im_height-20))
    mp.draw_rectange(Point(0, 0), Point(im_width, im_height), linewidth=0)

    mp.comment("Stars")
    bs = select_stars(magnitude=FAINTEST_MAGNITUDE, constellation=None, ra_range=(start_longitude, stop_longitude), dec_range=(start_latitude, stop_latitude))
    for s in bs:
        draw_star(mp, s, sc)

    mp.end_figure()
    mp.render(filename)


def draw_intermediate_map(start_longitude, stop_longitude, start_latitude, stop_latitude, filename, im_width=330, im_height=223):
    if start_latitude > stop_latitude:
        raise ValueError("Invalid start and stop latitudes!")

    if start_longitude < stop_longitude:
        origin_longitude = 0.5*(start_longitude+stop_longitude)
    else:
        origin_longitude = 0.5*(start_longitude+stop_longitude) - 180.0

    if stop_latitude == 90.0:
        sp1 = start_latitude
        sp2 = 90.0
    elif start_latitude == -90.0:
        sp1 = -90.0
        sp2 = stop_latitude
    else:
        central_latitude = 0.5*(start_latitude+stop_latitude)
        sp1 = central_latitude - (stop_latitude-start_latitude)/3.0
        sp2 = central_latitude + 0.4*(stop_latitude-start_latitude)/3.0

    if start_latitude > 0:
        hemisphere = "N"
        sc = LambertConformalConic(standard_parallel1=sp1, standard_parallel2=sp2, origin_longitude=origin_longitude, origin_latitude=start_latitude-3)
    elif stop_latitude < 0:
        hemisphere = "S"
        sc = InvertedLambertConformalConic(standard_parallel1=sp1, standard_parallel2=sp2, origin_longitude=origin_longitude, origin_latitude=stop_latitude+3)
    else:
        raise ValueError("Invalid start or stop latitudes!")

    sc.set_map_size(im_width-40, im_height-40)
    sc.set_map_offset(20, 20)
    sc.set_latitude_limits(start_latitude-3, stop_latitude+3)
    sc.calculate_map_pole()

    mp = MetaPostFigure("map", "Intermediate star map")


    mp.comment("Constellations")
    draw_constellation_borders(mp, sc)

    mp.comment("Meridians")
    for i in range(72):
        longitude = i * 5
        start_longitude = sc.min_longitude
        stop_longitude = sc.max_longitude

        if start_longitude < stop_longitude:
            if longitude < start_longitude or longitude > stop_longitude:
                continue
        else:
            if start_longitude > longitude > stop_longitude:
                continue

        ha = HourAngle()
        ha.from_degrees(longitude)
        p1, p2, pos1, pos2 = sc.points_for_meridian(longitude)
        angle = math.degrees(math.atan2(p2[1]-p1[1], p2[0]-p1[0]))
        tickp1 = p1 + Point(1, 0).rotate(angle+180)
        tickp2 = p2 + Point(1, 0).rotate(angle)
        mp.draw_line(p1, tickp1, delay_write=True)
        mp.draw_line(p2, tickp2, delay_write=True)

        if not longitude % 15:
            color = "black"
            marker = "\\textbf{{{0}\\textsuperscript{{h}}}}".format(ha.hours)
            textsize = "small"
            mp.draw_line(p1, p2, color)
        else:
            marker = "{0}\\textsuperscript{{m}}".format(ha.minutes)
            textsize = "scriptsize"

        if hemisphere == "N":
            all_label_pos = "bot"
        else:
            all_label_pos = "top"

        if pos1 and (pos1 == all_label_pos or textsize == "small"):
            mp.draw_text(tickp1, marker, pos1, textsize, delay_write=True)
        if pos2 and (pos2 == all_label_pos or textsize == "small"):
            mp.draw_text(tickp2, marker, pos2, textsize, delay_write=True)

    mp.comment("Parallels")
    for i in range(8):
        if hemisphere == "N":
            latitude = 10 + i*10
            marker = "+{0}$^{{\\circ}}$".format(latitude)
        else:
            latitude = -10 - i*10
            marker = "--{0}$^{{\\circ}}$".format(abs(latitude))

        center = sc.map_pole
        radius, intersections = sc.radius_for_parallel(latitude)
        color = "black"

        mp.draw_circle(center, radius, color)
        for ip, pos, angle in intersections:
            if pos == "lft":
                tickp = ip + Point(-1, 0).rotate(angle)
            elif pos == "rt":
                tickp = ip + Point(1, 0).rotate(angle)

            mp.draw_line(ip, tickp, delay_write=True)
            mp.draw_text(tickp, marker, pos, "scriptsize", angle=angle, delay_write=True)

    mp.comment("Bounding boxes")
    mp.clip(Point(20, 20), Point(im_width-20, im_height-20))
    mp.draw_rectange(Point(20, 20), Point(im_width-20, im_height-20))
    mp.draw_rectange(Point(0, 0), Point(im_width, im_height), linewidth=0)

    mp.comment("Stars")

    if hemisphere == "N":
        dec_range = (sc.lowest_latitude, sc.max_latitude)
    else:
        dec_range = (sc.max_latitude, sc.lowest_latitude)

    bs = select_stars(magnitude=FAINTEST_MAGNITUDE, constellation=None, ra_range=(sc.min_longitude, sc.max_longitude), dec_range=dec_range)

    for s in bs:
        draw_star(mp, s, sc)

    mp.end_figure()
    mp.render(filename)


if __name__ == "__main__":
    #draw_equatorial_map(0, 60, -20, 20, "maps/skymap1.pdf") # Cetus
    draw_equatorial_map(45, 105, -20, 20, "maps/skymap1.pdf") # Orion
    #draw_intermediate_map(300, 60, -70, -20, "maps/skymap2.pdf")
    #draw_intermediate_map(240, 0, 20, 70, "maps/skymap2.pdf")
