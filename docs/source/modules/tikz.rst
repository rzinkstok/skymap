``tikz``
--------

TikZ is a LaTeX package for generating images. This module provides an interface for generating TikZ documents.

Basic structure
===============

A TikZ document can be created using the :class:`skymap.tikz.Tikz` class. This class
handles all the boilerplate stuff needed for a LaTeX TikZ document. In order to actually
draw stuff, a :class:`skymap.tikz.TikzPicture` object must be used. The first argument
of the constructor is the Tikz document the picture is to be added to. The :class:`skymap.tikz.TikzPicture`
object has methods for drawing objects, as well as methods for altering the drawing style.

Examples
========

Using the module is simple::

    from skymap.tikz import Tikz, TikzPicture
    from skymap.geometry import Circle, Rectangle, Point

    # Open a document and a picture
    t = Tikz("tizk_test1")
    p = TikzPicture(t, Point(20, 20), Point(190, 277))

    # Draw a simple circle
    p.draw_circle(Circle(Point(85, 128.5), 30))

    # Draw a dotted rectangle
    p.dotted_pen()
    p.draw_rectangle(Rectangle(Point(55, 98.5), Point(115, 158.5)))

    # Generate a pdf
    t.render(verbose=True)


Contents
========

.. toctree::
   :maxdepth: 2

   tikz/tikz
   tikz/papersize
   tikz/fontsize
   tikz/tikz_picture

