import math

from hipparcos import HourAngle, select_stars
from projection import StereographicCylinder, LambertConformalConic, InvertedLambertConformalConic
from draw_metapost import *
from geometry import rotate_point


def draw_star(fp, star, map_projection):
    x, y = map_projection.project_to_map(star.right_ascension, star.declination)
    if not map_projection.inside_viewport(x, y):
        return
    size = 0.5*math.exp(math.log(10)*0.125*(6.5-star.visual_magnitude))
    draw_point(fp, x, y, size+0.1, color="white")
    draw_point(fp, x, y, size)
    if star.identifier_string.strip():
        return prepare_text(x - 0.8 + 0.5 * size, y, star.identifier_string, "rt", "tiny")



def draw_equatorial_map(start_longitude, stop_longitude, start_latitude, stop_latitude, filename=None, im_width=290, im_height=223):
    sc = StereographicCylinder(standard_parallel=30, source_distance_scale=1)
    sc.set_longitude_limits(start_longitude, stop_longitude)
    sc.set_latitude_limits(start_latitude, stop_latitude)
    sc.set_map_size(im_width-40, im_height-40)
    sc.set_map_offset(20, 20)

    with open("mpost/map.mp", "w") as fp:
        fp.write("% Equatorial star map\n\n")
        fp.write("verbatimtex\n")
        fp.write("%&latex\n")
        fp.write("\\documentclass{article}\n")
        fp.write("\\begin{document}\n")
        fp.write("etex\n\n")
        fp.write("beginfig(1);\n")

        labels = []
        ticks = []

        fp.flush()
        fp.write("\n% Meridians\n")
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
            tickp1 = (p1[0], p1[1]-1)
            tickp2 = (p2[0], p2[1]+1)

            if not longitude % 15:
                marker = "\\textbf{{{0}\\textsuperscript{{h}}}}".format(ha.hours)
                textsize = "small"
                draw_line(fp, p1[0], p1[1], p2[0], p2[1], "black")

            else:
                marker = "{0}\\textsuperscript{{m}}".format(ha.minutes)
                textsize = "scriptsize"

            ticks.append((p1, tickp1))
            ticks.append((p2, tickp2))
            labels.append(prepare_text(tickp1[0], tickp1[1], marker, pos1, textsize))
            labels.append(prepare_text(tickp2[0], tickp2[1], marker, pos2, textsize))

        fp.flush()
        fp.write("\n% Parallels\n")
        for i in range(35):
            latitude = -85 + i * 5
            if latitude < start_latitude or latitude > stop_latitude:
                continue

            p1, p2, pos1, pos2 = sc.points_for_parallel(latitude)
            tickp1 = (p1[0]+1, p1[1])
            tickp2 = (p2[0]-1, p2[1])

            if latitude > 0:
                marker = "$+{0}^{{\\circ}}$".format(latitude)
            else:
                marker = "${0}^{{\\circ}}$".format(latitude)

            if not latitude % 10:
                draw_line(fp, p1[0], p1[1], p2[0], p2[1], "black")

            ticks.append((p1, tickp1))
            ticks.append((p2, tickp2))

            if marker:
                labels.append(prepare_text(tickp1[0], tickp1[1], marker, pos1, "scriptsize"))
                labels.append(prepare_text(tickp2[0], tickp2[1], marker, pos2, "scriptsize"))

        fp.flush()
        fp.write("\n% Bounding boxes\n")
        clip_image(fp, (20, 20, im_width-20, im_height-20))
        draw_rectange(fp, 20, 20, im_width-20, im_height-20)
        draw_rectange(fp, 0, 0, im_width, im_height, linewidth=0)

        fp.flush()
        fp.write("\n% Stars\n")
        bs = select_stars(magnitude=6.5, constellation=None, ra_range=(start_longitude, stop_longitude), dec_range=(start_latitude, stop_latitude))
        for s in bs:
            l = draw_star(fp, s, sc)
            if l:
                labels.append(l)

        fp.flush()
        fp.write("\n% Labels\n")
        for l in labels:
            fp.write(l)
        for p1, p2 in ticks:
            draw_line(fp, p1[0], p1[1], p2[0], p2[1])

        fp.flush()
        fp.write("endfig;\n")
        fp.write("end;\n")

    render_map(filename)


