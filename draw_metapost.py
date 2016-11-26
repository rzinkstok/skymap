import subprocess
import shutil

def draw_rectange(fp, x1, y1, x2, y2, color="black", linewidth=0.5):
    p1 = "({0}mm,{1}mm)".format(x1, y1)
    p2 = "({0}mm,{1}mm)".format(x1, y2)
    p3 = "({0}mm,{1}mm)".format(x2, y2)
    p4 = "({0}mm,{1}mm)".format(x2, y1)
    s = "draw {0}--{1}--{2}--{3}--cycle withcolor {4} withpen pencircle scaled {5}pt;\n".format(p1, p2, p3, p4, color, linewidth)
    fp.write(s)


def draw_line(fp, x1, y1, x2, y2, color="black", linewidth=0.5):
    p1 = "({0}mm,{1}mm)".format(x1, y1)
    p2 = "({0}mm,{1}mm)".format(x2, y2)
    s = "draw {0}--{1} withcolor {2} withpen pencircle scaled {3}pt;\n".format(p1, p2, color, linewidth)
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


def draw_circle(fp, center, radius, color="black", linewidth=0.5):
    fp.write("draw fullcircle scaled {0}mm shifted ({1}mm, {2}mm) withcolor {3} withpen pencircle scaled {4}pt;\n".format(2*radius, center[0], center[1], color, linewidth))


def clip_image(fp, clipbox):
    x1, y1, x2, y2 = clipbox
    p1 = "({0}mm,{1}mm)".format(x1, y1)
    p2 = "({0}mm,{1}mm)".format(x1, y2)
    p3 = "({0}mm,{1}mm)".format(x2, y2)
    p4 = "({0}mm,{1}mm)".format(x2, y1)
    fp.write("path b;\n")
    fp.write("b := {0}--{1}--{2}--{3}--cycle;\n".format(p1, p2, p3, p4))
    fp.write("clip currentpicture to b;\n")


def render_map(filename):
    subprocess.Popen(["mpost", "map"], cwd="mpost").wait()
    subprocess.Popen(["mptopdf map.1"], shell=True, cwd="mpost").wait()
    shutil.move("mpost/map-1.pdf", filename)
    subprocess.Popen(["open", filename]).wait()