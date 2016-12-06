import os
from skymap.map import AzimuthalEquidistantMap, EquidistantCylindricalMap, EquidistantConicMap


def build_atlas(path="atlas"):
    if not os.path.exists(path):
        os.makedirs(path)

    m = AzimuthalEquidistantMap("atlas/01.pdf", north=True, celestial=True, reference_scale=52)
    m.render()
    m = AzimuthalEquidistantMap("atlas/20.pdf", north=False, celestial=True, reference_scale=-52)
    m.render()

    for i, central_longitude in enumerate(range(0, 360, 60)):
        m = EquidistantConicMap("atlas/{0:02d}.pdf".format(i+2), celestial=True, standard_parallel1=28, standard_parallel2=52, reference_longitude=central_longitude, scale=1.25)
        m.render()

        m = EquidistantCylindricalMap("atlas/{0:02d}.pdf".format(i+8), celestial=True, reference_longitude=central_longitude, standard_parallel=14, reference_scale=30)
        m.render()

        m = EquidistantConicMap("atlas/{0:02d}.pdf".format(i+14), celestial=True, standard_parallel1=-28, standard_parallel2=-52, reference_longitude=central_longitude, scale=1.25)
        m.render()

build_atlas()