def draw_intermediate_map(start_longitude, stop_longitude, start_latitude, stop_latitude, filename, im_width=290, im_height=223):
    if start_latitude > stop_latitude:
        raise ValueError("Invalid start and stop latitudes!")

    if start_longitude < stop_longitude:
        origin_longitude = 0.5*(start_longitude+stop_longitude)
    else:
        origin_longitude = 0.5*(start_longitude+stop_longitude) - 180.0

    if start_latitude > 0:
        hemisphere = "N"
        sc = LambertConformalConic(standard_parallel1=start_latitude, standard_parallel2=stop_latitude, origin_longitude=origin_longitude, origin_latitude=start_latitude-3)
    elif stop_latitude < 0:
        hemisphere = "S"
        sc = InvertedLambertConformalConic(standard_parallel1=start_latitude, standard_parallel2=stop_latitude, origin_longitude=origin_longitude, origin_latitude=stop_latitude+3)
    else:
        raise ValueError("Invalid start or stop latitudes!")

    sc.set_map_size(im_width-40, im_height-40)
    sc.set_map_offset(20, 20)
    sc.set_latitude_limits(start_latitude-3, stop_latitude+3)
    sc.calculate_map_pole()

    print sc.min_longitude, sc.max_longitude
    print sc.lowest_latitude, sc.max_latitude
    print "LL:", sc.project_from_map(sc.map_offset_x, sc.map_offset_y)
    print "LR:", sc.project_from_map(sc.map_offset_x+sc.map_size_x, sc.map_offset_y)


    with open("mpost/map.mp", "w") as fp:
        fp.write("% Intermediate star map\n\n")
        fp.write("verbatimtex\n")
        fp.write("%&latex\n")
        fp.write("\\documentclass{article}\n")
        fp.write("\\begin{document}\n")
        fp.write("etex\n\n")
        fp.write("beginfig(1);\n")

        labels = []
        ticks = []

        fp.flush()
        fp.write("\n% Meridians\n")
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
            tickp1 = rotate_point((p1[0]+1,p1[1]), p1, angle+180)
            tickp2 = rotate_point((p2[0]+1,p2[1]), p2, angle)
            ticks.append((p1, tickp1))
            ticks.append((p2, tickp2))

            if not longitude % 15:
                color = "black"
                marker = "\\textbf{{{0}\\textsuperscript{{h}}}}".format(ha.hours)
                textsize = "small"
                draw_line(fp, p1[0], p1[1], p2[0], p2[1], color)
            else:
                marker = "{0}\\textsuperscript{{m}}".format(ha.minutes)
                textsize = "scriptsize"

            if hemisphere == "N":
                all_label_pos = "bot"
            else:
                all_label_pos = "top"

            if pos1 and (pos1 == all_label_pos or textsize == "small"):
                labels.append(prepare_text(tickp1[0], tickp1[1], marker, pos1, textsize))
            if pos2 and (pos2 == all_label_pos or textsize == "small"):
                labels.append(prepare_text(tickp2[0], tickp2[1], marker, pos2, textsize))

        fp.flush()
        fp.write("\n% Parallels\n")
        for i in range(8):
            if hemisphere == "N":
                latitude = 10 + i*10
                marker = "$+{0}^{{\\circ}}$".format(latitude)
            else:
                latitude = -10 - i*10
                marker = "${0}^{{\\circ}}$".format(latitude)

            center = sc.map_pole
            radius, intersections = sc.radius_for_parallel(latitude)
            color = "black"

            draw_circle(fp, center, radius, color)
            for ip, pos, angle in intersections:
                if pos == "lft":
                    tickp = rotate_point((ip[0]-1, ip[1]), ip, angle)
                elif pos == "rt":
                    tickp = rotate_point((ip[0]+1, ip[1]), ip, angle)
                ticks.append((ip, tickp))
                labels.append(prepare_text(tickp[0], tickp[1], marker, pos, "scriptsize", angle=angle))

        fp.flush()
        fp.write("\n% Bounding boxes\n")
        clip_image(fp, (20, 20, im_width-20, im_height-20))
        draw_rectange(fp, 20, 20, im_width-20, im_height-20)
        draw_rectange(fp, 0, 0, im_width, im_height, linewidth=0)

        fp.flush()
        fp.write("\n% Stars\n")

        if hemisphere == "N":
            dec_range = (sc.lowest_latitude, sc.max_latitude)
        else:
            dec_range = (sc.max_latitude, sc.lowest_latitude)

        bs = select_stars(magnitude=6.5, constellation=None, ra_range=(sc.min_longitude, sc.max_longitude), dec_range=dec_range)

        maxstar = bs[0]
        for s in bs:
            if s.visual_magnitude < maxstar.visual_magnitude:
                maxstar = s
            l = draw_star(fp, s, sc)
            if l:
                labels.append(l)

        fp.flush()
        fp.write("\n% Labels\n")
        for l in labels:
            fp.write(l)
        for p1, p2 in ticks:
            draw_line(fp, p1[0], p1[1], p2[0], p2[1])

        fp.flush()
        fp.write("endfig;\n")
        fp.write("end;\n")

    render_map(filename)


if __name__ == "__main__":
    #draw_equatorial_map(30, 120, -28, 28, "maps/skymap1.pdf")
    #draw_intermediate_map(300, 60, -70, -20, "maps/skymap2.pdf")
    draw_intermediate_map(120, 240, 20, 70, "maps/skymap2.pdf")