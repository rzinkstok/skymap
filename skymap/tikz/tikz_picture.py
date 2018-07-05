from contextlib import contextmanager
from skymap.geometry import Point, Rectangle


class DrawError(Exception):
    pass


class TikzPicture(object):
    """Part of the Tikz page that can be used for drawing.

    It is enclosed by an optional box, and has its own origin.

    Args:
        tikz (skymap.tikz.Tikz): the Tikz object to add the TikzPicture to
        p1 (skymap.geometry.Point): the lower left corner of the picture, in paper coordinates
        p2 (skymap.geometry.Point): the upper right corner of the picture, in paper coordinates
        origin (skymap.geometry.Point): the location of the origin of the picture's coordinate
            system, in paper coordinates
        boxed (bool): whether to draw a box around the picture
    """
    def __init__(self, tikz, p1, p2, origin=None, boxed=True):
        self.p1 = p1
        self.p2 = p2

        if origin is None:
            self.set_origin(p1)
        else:
            self.set_origin(origin)

        self.boxed = boxed

        self.width = p2.x - p1.x
        self.height = p2.y - p1.y

        self.texstring = ""
        self._dotted = False
        self._dashed = False
        self.linewidth = 0.5
        self.color = "black"
        self.opened = False
        self.closed = False

        tikz.add(self)

    def set_origin(self, origin):
        """
        Sets the location of the origin of the coordinate system for the picture.
        The minimum and maximum x and y values for the picture, as well as the bounding box, are determined as well.

        Args:
            origin (skymap.geometry.Point): the location in absolute paper coordinates
        """
        self.origin = origin
        self.minx = self.p1.x - self.origin.x
        self.maxx = self.p2.x - self.origin.x
        self.miny = self.p1.y - self.origin.y
        self.maxy = self.p2.y - self.origin.y

        self.bounding_box = Rectangle(Point(self.minx, self.miny), Point(self.maxx, self.maxy))

    def open(self):
        if self.opened:
            return
        if self.closed:
            raise RuntimeError("You cannot re-open a TikzPicture")

        if self.origin != Point(0, 0):
            shift = "{([shift={" + self.point_to_coordinates(self.origin) + "}]current page.south west)}"
        else:
            shift = "{(current page.south west)}"

        self.texstring += "\\begin{{tikzpicture}}[remember picture, overlay, shift={0}, every node/.style={{inner sep=0mm, outer sep=0mm, minimum size=0mm, text height=\\normaltextheight, text depth=\\normaltextdepth}}]\n".format(shift)
        self.opened = True

        if self.boxed:
            self.draw_bounding_box()

    def close(self, add_to_tikz_string):
        if not self.opened or self.closed:
            return

        self.comment("")
        self.texstring += "\\end{tikzpicture}\n\n"
        add_to_tikz_string(self.texstring)
        self.closed = True

    @contextmanager
    def clip(self, path=None):
        """
        Context manager for clipping the enclosed drawing actions to the given path.

        Args:
            path: the clipping path to use
        """
        if path is None:
            path = self.bounding_box.path
        self.comment("Clipping")
        self.texstring += "\\begin{scope}\n"
        self.texstring += "\\clip {};\n".format(path)
        yield
        self.comment("End clipping")
        self.texstring += "\\end{scope}\n"

    @staticmethod
    def point_to_coordinates(p):
        """Converts the given point to Tikz coordinates.

        Args:
            p (skymap.geometry.Point): the point to convert

        Returns:
            str: the Tikz point representation
        """
        x = p.x
        y = p.y
        if abs(x) < 1e-4:
            x = 0.0
        if abs(y) < 1e-4:
            y = 0.0

        return "({0}mm,{1}mm)".format(x, y)

    def path(self, points, cycle=True):
        """Builds a Tikz path from the given list of points.

        Args:
            points (list): the points of the path
            cycle (bool): whether to link the last point to the first
        Returns:
            str: the Tikz path representation
        """
        path = "--".join([self.point_to_coordinates(p) for p in points])
        if cycle:
            path += "--cycle"
        return path

    def comment(self, comment, prefix_newline=True):
        """Adds a comment to the Tikz file."""
        if prefix_newline:
            s = "\n"
        else:
            s = ""
        if comment:
            s += "% {0}\n".format(comment)
        self.texstring += s

    # Draw options
    @property
    def dotted(self):
        return self._dotted

    @dotted.setter
    def dotted(self, value):
        self._dashed = not value
        self._dotted = value

    @property
    def dashed(self):
        return self._dashed

    @dashed.setter
    def dashed(self, value):
        self._dotted = not value
        self._dashed = value

    def solid_pen(self):
        self.dashed = False
        self.dotted = False

    def dotted_pen(self):
        self.dotted = True

    def dashed_pen(self):
        self.dashed = True

    def draw_options(self):
        options = "["
        options += "line width={}pt,".format(self.linewidth)
        options += self.color
        if self._dotted:
            options += ",dotted"
        elif self._dashed:
            options += ",dashed"
        options += "]"
        return options

    # Drawing various objects

    def draw_line(self, line, delay_write=False):
        self.open()
        if not hasattr(line, "p1") or not hasattr(line, "p2"):
            raise DrawError
        p1 = self.point_to_coordinates(line.p1)
        p2 = self.point_to_coordinates(line.p2)
        opts = self.draw_options()
        self.texstring += "\\draw {} {}--{};\n".format(opts, p1, p2)

    def draw_path(self, path, delay_write=False):
        self.open()
        opts = self.draw_options()
        self.texstring += "\\draw {} {};\n".format(opts, path)

    def draw_polygon(self, points, cycle=False, delay_write=False):
        self.open()
        opts = self.draw_options()
        cmd = "\\draw {}".format(opts)
        for p in points:
            cmd += self.point_to_coordinates(p)
            cmd += "--"
        if cycle:
            cmd += "cycle;\n"
        else:
            cmd = cmd[:-2] + ";\n"
        self.texstring += cmd

    def draw_rectangle(self, rectangle, delay_write=False):
        self.open()
        if not hasattr(rectangle, "p1") or not hasattr(rectangle, "p2"):
            raise DrawError
        p1 = self.point_to_coordinates(rectangle.p1)
        p2 = self.point_to_coordinates(rectangle.p2)
        opts = self.draw_options()
        self.texstring += "\\draw {} {} rectangle {};\n".format(opts, p1, p2)

    def draw_circle(self, circle, delay_write=False):
        self.open()
        if not hasattr(circle, "center") or not hasattr(circle, "radius"):
            raise DrawError
        c = self.point_to_coordinates(circle.center)
        opts = self.draw_options()
        self.texstring += "\\draw {} {} circle ({}mm);\n".format(opts, c, circle.radius)

    def draw_arc(self, arc, delay_write=False):
        self.open()
        if not hasattr(arc, "center") or not hasattr(arc, "radius") or not hasattr(arc, "start_angle") or not hasattr(arc, "stop_angle"):
            raise DrawError
        if arc.radius > 2000:
            self.draw_interpolated_arc(arc, delay_write)
            return
        c = "([shift=({}:{}mm)]".format(arc.start_angle, arc.radius)
        c += self.point_to_coordinates(arc.center)[1:]
        opts = self.draw_options()
        self.texstring += "\\draw {} {} arc ({}:{}:{}mm);\n".format(opts, c, arc.start_angle, arc.stop_angle, arc.radius)

    def draw_interpolated_arc(self, arc, delay_write=False):
        self.open()
        self.draw_polygon(arc.interpolated_points(), delay_write=delay_write)

    def draw_bounding_box(self, linewidth=0.5):
        self.open()
        old_linewidth = self.linewidth
        self.linewidth = linewidth
        self.draw_rectangle(self.bounding_box)
        self.linewidth = old_linewidth

    def draw_label(self, label, delay_write=False):
        self.open()
        """pos can be a position string or an angle float"""
        p = self.point_to_coordinates(label.point)

        textheight = "\\{}textheight".format(label.fontsize)
        textdepth = "\\{}textdepth".format(label.fontsize)

        if label.fill:
            labelfill = ", fill={}".format(label.fill)
        else:
            labelfill = ""

        text = "{{{}:{{\\{} {}}}}}".format(label.position, label.fontsize, label.text)
        text = "{{[label distance=0mm, rotate={}, text height={} mm, text depth={} mm{}, text={}]".format(label.angle, textheight, textdepth, labelfill, label.color) + text[1:]

        self.texstring += "\\node at {} [text height=0mm, text depth=0mm, label={}] {{}};\n".format(p, text)

    def fill_circle(self, point, radius):
        self.open()
        p = self.point_to_coordinates(point)
        self.texstring += "\\fill [{}] {} circle ({}mm);\n".format(self.color, p, radius)

    def fill_rectangle(self, rectangle):
        self.open()
        p1 = self.point_to_coordinates(rectangle.p1)
        p2 = self.point_to_coordinates(rectangle.p2)
        self.texstring += "\\fill [{}] {} rectangle {};\n".format(self.color, p1, p2)