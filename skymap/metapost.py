import os
import subprocess
import shutil

from geometry import Point


# Set the path for metapost
os.environ['PATH'] = "/Library/TeX/texbin:"+os.environ['PATH']


class DrawError(Exception):
    pass


class MetaPostFigure(object):
    def __init__(self, name, comment=None):
        self.name = name
        if not os.path.exists("mpost"):
            os.makedirs("mpost")
        self.fp = open("mpost/{0}.mp".format(name), "w")
        self.delayed = []
        self.start_figure(comment)

    def start_figure(self, comment=None):
        if comment:
            self.comment(comment, False)
        self.fp.write("verbatimtex\n")
        self.fp.write("%&latex\n")
        self.fp.write("\\documentclass{article}\n")
        self.fp.write("\\usepackage[default]{sourcesanspro}\n")
        self.fp.write("\\usepackage[T1]{fontenc}\n")
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

    def draw_rectangle(self, p1, p2, color="black", linewidth=0.5):
        c1 = self.point_to_coordinates(p1)
        c2 = self.point_to_coordinates(Point(p1.x, p2.y))
        c3 = self.point_to_coordinates(p2)
        c4 = self.point_to_coordinates(Point(p2.x, p1.y))
        path = "{0}--{1}--{2}--{3}--cycle".format(c1, c2, c3, c4)
        self.draw_path(path, color=color, linewidth=linewidth)

    def draw_line(self, line, color="black", linewidth=0.5, dotted=False, delay_write=False):
        if not hasattr(line, "p1") or not hasattr(line, "p2"):
            raise DrawError
        c1 = self.point_to_coordinates(line.p1)
        c2 = self.point_to_coordinates(line.p2)
        path = "{0}--{1}".format(c1, c2)

        self.draw_path(path, color=color, linewidth=linewidth, dotted=dotted, delay_write=delay_write)

    def draw_polygon(self, polygon, color="black", linewidth=0.5, dashed=False, dotted=False, delay_write=False):
        path = ""
        for p in polygon.points:
            c1 = self.point_to_coordinates(p)
            path += "{0}--".format(c1)
        if polygon.closed:
            path += "{0}".format(self.point_to_coordinates(polygon.points[0]))
        else:
            path = path[:-2]
        self.draw_path(path, color=color, linewidth=linewidth, dotted=dotted, dashed=dashed, delay_write=delay_write)

    def fill_path(self, path, color, delay_write=False):
        s = "fill "
        s += path
        s += " withcolor {0}".format(color)
        s += ";\n"
        if delay_write:
            self.delayed.append(s)
        else:
            self.fp.write(s)

    def draw_path(self, path, color="black", linewidth=0.5, dashed=False, dotted=False, delay_write=False):
        s = "draw "
        s += path
        s += " withcolor {0} withpen pencircle scaled {1}pt".format(color, linewidth)
        if dotted:
            s += " dashed withdots scaled {0}".format(linewidth)
        if dashed:
            s += " dashed evenly scaled {0}".format(linewidth)
        s += ";\n"
        if delay_write:
            self.delayed.append(s)
        else:
            self.fp.write(s)

    def draw_curve(self, points, closed=False, color="black", linewidth=0.5, dashed=False, dotted=False, delay_write=False):
        path = ""
        for p in points:
            c1 = self.point_to_coordinates(p)
            path += "{0}..".format(c1)
        if closed:
            path += "cycle"
        else:
            path = path[:-2]
        self.draw_path(path, color=color, linewidth=linewidth, dashed=dashed, dotted=dotted, delay_write=delay_write)

    def fill_curve(self, curve, color="black", delay_write=False):
        if curve[0] == curve[-1]:
            curve = curve[:-1]
        path = ""
        for p in curve:
            c1 = self.point_to_coordinates(p)
            path += "{0}..".format(c1)
        path = path[:-2]
        path += "..cycle"
        self.fill_path(path, color=color, delay_write=delay_write)

    def draw_connected_curves(self, curves, color="black", linewidth=0.5, dashed=False, dotted=False, delay_write=False):
        path = ""
        for c in curves:
            for p in c:
                pp = self.point_to_coordinates(p)
                path += "{0}..".format(pp)
            path = path[:-2] + "--"
        path = path[:-2]
        #path += "cycle"
        self.draw_path(path, color=color, linewidth=linewidth, dashed=dashed, dotted=dotted, delay_write=delay_write)

    def fill_connected_curves(self, curves, color="black", delay_write=False):
        path = ""
        for c in curves:
            for p in c:
                pp = self.point_to_coordinates(p)
                path += "{0}..".format(pp)
            path = path[:-2] + "--"
        path += "cycle"
        self.fill_path(path, color=color, delay_write=delay_write)

    def draw_point(self, p, size, color="black"):
        c = self.point_to_coordinates(p)
        s = "draw {0} withcolor {1} withpen pencircle scaled {2}mm;\n".format(c, color, size)
        self.fp.write(s)

    def draw_circle(self, circle, color="black", linewidth=0.5, dotted=False, dashed=False, delay_write=False):
        if not hasattr(circle, "center") or not hasattr(circle, "radius"):
            raise DrawError
        c = self.point_to_coordinates(circle.center)
        path = "fullcircle scaled {0}mm shifted {1}".format(2*circle.radius, c)
        self.draw_path(path, color=color, linewidth=linewidth, dotted=dotted, dashed=dashed, delay_write=delay_write)

    def draw_arc(self, arc, color="black", linewidth=0.5, dotted=False, delay_write=False):
        if not hasattr(arc, "center") or not hasattr(arc, "radius") or not hasattr(arc, "start_mp"):
            raise DrawError
        c = self.point_to_coordinates(arc.center)
        path = "subpath ({}, {}) of fullcircle scaled {}mm shifted {}".format(arc.start_mp, arc.stop_mp, 2*arc.radius, c)
        self.draw_path(path, color=color, linewidth=linewidth, dotted=dotted, delay_write=delay_write)

    def draw_text(self, p, text, pos, size="tiny", scale=None, angle=None, delay_write=False):
        o = self.point_to_coordinates(Point(0, 0))
        c = self.point_to_coordinates(p)

        s = "label.{0}(btex \\{1} {2} etex".format(pos, size, text)
        if scale:
            s += " scaled {0}".format(scale)
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

    def render(self, filename=None, open=True):
        #subprocess.Popen(["mpost", self.name+".mp"], cwd="mpost").wait()
        subprocess.check_output(["mpost", self.name + ".mp"], cwd="mpost")
        if filename:
            subprocess.Popen(["mptopdf {0}.1".format(self.name)], shell=True, cwd="mpost").wait()
            folder = os.path.dirname(filename)
            if folder and not os.path.exists(folder):
                os.makedirs(folder)
            shutil.move("mpost/{0}-1.pdf".format(self.name), filename)
            if open:
                subprocess.Popen(["open", filename]).wait()

    def bounding_box(self):
        self.end_figure()
        self.render()
        fpath = os.path.join("mpost", "{0}.1".format(self.name))
        with open(fpath, "r") as fp:
            lines = fp.readlines()
        for l in lines:
            if l.startswith("%%HiResBoundingBox:"):
                bb = [(2.54 / 72) * float(x) for x in l.split(":")[-1].split()]
                return bb
        return None

    def bounding_box_size(self):
        bb = self.bounding_box()
        return bb[2]-bb[0], bb[3]-bb[1]