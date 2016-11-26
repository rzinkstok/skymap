import sqlite3
import os
import shutil
import math
import subprocess

from hipparcos import HipparcosStar, HourAngle
from projection import StereographicCylinder, LambertConformalConic


def select_stars(magnitude=0.0, constellation=None, ra_range=None, dec_range=None):
    conn = sqlite3.connect("hipparcos/hipparcos.db")
    c = conn.cursor()

    result = []
    q = "SELECT * " \
        "FROM main " \
        "JOIN photo ON photo.id=main.id " \
        "JOIN biblio ON biblio.id=main.id " \
        "WHERE photo.Vmag<{0}".format(magnitude)
    if constellation:
        q += " AND biblio.constellation='{0}'".format(constellation)
    if ra_range:
        if ra_range[0] < 0:
            while ra_range[0] < 0:
                ra_range = (ra_range[0] + 360, ra_range[1])
        if ra_range[1] < 0:
            while ra_range[1] < 0:
                ra_range = (ra_range[0], ra_range[1]+360)

        if ra_range[0] < 0 or ra_range[0] > 360 or ra_range[1] < 0 or ra_range[1] > 360:
            raise ValueError("Illegal RA range!")
        if ra_range[0] < ra_range[1]:
            q += " AND main.right_ascension>={0} AND main.right_ascension<={1}".format(ra_range[0], ra_range[1])
        elif ra_range[1] < ra_range[0]:
            q += " AND (main.right_ascension>={0} OR main.right_ascension<={1})".format(ra_range[0], ra_range[1])
        else:
            raise ValueError("Illegal RA range!")
    if dec_range:
        if dec_range[0] < -90 or dec_range[0] > 90 or dec_range[1] < -90 or dec_range[1] > 90 or dec_range[1] <= dec_range[0]:
            raise ValueError("Illegal DEC range!")
        q += " AND main.declination>={0} AND main.declination<={1}".format(dec_range[0], dec_range[1])

    q += " ORDER BY photo.Vmag ASC"
    res = c.execute(q)
    columns = [x[0] for x in res.description]
    for row in res:
        result.append(HipparcosStar(row, columns))

    conn.close()
    return result


def draw_rectange(fp, x1, y1, x2, y2, color="black", width=1):
    p1 = "({0}mm,{1}mm)".format(x1, y1)
    p2 = "({0}mm,{1}mm)".format(x1, y2)
    p3 = "({0}mm,{1}mm)".format(x2, y2)
    p4 = "({0}mm,{1}mm)".format(x2, y1)
    s = "draw {0}--{1}--{2}--{3}--cycle withcolor {4} withpen pencircle scaled {5}pt;;\n".format(p1, p2, p3, p4, color, width)
    fp.write(s)


def draw_line(fp, x1, y1, x2, y2, color="black"):
    p1 = "({0}mm,{1}mm)".format(x1, y1)
    p2 = "({0}mm,{1}mm)".format(x2, y2)
    s = "draw {0}--{1} withcolor {2};\n".format(p1, p2, color)
    fp.write(s)


def draw_point(fp, x, y, size, color="black"):
    p1 = "({0}mm,{1}mm)".format(x, y)
    s = "draw {0} withcolor {1} withpen pencircle scaled {2}mm;\n".format(p1, color, size)
    fp.write(s)


def prepare_text(x, y, text, pos, size="tiny", scale=None, angle=None):
    o = "(0,0)"
    p1 = "({0}mm,{1}mm)".format(x, y)
    if scale:
        s = "label.{0}(btex \\{1} {2} etex scaled {3}, {4})".format(pos, size, text, scale, o)
    else:
        s = "label.{0}(btex \\{1} {2} etex, {3})".format(pos, size, text, o)

    if angle:
        s += " rotated {0}".format(angle)

    s += " shifted {0};\n".format(p1)
    return s


def draw_circle(fp, center, radius, color="black"):
    fp.write("draw fullcircle scaled {0}mm shifted ({1}mm, {2}mm) withcolor {3};\n".format(2*radius, center[0], center[1], color))


