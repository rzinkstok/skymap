import os
import math
import subprocess
import shutil
from contextlib import contextmanager

from skymap.geometry import Point, Rectangle


BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_OUTPUT_FOLDER = os.path.join(BASEDIR, "output")
print "Basedir:", BASEDIR
print "Texfolder:", TEX_OUTPUT_FOLDER

PAPERSIZES = {
    "A4": (210.0, 297.0),
    "A3": (297.0, 420.0),
    "A2": (420.0, 594.0),
}

FONTSIZES = {
    10: {
        'nano': 3,
        'miniscule': 4,
        'tiny': 5,
        'scriptsize': 7,
        'footnotesize': 8,
        'small': 9,
        'normalsize': 10,
        'large': 12,
        'Large': 14.4,
        'LARGE': 17.28,
        'huge': 20.74,
        'Huge': 24.88,
        'HUGE': 45,
    },
    11: {
        'nano': 4,
        'miniscule': 5,
        'tiny': 6,
        'scriptsize': 8,
        'footnotesize': 9,
        'small': 10,
        'normalsize': 10.95,
        'large': 12,
        'Large': 14.4,
        'LARGE': 17.28,
        'huge': 20.74,
        'Huge': 24.88,
    },
    12: {
        'nano': 4,
        'miniscule': 5,
        'tiny': 6,
        'scriptsize': 8,
        'footnotesize': 10,
        'small': 10.95,
        'normalsize': 12,
        'large': 14.4,
        'Large': 17.28,
        'LARGE': 20.74,
        'huge': 24.88,
        'Huge': 24.88,
    }
}



os.environ['PATH'] = "/Library/TeX/texbin:"+os.environ['PATH']


class DrawError(Exception):
    pass


class TikzFigure(object):
    def __init__(self, name, papersize=PAPERSIZES["A4"], left_margin=20, right_margin=20, top_margin=20, bottom_margin=20, landscape=False, fontsize=11):
        self.name = name
        self.papersize = papersize
        self.landscape = landscape
        if landscape:
            self.papersize = (self.papersize[1], self.papersize[0])
        print self.papersize

        self.left_margin = left_margin
        self.right_margin = right_margin
        self.top_margin = top_margin
        self.bottom_margin = bottom_margin
        self.llcorner = Point(self.left_margin, self.bottom_margin)
        self.ulcorner = Point(self.left_margin, self.papersize[1] - self.top_margin)
        self.urcorner = Point(self.papersize[0] - self.right_margin, self.papersize[1] - self.top_margin)
        self.lrcorner = Point(self.papersize[0] - self.right_margin, self.bottom_margin)
        self.center = 0.5*(self.llcorner + self.urcorner)

        self.fontsize = fontsize
        self.fontsizes = FONTSIZES[fontsize]
        if not os.path.exists(TEX_OUTPUT_FOLDER):
            os.makedirs(TEX_OUTPUT_FOLDER)
        self.fp = open(os.path.join(TEX_OUTPUT_FOLDER, "{0}.tex".format(name)), "w")

        self.delayed = []
        self.current_drawing_area = None
        self.closed = False
        self.start_figure()

    def start_figure(self):
        if self.landscape:
            self.fp.write("\\documentclass[landscape,{}pt]{{article}}\n".format(self.fontsize))
        else:
            self.fp.write("\\documentclass[{}pt]{{article}}\n".format(self.fontsize))
        #self.fp.write("\\usepackage[{}paper]{{geometry}}\n".format(self.papersize.lower()))
        self.fp.write("\\usepackage[paperwidth={}mm,paperheight={}mm]{{geometry}}\n".format(self.papersize[0], self.papersize[1]))
        self.fp.write("\\usepackage{mathspec}\n")
        self.fp.write("\\usepackage{tikz}\n")
        self.fp.write("\\usetikzlibrary{positioning}\n")
        self.fp.write("\\setallmainfonts[Numbers={Lining,Proportional}]{Myriad Pro}\n")

        self.fp.write("\n")
        self.fp.write("\\makeatletter\n")
        self.fp.write("\\ifcase \\@ptsize \\relax% 10pt\n")
        self.fp.write("    \\newcommand{\\HUGE}{\\@setfontsize\\HUGE{45}{50}}\n")
        self.fp.write("    \\newcommand{\\miniscule}{\\@setfontsize\\miniscule{4}{5}}% \\tiny: 5/6\n")
        self.fp.write("    \\newcommand{\\nano}{\\@setfontsize\\nano{3}{4}}% \\tiny: 5/6\n")
        self.fp.write("\\or% 11pt\n")
        self.fp.write("    \\newcommand{\\miniscule}{\\@setfontsize\\miniscule{5}{6}}% \\tiny: 6/7\n")
        self.fp.write("    \\newcommand{\\nano}{\\@setfontsize\\nano{4}{5}}% \\tiny: 6/7\n")
        self.fp.write("\\or% 12pt\n")
        self.fp.write("    \\newcommand{\\miniscule}{\\@setfontsize\\miniscule{5}{6}}% \\tiny: 6/7\n")
        self.fp.write("    \\newcommand{\\nano}{\\@setfontsize\\nano{4}{5}}% \\tiny: 6/7\n")
        self.fp.write("\\fi\n")
        self.fp.write("\\makeatother\n")

        self.fp.write("\n")
        self.fp.write("\\begin{document}\n")
        self.fp.write("\\pagenumbering{gobble}\n")

        self.fp.write("\n")
        self.fp.write("\\newcommand\\normaltextheightem{0.75} % Text height for normalsize\n")
        self.fp.write("\\newcommand\\normaltextdepthem{0.24} % Text depth for normalsize\n")
        self.fp.write("\\pgfmathsetmacro{\\normaltextheight}{\\normaltextheightem em/1mm} % Converted to mm\n")
        self.fp.write("\\pgfmathsetmacro{\\normaltextdepth}{\\normaltextdepthem em/1mm} % Converted to mm\n")

        for fontsize, pointsize in self.fontsizes.items():
            self.fp.write("\\pgfmathsetmacro{{\\{}textheight}}{{{}*\\normaltextheight/{}}} % Text height for {} ({} pt)\n".format(fontsize, pointsize, self.fontsize, fontsize, pointsize))
            self.fp.write("\\pgfmathsetmacro{{\\{}textdepth}}{{{}*\\normaltextdepth/{}}} % Text depth for {} ({} pt)\n".format(fontsize, pointsize, self.fontsize, fontsize, pointsize))
        self.fp.write("\n")

    def close(self):
        if self.current_drawing_area is not None:
            self.current_drawing_area.close()
        self.fp.write("\\end{document}\n")
        self.fp.close()

    def comment(self, comment, prefix_newline=True):
        if prefix_newline:
            s = "\n"
        else:
            s = ""
        if comment:
            s += "% {0}\n".format(comment)
        self.fp.write(s)

    def add(self, drawing_area):
        if self.current_drawing_area is not None:
            self.current_drawing_area.close()
        self.current_drawing_area = drawing_area
        drawing_area.set_figure(self.fp)

    def render(self, filepath=None, open=True):
        if not self.closed:
            self.close()
        subprocess.check_output(["xelatex", self.name + ".tex"], cwd=TEX_OUTPUT_FOLDER)
        subprocess.check_output(["xelatex", self.name + ".tex"], cwd=TEX_OUTPUT_FOLDER)
        if filepath:
            folder = os.path.dirname(filepath)
            if folder and not os.path.exists(folder):
                os.makedirs(folder)
            shutil.move(os.path.join(TEX_OUTPUT_FOLDER, "{0}.pdf".format(self.name)), filepath)
            if open:
                subprocess.Popen(["open", filepath]).wait()


