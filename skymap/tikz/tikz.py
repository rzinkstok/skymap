import os
import subprocess
import shutil


from skymap.geometry import Point
from skymap.tikz import PaperSize, FontSize, PaperMargin


BASEDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX_OUTPUT_FOLDER = os.path.join(BASEDIR, "temp")
os.environ['PATH'] = "/Library/TeX/texbin:"+os.environ['PATH']


class Tikz(object):
    def __init__(self, name, papersize=PaperSize(), margins=PaperMargin(), normalsize=11):
        self.name = name
        self.papersize = papersize
        self.margins = margins
        self.fontsizes = FontSize(normalsize)

        # Landmark points
        self.llcorner = Point(self.margins.l, self.margins.b)
        self.ulcorner = Point(self.margins.l, self.papersize.height - self.margins.t)
        self.urcorner = Point(self.papersize.width - self.margins.r, self.papersize.height - self.margins.t)
        self.lrcorner = Point(self.papersize.width - self.margins.r, self.margins.b)
        self.center = 0.5*(self.llcorner + self.urcorner)

        self.texfile_name = "{0}.tex".format(self.name)
        self.texfile = None
        self.delayed = []
        self.current_picture = None
        self.started = False
        self.finished = False

    def open_file(self):
        if not os.path.exists(TEX_OUTPUT_FOLDER):
            os.makedirs(TEX_OUTPUT_FOLDER)
        self.texfile = open(os.path.join(TEX_OUTPUT_FOLDER, self.texfile_name), "w")

    def close_file(self):
        self.texfile.close()

    def write_header(self):
        if not self.texfile:
            return

        if self.papersize.landscape:
            self.texfile.write("\\documentclass[landscape,{}pt]{{article}}\n".format(self.fontsizes['normalsize']))
        else:
            self.texfile.write("\\documentclass[{}pt]{{article}}\n".format(self.fontsizes['normalsize']))
        self.texfile.write("\\usepackage[paperwidth={}mm,paperheight={}mm]{{geometry}}\n".format(self.papersize.width, self.papersize.height))
        self.texfile.write("\\usepackage{mathspec}\n")
        self.texfile.write("\\usepackage{tikz}\n")
        self.texfile.write("\\usetikzlibrary{positioning}\n")
        self.texfile.write("\\defaultfontfeatures{Ligatures=TeX}\n")
        self.texfile.write("\\setallmainfonts[Numbers={Lining,Proportional}]{Myriad Pro SemiCondensed}\n")

        self.texfile.write("\n")
        self.texfile.write("\\makeatletter\n")
        self.texfile.write("\\ifcase \\@ptsize \\relax% 10pt\n")
        self.texfile.write("    \\newcommand{\\HUGE}{\\@setfontsize\\HUGE{45}{50}}\n")
        self.texfile.write("    \\newcommand{\\miniscule}{\\@setfontsize\\miniscule{4}{5}}% \\tiny: 5/6\n")
        self.texfile.write("    \\newcommand{\\nano}{\\@setfontsize\\nano{3}{4}}% \\tiny: 5/6\n")
        self.texfile.write("\\or% 11pt\n")
        self.texfile.write("    \\newcommand{\\miniscule}{\\@setfontsize\\miniscule{5}{6}}% \\tiny: 6/7\n")
        self.texfile.write("    \\newcommand{\\nano}{\\@setfontsize\\nano{4}{5}}% \\tiny: 6/7\n")
        self.texfile.write("\\or% 12pt\n")
        self.texfile.write("    \\newcommand{\\miniscule}{\\@setfontsize\\miniscule{5}{6}}% \\tiny: 6/7\n")
        self.texfile.write("    \\newcommand{\\nano}{\\@setfontsize\\nano{4}{5}}% \\tiny: 6/7\n")
        self.texfile.write("\\fi\n")
        self.texfile.write("\\makeatother\n")

        self.texfile.write("\n")
        self.texfile.write("\\begin{document}\n")
        self.texfile.write("\\pagenumbering{gobble}\n")

        self.texfile.write("\n")
        self.texfile.write("\\newcommand\\normaltextheightem{0.75} % Text height for normalsize\n")
        self.texfile.write("\\newcommand\\normaltextdepthem{0.24} % Text depth for normalsize\n")
        self.texfile.write("\\pgfmathsetmacro{\\normaltextheight}{\\normaltextheightem em/1mm} % Converted to mm\n")
        self.texfile.write("\\pgfmathsetmacro{\\normaltextdepth}{\\normaltextdepthem em/1mm} % Converted to mm\n")

        for sizename, pointsize in self.fontsizes.items():
            self.texfile.write("\\pgfmathsetmacro{{\\{}textheight}}{{{}*\\normaltextheight/{}}} % Text height for {} ({} pt)\n".format(sizename, pointsize, self.fontsizes['normalsize'], sizename, pointsize))
            self.texfile.write("\\pgfmathsetmacro{{\\{}textdepth}}{{{}*\\normaltextdepth/{}}} % Text depth for {} ({} pt)\n".format(sizename, pointsize, self.fontsizes['normalsize'], sizename, pointsize))
        self.texfile.write("\n")
        self.texfile.write("\\newfontfamily\\condensed{Myriad Pro Condensed}[Numbers={Lining,Proportional}]\n")
        self.texfile.write("\n")

    def write_footer(self):
        if not self.texfile:
            return

        if self.current_picture is not None:
            self.current_picture.close()

        self.texfile.write("\\end{document}\n")

    def start(self):
        self.open_file()
        self.write_header()
        self.started = True

    def finish(self):
        self.write_footer()
        self.close_file()
        self.finished = True

    # Drawing functions
    def comment(self, comment, prefix_newline=True):
        if prefix_newline:
            s = "\n"
        else:
            s = ""
        if comment:
            s += "% {0}\n".format(comment)
        self.texfile.write(s)

    def add(self, picture):
        if not self.started:
            self.start()

        if self.current_picture is not None:
            self.current_picture.close()

        self.current_picture = picture
        picture.set_texfile(self.texfile)

    def render(self, filepath=None, open=True):
        if not self.started:
            self.start()

        if not self.finished:
            self.finish()

        print "Rendering", filepath or os.path.join(TEX_OUTPUT_FOLDER, self.texfile_name)
        subprocess.check_output(["xelatex", self.texfile_name], cwd=TEX_OUTPUT_FOLDER)
        subprocess.check_output(["xelatex", self.texfile_name], cwd=TEX_OUTPUT_FOLDER)

        if filepath:
            folder = os.path.dirname(filepath)
            if folder and not os.path.exists(folder):
                os.makedirs(folder)
            shutil.move(os.path.join(TEX_OUTPUT_FOLDER, "{0}.pdf".format(self.name)), filepath)
            if open:
                subprocess.Popen(["open", filepath]).wait()


