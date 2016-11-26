import subprocess
import shutil

from geometry import Point


class MetaPostFigure(object):
    def __init__(self, name, comment=None):
        self.name = name
        self.fp = open("mpost/{0}.mp".format(name), "w")
        self.delayed = []
        self.start_figure(comment)

    def start_figure(self, comment=None):
        if comment:
            self.comment(comment, False)
        self.fp.write("verbatimtex\n")
        self.fp.write("%&latex\n")
        self.fp.write("\\documentclass{article}\n")
        self.fp.write("\\begin{document}\n")
        self.fp.write("etex\n\n")
        self.fp.write("beginfig(1);\n")

    def end_figure(self):
        for d in self.delayed:
            self.fp.write(d)
        self.fp.write("\nendfig;\n")
        self.fp.write("end;\n")
        self.fp.close()

    def comment(self, comment, prefix_newline=True):
        if prefix_newline:
            s = "\n"
        else:
            s = ""
        s += "% {0}\n".format(comment)
        self.fp.write(s)

    @staticmethod
    def point_to_coordinates(p):
        return "({0}mm,{1}mm)".format(p.x, p.y)

    def draw_rectange(self, p1, p2, color="black", linewidth=0.5):
        c1 = self.point_to_coordinates(p1)
        c2 = self.point_to_coordinates(Point(p1.x, p2.y))
        c3 = self.point_to_coordinates(p2)
        c4 = self.point_to_coordinates(Point(p2.x, p1.y))
        s = "draw {0}--{1}--{2}--{3}--cycle withcolor {4} withpen pencircle scaled {5}pt;\n".format(c1, c2, c3, c4, color, linewidth)
        self.fp.write(s)

    def draw_line(self, p1, p2, color="black", linewidth=0.5, dotted=False, delay_write=False):
        # dotted: dashed withdots scaled 0.5
        c1 = self.point_to_coordinates(p1)
        c2 = self.point_to_coordinates(p2)
        s = "draw {0}--{1} withcolor {2} withpen pencircle scaled {3}pt".format(c1, c2, color, linewidth)
        if dotted:
            s += " dashed withdots scaled 0.5"
        s += ";\n"
        if delay_write:
            self.delayed.append(s)
        else:
            self.fp.write(s)

    def draw_polygon(self, points, color="black", linewidth=0.5, closed=True, dotted=False, delay_write=False):
        s = "draw "
        for p in points:
            c1 = self.point_to_coordinates(p)
            s += "{0}--".format(c1)
        if closed:
            s+="{0}".format(self.point_to_coordinates(points[0]))
        else:
            s = s[:-2]
        s += " withcolor {0} withpen pencircle scaled {1}pt".format(color, linewidth)
        if dotted:
            s += " dashed withdots scaled {0}".format(linewidth)
        s += ";\n"
        if delay_write:
            self.delayed.append(s)
        else:
            self.fp.write(s)

    def draw_point(self, p, size, color="black"):
        c = self.point_to_coordinates(p)
        s = "draw {0} withcolor {1} withpen pencircle scaled {2}mm;\n".format(c, color, size)
        self.fp.write(s)

    def draw_circle(self, p, radius, color="black", linewidth=0.5):
        c = self.point_to_coordinates(p)
        self.fp.write("draw fullcircle scaled {0}mm shifted {1} withcolor {2} withpen pencircle scaled {3}pt;\n".format(2*radius, c, color, linewidth))

    def draw_text(self, p, text, pos, size="tiny", scale=None, angle=None, delay_write=False):
        o = self.point_to_coordinates(Point(0, 0))
        c = self.point_to_coordinates(p)

        s = "label.{0}(btex \\{1} {2} etex".format(pos, size, text)
        if scale:
            s += " scaled {1}".format(scale)
        s += ", {0})".format(o)

        if angle:
            s += " rotated {0}".format(angle)
        s += " shifted {0};\n".format(c)

        if delay_write:
            self.delayed.append(s)
        else:
            self.fp.write(s)

    def clip(self, p1, p2):
        c1 = self.point_to_coordinates(p1)
        c2 = self.point_to_coordinates(Point(p1.x, p2.y))
        c3 = self.point_to_coordinates(p2)
        c4 = self.point_to_coordinates(Point(p2.x, p1.y))
        self.fp.write("path b;\n")
        self.fp.write("b := {0}--{1}--{2}--{3}--cycle;\n".format(c1, c2, c3, c4))
        self.fp.write("clip currentpicture to b;\n")

    @staticmethod
    def render(filename):
        subprocess.Popen(["mpost", "map"], cwd="mpost").wait()
        subprocess.Popen(["mptopdf map.1"], shell=True, cwd="mpost").wait()
        shutil.move("mpost/map-1.pdf", filename)
        subprocess.Popen(["open", filename]).wait()
