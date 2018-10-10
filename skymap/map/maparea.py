from skymap.tikz import TikzPicture

"""

MapArea
    Projection
    Gridlines/axes
    Border with gridline labels etc
    
    plot a point
    plot a line
    plot a circle
    


"""


class MapArea(TikzPicture):
    def __init__(self, tikz, p1, p2):
        TikzPicture.__init__(self, tikz, p1, p2, origin=None, boxed=True)