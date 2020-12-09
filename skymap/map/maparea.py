from skymap.tikz import TikzPicture
from skymap.geometry import Point, Circle

"""

MapArea
    Projection
    Gridlines/axes
    Border with gridline labels etc
    
    plot a point
    plot a line
    plot a circle
    


"""


class MapLegend(TikzPicture):
    def __init__(self, tikz, p1, p2):
        TikzPicture.__init__(self, tikz, p1, p2, origin=None, boxed=True)


class MapArea(TikzPicture):
    """Area on the paper used to plot a map.
    Area is defined by the points p1 and p2.
    Origin of the area is lower left corner (p1), and a box is drawn around the map.

    Objects to place:
      - Border
      - Ticks and numbers
      - Gridlines
      - Ecliptic, galactic equator
      - Constellation boundaries
      - Stars
      - Galaxies
      - Other objects
    """

    def __init__(self, tikz, p1, p2, projection):
        TikzPicture.__init__(self, tikz, p1, p2, origin=None, boxed=True)
        self.projection = projection


class StarMarker(object):
    def __init__(self, skycoord, magnitude):
        self.skycoord = skycoord
        self.magnitude = magnitude

    def draw(self, map_area):
        point = map_area.projection.project(self.skycoord)
        map_area.fill_circle(Circle(point, self.size(map_area)))