def draw_star(fp, star, map_projection):
    x, y = map_projection.project_to_map(star.right_ascension, star.declination)
    if not map_projection.inside_viewport(x, y):
        return
    size = 0.25*math.exp(math.log(10)*0.125*(6.5-star.visual_magnitude))
    draw_point(fp, x, y, size+0.05, color="white")
    draw_point(fp, x, y, size)
    if star.identifier_string.strip():
        return prepare_text(x - 0.8 + 0.5 * size, y, star.identifier_string, "rt", "tiny", scale=0.5)


def clip_image(fp, clipbox):
    x1, y1, x2, y2 = clipbox
    p1 = "({0}mm,{1}mm)".format(x1, y1)
    p2 = "({0}mm,{1}mm)".format(x1, y2)
    p3 = "({0}mm,{1}mm)".format(x2, y2)
    p4 = "({0}mm,{1}mm)".format(x2, y1)
    fp.write("path b;\n")
    fp.write("b := {0}--{1}--{2}--{3}--cycle;\n".format(p1, p2, p3, p4))
    fp.write("clip currentpicture to b;\n")


def draw_equatorial_map(start_longitude, stop_longitude, start_latitude, stop_latitude, filename=None, im_width=200, im_height=150):
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

        fp.flush()
        fp.write("\n% Stars\n")
        bs = select_stars(magnitude=6.5, constellation=None, ra_range=(start_longitude, stop_longitude), dec_range=(start_latitude, stop_latitude))
        for s in bs:
            l = draw_star(fp, s, sc)
            if l:
                labels.append(l)

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

            if not longitude % 15:
                marker = "\\textbf{{{0}\\textsuperscript{{h}}}}".format(ha.hours)
                textsize = "small"
                draw_line(fp, p1[0], p1[1], p2[0], p2[1], "black")
            else:
                marker = "{0}m".format(ha.minutes)
                textsize = "tiny"

            labels.append(prepare_text(p1[0], p1[1], marker, pos1, textsize))
            labels.append(prepare_text(p2[0], p2[1], marker, pos2, textsize))

        fp.flush()
        fp.write("\n% Parallels\n")
        for i in range(35):
            latitude = -85 + i * 5
            if latitude < start_latitude or latitude > stop_latitude:
                continue

            p1, p2, pos1, pos2 = sc.points_for_parallel(latitude)

            if latitude > 0:
                marker = "$+{0}^{{\\circ}}$".format(latitude)
            else:
                marker = "${0}^{{\\circ}}$".format(latitude)

            if not latitude % 10:
                draw_line(fp, p1[0], p1[1], p2[0], p2[1], "black")
            else:
                pass

            if marker:
                labels.append(prepare_text(p1[0], p1[1], marker, pos1, "small", 0.7))
                labels.append(prepare_text(p2[0], p2[1], marker, pos2, "small", 0.7))

        fp.flush()
        fp.write("\n% Bounding boxes\n")
        clip_image(fp, (20, 20, im_width-20, im_height-20))
        draw_rectange(fp, 20, 20, im_width-20, im_height-20)
        draw_rectange(fp, 0, 0, im_width, im_height, width=0)

        fp.flush()
        fp.write("\n% Labels\n")
        for l in labels:
            fp.write(l)

        fp.flush()
        fp.write("endfig;\n")
        fp.write("end;\n")

    subprocess.Popen(["mpost", "map"], cwd="mpost").wait()
    subprocess.Popen(["mptopdf map.1"], shell=True, cwd="mpost").wait()
    shutil.move("mpost/map-1.pdf", filename)
    subprocess.Popen(["open", filename]).wait()


