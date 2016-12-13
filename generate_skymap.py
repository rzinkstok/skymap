import os
from skymap.map import AzimuthalEquidistantMap, EquidistantCylindricalMap, EquidistantConicMap
from skymap.mapmaker import SkyMapMaker


def build_atlas(path="atlas"):
    if not os.path.exists(path):
        os.makedirs(path)

    m = SkyMapMaker()

    m.set_polar("atlas/01.pdf", north=True, vertical_range=50)
    m.render()

    m.set_polar("atlas/20.pdf", north=False, vertical_range=50)
    m.render()

    for i, center_longitude in enumerate(range(0, 360, 60)):
        center = (center_longitude, 45)
        m.set_intermediate("atlas/{0:02d}.pdf".format(i+2), center, standard_parallel1=35, standard_parallel2=60, vertical_range=56)
        m.render()

        m.set_equatorial("atlas/{0:02d}.pdf".format(i+8), center_longitude=center_longitude, standard_parallel=14, vertical_range=50)
        m.render()

        center = (center_longitude, -45)
        m.set_intermediate("atlas/{0:02d}.pdf".format(i+14), center, standard_parallel1=-35, standard_parallel2=-60, vertical_range=56)
        m.render()


def label_size_test():
    from skymap.metapost import MetaPostFigure
    from skymap.geometry import Point

    m = MetaPostFigure("bliep")
    m.draw_text(Point(10, 0), "Bliep!", "rt")
    m.end_figure()
    print m.bounding_box()
    print m.bounding_box_size()

build_atlas()
#label_size_test()


