import os
from skymap.mapmaker import SkyMapMaker
from skymap.geometry import Point


def build_cambridge_star_atlas(path="atlas"):
    if not os.path.exists(path):
        os.makedirs(path)

    m = SkyMapMaker(landscape=True)

    m.set_polar("atlas/01.pdf", north=True, latitude_range=80)
    m.render()
    return
    m.set_polar("atlas/20.pdf", north=False, latitude_range=50)
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


def build_sky_atlas_2000(path="skyatlas2000"):
    if not os.path.exists(path):
        os.makedirs(path)

    m = SkyMapMaker()
    m.set_intermediate("skyatlas2000/01.pdf", (90, 70), standard_parallel1=90, standard_parallel2=60, vertical_range=40)
    m.map.set_origin(Point(m.paper_size[0]/3.0, m.paper_size[1]/2.0))

    m.render()

    m.set_intermediate("skyatlas2000/02.pdf", (210, 70), standard_parallel1=90, standard_parallel2=60, vertical_range=40)
    m.map.set_origin(Point(m.paper_size[0] / 3.0, m.paper_size[1] / 2.0))

    m.render()

    m.set_intermediate("skyatlas2000/03.pdf", (330, 70), standard_parallel1=90, standard_parallel2=60, vertical_range=40)
    m.map.set_origin(Point(m.paper_size[0] / 3.0, m.paper_size[1] / 2.0))

    m.render()


if __name__ == "__main__":
    build_cambridge_star_atlas()
    #build_sky_atlas_2000()


