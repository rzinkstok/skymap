"""
Tikz figure interface.
"""
import os
import subprocess
import shutil
import jinja2
import io

from skymap.geometry import Point
from skymap.tikz import PaperSize, FontSize, PaperMargin


BASEDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX_OUTPUT_FOLDER = os.path.join(BASEDIR, "temp")
JINJA_TEMPLATE_FOLDER = os.path.join(BASEDIR, "skymap", "tikz", "templates")
os.environ['PATH'] = "/Library/TeX/texbin:"+os.environ['PATH']


class Tikz(object):
    """
    Tikz document class.

    Args:
        name (str): the base name for the tex and pdf files
        papersize (skymap.tikz.Papersize): PaperSize instance indicating the page dimensions
        margins (skymap.tikz.PaperMargin): PaperMargin instance describing the margins to use
        normalsize (int): the standard fontsize to use
    """
    def __init__(self, name, papersize=PaperSize(), margins=PaperMargin(), normalsize=11, template=None):
        self.name = name
        self.papersize = papersize
        self.margins = margins
        self.fontsizes = FontSize(normalsize)
        self.template = template or "tikz_base.j2"

        # Landmark points
        self.llcorner = Point(self.margins.l, self.margins.b)
        self.ulcorner = Point(self.margins.l, self.papersize.height - self.margins.t)
        self.urcorner = Point(self.papersize.width - self.margins.r, self.papersize.height - self.margins.t)
        self.lrcorner = Point(self.papersize.width - self.margins.r, self.margins.b)
        self.center = 0.5*(self.llcorner + self.urcorner)

        self.texfile_name = "{0}.tex".format(self.name)
        self.texstring = ""
        self.delayed = []
        self.current_picture = None
        self.started = False
        self.finished = False

        self.j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(JINJA_TEMPLATE_FOLDER), trim_blocks=True)

    def append(self, s):
        self.texstring += s

    def write_header(self):
        self.texstring += "{{% extends '{}' %}}\n".format(self.template)
        self.texstring += "\n"
        self.texstring += "{% block content %}\n"
        self.texstring += "{{ super() }}\n"

    def write_footer(self):
        if self.current_picture is not None:
            self.current_picture.close(self.append)

        self.texstring += "{% endblock %}\n"

    def start(self):
        self.texstring = ""
        self.write_header()
        self.started = True

    def finish(self):
        self.write_footer()
        self.finished = True

    # Drawing functions
    def comment(self, comment, prefix_newline=True):
        if prefix_newline:
            s = "\n"
        else:
            s = ""
        if comment:
            s += "% {0}\n".format(comment)
        self.texstring += s

    def add(self, picture):
        if not self.started:
            self.start()

        if self.current_picture is not None:
            self.current_picture.close(self.append)

        self.current_picture = picture

    def render(self, filepath=None, open=True, extra_context=None):
        if not self.started:
            self.start()

        if self.current_picture and not self.current_picture.opened:
            self.current_picture.open()

        if self.current_picture and not self.current_picture.closed:
            self.current_picture.close(self.append)

        if not self.finished:
            self.finish()

        # Render template
        if not os.path.exists(TEX_OUTPUT_FOLDER):
            os.makedirs(TEX_OUTPUT_FOLDER)

        template = self.j2_env.from_string(self.texstring)

        context = {
            "paperwidth": self.papersize.width,
            "paperheight": self.papersize.height,
            "fontsizes": self.fontsizes,
            "normal_pointsize": self.fontsizes['normalsize']
        }
        if extra_context:
            context.update(extra_context)

        rendered_template = template.render(context)
        with io.open(os.path.join(TEX_OUTPUT_FOLDER, self.texfile_name), mode="w", encoding="utf-8") as fp:
            fp.write(rendered_template)

        # Run XeLaTeX
        print "Rendering", filepath or os.path.join(TEX_OUTPUT_FOLDER, self.texfile_name)
        subprocess.check_output(["xelatex", self.texfile_name], cwd=TEX_OUTPUT_FOLDER)
        output = subprocess.check_output(["xelatex", self.texfile_name], cwd=TEX_OUTPUT_FOLDER)

        # Move output file
        if filepath:
            folder = os.path.dirname(filepath)
            if folder and not os.path.exists(folder):
                os.makedirs(folder)
            shutil.move(os.path.join(TEX_OUTPUT_FOLDER, "{0}.pdf".format(self.name)), filepath)
            if open:
                subprocess.Popen(["open", filepath]).wait()

        return output