class DrawingArea(object):
    def __init__(self, p1, p2, origin=None, box=True):
        self.p1 = p1
        self.p2 = p2
        self.current = True

        if origin is None:
            self.set_origin(p1)
        else:
            self.set_origin(origin)

        self.box = box

        self.width = p2.x - p1.x
        self.height = p2.y - p1.y

    def set_origin(self, origin):
        self.origin = origin
        self.minx = self.p1.x - self.origin.x
        self.maxx = self.p2.x - self.origin.x
        self.miny = self.p1.y - self.origin.y
        self.maxy = self.p2.y - self.origin.y

        self.bounding_box = Rectangle(Point(self.minx, self.miny), Point(self.maxx, self.maxy))

    def open(self):
        if self.origin != Point(0, 0):
            shift = "{([shift={" + self.point_to_coordinates(self.origin) + "}]current page.south west)}"
        else:
            shift = "{(current page.south west)}"

        self.fp.write("\\begin{{tikzpicture}}[remember picture, overlay, shift={0}, every node/.style={{inner sep=0mm, outer sep=0mm, minimum size=0mm, text height=\\normaltextheight, text depth=\\normaltextdepth}}]\n".format(shift))
        if self.box:
            self.draw_bounding_box()

    def close(self):
        self.comment("")
        self.fp.write("\\end{tikzpicture}\n\n")
        self.fp = None
        self.current = False

    def set_figure(self, fp):
        self.fp = fp
        self.open()

    @contextmanager
    def clip(self, path):
        self.comment("Clipping")
        self.fp.write("\\begin{scope}\n")
        self.fp.write("\\clip {};\n".format(path))
        yield
        self.comment("End clipping")
        self.fp.write("\\end{scope}\n")

    @staticmethod
    def point_to_coordinates(p):
        x = p.x
        y = p.y
        if abs(x) < 1e-4:
            x = 0.0
        if abs(y) < 1e-4:
            y = 0.0

        return "({0}mm,{1}mm)".format(x, y)

    def path(self, points, cycle=True):
        path = ""
        for p in points:
            path += self.point_to_coordinates(p)
            path += "--"
        if cycle:
            path += "cycle"
        else:
            path = path[:-2]
        return path

    def comment(self, comment, prefix_newline=True):
        if prefix_newline:
            s = "\n"
        else:
            s = ""
        if comment:
            s += "% {0}\n".format(comment)
        self.fp.write(s)

    def draw_options(self, linewidth, color, dotted, dashed):
        options = "["
        options += "line width={}pt,".format(linewidth)
        options += color
        if dotted:
            options += ",{}".format(dotted)
        elif dashed:
            options += ",{}".format(dashed)
        options += "]"
        return options

    def draw_line(self, line, color="black", linewidth=0.5, dotted=False, dashed=False, delay_write=False):
        if not hasattr(line, "p1") or not hasattr(line, "p2"):
            raise DrawError
        p1 = self.point_to_coordinates(line.p1)
        p2 = self.point_to_coordinates(line.p2)
        opts = self.draw_options(linewidth, color, dotted, dashed)
        self.fp.write("\\draw {} {}--{};\n".format(opts, p1, p2))

    def draw_path(self, path, color="black", linewidth=0.5, dotted=False, dashed=False, delay_write=False):
        opts = self.draw_options(linewidth, color, dotted, dashed)
        self.fp.write("\\draw {} {};\n".format(opts, path))

    def draw_polygon(self, points, cycle=False, color="black", linewidth=0.5, dotted=False, dashed=False, delay_write=False):
        opts = self.draw_options(linewidth, color, dotted, dashed)
        cmd = "\\draw {}".format(opts)
        for p in points:
            cmd += self.point_to_coordinates(p)
            cmd += "--"
        if cycle:
            cmd += "cycle;\n"
        else:
            cmd = cmd[:-2] + ";\n"
        self.fp.write(cmd)

    def draw_rectangle(self, rectangle, color="black", linewidth=0.5, dotted=False, dashed=False, delay_write=False):
        if not hasattr(rectangle, "p1") or not hasattr(rectangle, "p2"):
            raise DrawError
        p1 = self.point_to_coordinates(rectangle.p1)
        p2 = self.point_to_coordinates(rectangle.p2)
        opts = self.draw_options(linewidth, color, dotted, dashed)
        self.fp.write("\\draw {} {} rectangle {};\n".format(opts, p1, p2))

    def draw_circle(self, circle, color="black", linewidth=0.5, dotted=False, dashed=False, delay_write=False):
        if not hasattr(circle, "center") or not hasattr(circle, "radius"):
            raise DrawError
        c = self.point_to_coordinates(circle.center)
        opts = self.draw_options(linewidth, color, dotted, dashed)
        self.fp.write("\\draw {} {} circle ({}mm);\n".format(opts, c, circle.radius))

    def draw_arc(self, arc, color="black", linewidth=0.5, dotted=False, dashed=False, delay_write=False):
        if not hasattr(arc, "center") or not hasattr(arc, "radius") or not hasattr(arc, "start_angle") or not hasattr(arc, "stop_angle"):
            raise DrawError
        if arc.radius > 2000:
            self.draw_interpolated_arc(arc, color, linewidth, dotted, dashed, delay_write)
            return
        c = "([shift=({}:{}mm)]".format(arc.start_angle, arc.radius)
        c += self.point_to_coordinates(arc.center)[1:]
        opts = self.draw_options(linewidth, color, dotted, dashed)
        delta_angle = arc.stop_angle - arc.start_angle
        self.fp.write("\\draw {} {} arc ({}:{}:{}mm);\n".format(opts, c, arc.start_angle, arc.stop_angle, arc.radius))

    def draw_interpolated_arc(self, arc, color="black", linewidth=0.5, dotted=False, dashed=False, delay_write=False):
        self.draw_polygon(arc.interpolated_points(), color=color, linewidth=linewidth, dotted=dotted, dashed=dashed, delay_write=delay_write)

    def draw_bounding_box(self):
        self.draw_rectangle(self.bounding_box)

    def draw_label(self, label, delay_write=False):
        """pos can be a position string or an angle float"""
        p = self.point_to_coordinates(label.point)

        textheight = "\\{}textheight".format(label.fontsize)
        textdepth = "\\{}textdepth".format(label.fontsize)

        if label.fill:
            labelfill = ", fill={}".format(label.fill)
        else:
            labelfill = ""

        text = "{{{}:{{\\{} {}}}}}".format(label.position, label.fontsize, label.text)
        text = "{{[label distance=0mm, rotate={}, text height={} mm, text depth={} mm{}]".format(label.angle, textheight, textdepth, labelfill) + text[1:]

        self.fp.write("\\node at {} [text height=0mm, text depth=0mm, label={}] {{}};\n".format(p, text))

    def fill_circle(self, point, radius):
        p = self.point_to_coordinates(point)
        self.fp.write("\\fill {} circle ({}mm);\n".format(p, radius))