"""
Tikz figure interface.
"""
import os
import sys
import platform
import logging
import subprocess
import shutil
import jinja2
import io

from skymap.tikz import PaperSize, FontSize, PaperMargin


BASEDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX_OUTPUT_FOLDER = os.path.join(BASEDIR, "temp")
JINJA_TEMPLATE_FOLDER = os.path.join(BASEDIR, "skymap", "tikz", "templates")
if platform.system() == "Darwin":
    os.environ["PATH"] = "/Library/TeX/texbin:" + os.environ["PATH"]


class Tikz(object):
    """
    Tikz document class.

    Args:
        name (str): the base name for the tex and pdf files
        papersize (skymap.tikz.Papersize): PaperSize instance indicating the page dimensions
        margins (skymap.tikz.PaperMargin): PaperMargin instance describing the margins to use
        normalsize (int): the standard fontsize to use
    """

    def __init__(
        self,
        name,
        papersize=PaperSize(),
        margins=PaperMargin(),
        normalsize=11,
        template=None,
    ):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        self.name = name
        self.papersize = papersize
        self.margins = margins
        self.fontsizes = FontSize(normalsize)
        self.template = template or "tikz_base.j2"

        # Landmark points
        self.llcorner = Point(self.margins.l, self.margins.b)
        self.ulcorner = Point(self.margins.l, self.papersize.height - self.margins.t)
        self.urcorner = Point(
            self.papersize.width - self.margins.r,
            self.papersize.height - self.margins.t,
        )
        self.lrcorner = Point(self.papersize.width - self.margins.r, self.margins.b)
        self.center = 0.5 * (self.llcorner + self.urcorner)

        self.texfile_name = "{0}.tex".format(self.name)
        self.texstring = ""
        self.delayed = []
        self.current_picture = None
        self.started = False
        self.finished = False

        self.j2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(JINJA_TEMPLATE_FOLDER), trim_blocks=True
        )

    def append(self, s):
        """Append the given string to the current document."""
        self.texstring += s

    def write_header(self):
        """Add the header to to the current document."""
        self.texstring += "{{% extends '{}' %}}\n".format(self.template)
        self.texstring += "\n"
        self.texstring += "{% block content %}\n"
        self.texstring += "{{ super() }}\n"

    def write_footer(self):
        """Add the footer to the current document."""
        if self.current_picture is not None:
            self.current_picture.close(self.append)

        self.texstring += "{% endblock %}\n"

    def start(self):
        """Start the document."""
        self.texstring = ""
        self.write_header()
        self.started = True

    def finish(self):
        """End the document."""
        self.write_footer()
        self.finished = True

    # Drawing functions
    def comment(self, comment, prefix_newline=True):
        """Add a comment to the document.

        Args:
            comment: the comment to add
            prefix_newline: whether to include a newline before the comment
        """
        if prefix_newline:
            s = "\n"
        else:
            s = ""
        if comment:
            s += "% {0}\n".format(comment)
        self.texstring += s

    def add(self, picture):
        """Add the given picture to the document."""
        if not self.started:
            self.start()

        if self.current_picture is not None:
            self.current_picture.close(self.append)

        self.current_picture = picture

    def render(self, filepath=None, open_pdf=True, extra_context=None, verbose=False):
        """Render the current document as a PDF file.

        Args:
            filepath: where to save the PDF
            open_pdf: whether to open the PDF when ready
            extra_context: dictionary containing extra context items for the jinja2 template
            verbose: whether to log all actions
        """
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
            "normal_pointsize": self.fontsizes["normalsize"],
        }
        if extra_context:
            context.update(extra_context)

        rendered_template = template.render(context)
        with io.open(
            os.path.join(TEX_OUTPUT_FOLDER, self.texfile_name),
            mode="w",
            encoding="utf-8",
        ) as fp:
            fp.write(rendered_template)

        # Run XeLaTeX
        if verbose:
            self.logger.info(
                f"Rendering {filepath or os.path.join(TEX_OUTPUT_FOLDER, self.texfile_name)}"
            )

        xelatex_error = False
        try:
            subprocess.check_output(
                [
                    "xelatex",
                    "-halt-on-error",
                    "-interaction",
                    "batchmode",
                    self.texfile_name,
                ],
                cwd=TEX_OUTPUT_FOLDER,
            )
            subprocess.check_output(
                [
                    "xelatex",
                    "-halt-on-error",
                    "-interaction",
                    "batchmode",
                    self.texfile_name,
                ],
                cwd=TEX_OUTPUT_FOLDER,
            )
        except subprocess.CalledProcessError as exc:
            self.logger.error("XeLaTeX compilation failed")
            self.logger.error("=" * 60)
            xelatex_error = exc

        # Open log file
        with open(os.path.join(TEX_OUTPUT_FOLDER, self.name + ".log"), "r") as fp:
            output = fp.read()
        if xelatex_error:
            self.logger.debug(output)
            raise xelatex_error

        # Move output file
        if filepath:
            folder = os.path.dirname(filepath)
            if folder and not os.path.exists(folder):
                os.makedirs(folder)
            shutil.move(
                os.path.join(TEX_OUTPUT_FOLDER, "{0}.pdf".format(self.name)), filepath
            )
            if open_pdf:
                subprocess.Popen(["open", filepath]).wait()

        return output


if __name__ == "__main__":
    from skymap.tikz import TikzPicture
    from skymap.geometry import Circle, Rectangle, Point

    t = Tikz("tizk_test1")
    p = TikzPicture(t, Point(20, 20), Point(190, 277))

    p.draw_circle(Circle(Point(85, 128.5), 30))
    p.draw_rectangle(Rectangle(Point(55, 98.5), Point(115, 158.5)))
    t.render(verbose=True)