def draw_intermediate_map(start_longitude, stop_longitude, start_latitude, stop_latitude, filename, im_width=200, im_height=150):
    if start_latitude < 0 and stop_latitude < 0:
        start_latitude = abs(start_latitude)
        stop_latitude = abs(stop_latitude)
        hemisphere = "S"
    elif start_latitude > 0 and stop_latitude > 0:
        hemisphere = "N"
    else:
        raise ValueError("Can only draw intermediate maps of areas that do not span the equator!")

    if start_latitude > stop_latitude:
        raise ValueError("Invalid start and stop latitudes!")

    if start_longitude < stop_longitude:
        origin_longitude = 0.5*(start_longitude+stop_longitude)
    else:
        origin_longitude = 0.5*(start_longitude+stop_longitude) - 180.0

    sc = LambertConformalConic(standard_parallel1=start_latitude, standard_parallel2=stop_latitude, origin_longitude=origin_longitude, origin_latitude=start_latitude, hemisphere=hemisphere)
    sc.set_map_size(im_width-40, im_height-40)
    sc.set_map_offset(20, 20)
    sc.set_latitude_limits(start_latitude-3, stop_latitude+3)
    sc.calculate_map_pole()

    print sc.min_longitude, sc.max_longitude
    print sc.lowest_latitude, sc.max_latitude

    with open("mpost/map.mp", "w") as fp:
        fp.write("% Intermediate star map\n\n")
        fp.write("verbatimtex\n")
        fp.write("%&latex\n")
        fp.write("\\documentclass{article}\n")
        fp.write("\\begin{document}\n")
        fp.write("etex\n\n")
        fp.write("beginfig(1);\n")

        labels = []

        fp.flush()
        fp.write("\n% Stars\n")
        if sc.hemisphere == "N":
            bs = select_stars(magnitude=6.5, constellation=None, ra_range=(sc.min_longitude, sc.max_longitude), dec_range=(sc.lowest_latitude, sc.max_latitude))
        else:
            bs = select_stars(magnitude=6.5, constellation=None, ra_range=(sc.min_longitude, sc.max_longitude), dec_range=(-sc.max_latitude, -sc.lowest_latitude))

        for s in bs:
            if sc.hemisphere == "N":
                x, y = sc.project_to_map(s.right_ascension, s.declination)
            else:
                x, y = sc.project_to_map(s.right_ascension, -s.declination)

            if not sc.inside_viewport(x, y):
                continue
            size = 0.25*math.exp(math.log(10)*0.125*(6.5-s.visual_magnitude))
            draw_point(fp, x, y, size)
            if s.identifier_string.strip():
                labels.append(prepare_text(x - 0.8 + 0.5 * size, y, s.identifier_string, "rt", "tiny", scale=0.5))

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

            if not longitude % 15:
                color = "black"
                marker = "\\textbf{{{0}\\textsuperscript{{h}}}}".format(ha.hours)
                textsize = "small"
            else:
                color = "0.8 white"
                marker = "{0}m".format(ha.minutes)
                textsize = "tiny"

            p1, p2, pos1, pos2 = sc.points_for_meridian(longitude)
            draw_line(fp, p1[0], p1[1], p2[0], p2[1], color)

            if sc.hemisphere == "N":
                all_label_pos = "bot"
            if sc.hemisphere == "S":
                all_label_pos = "top"

            if pos1 and (pos1 == all_label_pos or textsize == "small"):
                labels.append(prepare_text(p1[0], p1[1], marker, pos1, textsize))
            if pos2 and (pos2 == all_label_pos or textsize == "small"):
                labels.append(prepare_text(p2[0], p2[1], marker, pos2, textsize))

        fp.flush()
        fp.write("\n% Parallels\n")
        for i in range(7):
            latitude = start_latitude - 10 + i*10
            center = sc.map_pole
            radius, intersections = sc.radius_for_parallel(latitude)
            color = "black"
            if sc.hemisphere == "N":
                marker = "$+{0}^{{\\circ}}$".format(latitude)
            else:
                marker = "$-{0}^{{\\circ}}$".format(latitude)
            draw_circle(fp, center, radius, color)
            for ip, pos, angle in intersections:
                labels.append(prepare_text(ip[0], ip[1], marker, pos, "tiny", angle=angle))

        fp.flush()
        fp.write("\n% Bounding boxes\n")
        clip_image(fp, (20, 20, im_width-20, im_height-20))
        draw_rectange(fp, 20, 20, im_width-20, im_height-20)
        draw_rectange(fp, 0, 0, im_width, im_height)

        fp.flush()
        fp.write("\n% Labels\n")
        for l in labels:
            fp.write(l)

        fp.flush()
        fp.write("endfig;\n")
        fp.write("end;\n")

    subprocess.Popen(["mpost", "map"], cwd="mpost").wait()
    subprocess.Popen(["mptopdf map.1"], shell=True, cwd="mpost").wait()
    shutil.move("mpost/map-1.pdf", filename)
    subprocess.Popen(["open", filename]).wait()


if __name__ == "__main__":
    #draw_equatorial_map(30, 120, -28, 28, "maps/skymap1.pdf")
    draw_intermediate_map(300, 60, 20, 70, "maps/skymap2.pdf")