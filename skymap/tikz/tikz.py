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

from skymap.geometry import Point
from skymap.tikz import PaperSize, FontSize, PaperMargin

BASEDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX_OUTPUT_FOLDER = os.path.join(BASEDIR, "temp")
PDF_FOLDER = os.path.join(BASEDIR, "pdf")
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
        name="none",
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
        self.normalsize = normalsize
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

        # Usable size
        self.width = self.papersize.width - self.margins.l - self.margins.r
        self.height = self.papersize.height - self.margins.b - self.margins.t

        self.texfile_name = f"{self.name}.tex"
        self.delayed = []
        self.pictures = []

        # Header/footer
        self.header = (
            f"{{% extends '{self.template}' %}}\n\n"
            "{% block content %}\n"
            "{{ super() }}\n"
        )
        self.footer = "{% endblock %}\n"

        self.j2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(JINJA_TEMPLATE_FOLDER), trim_blocks=True
        )

    def add(self, picture):
        """Add the given picture to the document."""
        if self.pictures and not self.pictures[-1].closed:
            self.pictures[-1].close()

        self.pictures.append(picture)

    def new(self, name):
        return Tikz(name, self.papersize, self.margins, self.normalsize, self.template)

    def render(self, filepath=None, open_pdf=False, extra_context=None, verbose=False):
        """Render the current document as a PDF file.

        Args:
            filepath: where to save the PDF
            open_pdf: whether to open the PDF when ready
            extra_context: dictionary containing extra context items for the jinja2 template
            verbose: whether to log all actions
        """
        if self.pictures and not self.pictures[-1].opened:
            self.logger.info("Open")
            self.pictures[-1].open()

        if self.pictures and not self.pictures[-1].closed:
            self.logger.info("Close")
            self.pictures[-1].close()

        # Build the template souce string
        texstring = self.header
        for p in self.pictures:
            texstring += p.texstring
        texstring += self.footer

        # Render template
        if not os.path.exists(TEX_OUTPUT_FOLDER):
            os.makedirs(TEX_OUTPUT_FOLDER)

        template = self.j2_env.from_string(texstring)

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
            shutil.move(os.path.join(TEX_OUTPUT_FOLDER, f"{self.name}.pdf"), filepath)
            if open_pdf:
                subprocess.Popen(["open", filepath]).wait()

        return output


if __name__ == "__main__":
    from skymap.tikz import TikzPicture
    from skymap.geometry import Circle, Rectangle, Point

    t = Tikz("tizk_test1")
    with TikzPicture(t, Point(20, 20), Point(190, 277)) as p:
        p.draw_circle(Circle(Point(85, 128.5), 30))
        p.draw_rectangle(Rectangle(Point(55, 98.5), Point(115, 158.5)))
    t.render(verbose=True)
