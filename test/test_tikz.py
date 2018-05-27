import unittest
from skymap.tikz import Tikz, TikzPicture
from skymap.geometry import Point, Circle, Rectangle


class TikzTest(unittest.TestCase):
    def test_picture(self):
        t = Tikz("test1")
        d = TikzPicture(t, Point(20,20), Point(190, 277))

        d.draw_circle(Circle(Point(85, 128.5), 30))
        d.draw_rectangle(Rectangle(Point(55, 98.5), Point(115, 158.5)))
        t.render()

    def test_multiple_pictures(self):
        t = Tikz("test2")
        d = TikzPicture(t, Point(20, 20), Point(190, 138.5))
        d.draw_circle(Circle(Point(85, 59.25), 30))
        d.draw_rectangle(Rectangle(Point(55, 29.25), Point(115, 89.25)))

        d2 = TikzPicture(t, Point(20, 158.5), Point(95, 277))
        d2.draw_circle(Circle(Point(37.5, 59.25), 30))
        d2.draw_rectangle(Rectangle(Point(7.5, 29.25), Point(67.5, 89.25)))
        with d2.clip():
            d2.draw_circle(Circle(Point(37.5, 59.25), 40))

        d3 = TikzPicture(t, Point(115, 158.5), Point(190, 277))
        d3.draw_circle(Circle(Point(37.5, 59.25), 30))
        d3.draw_rectangle(Rectangle(Point(7.5, 29.25), Point(67.5, 89.25)))

        t.render()