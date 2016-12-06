from skymap.map import Map, AzimuthalEquidistantMap, EquidistantCylindricalMap, EquidistantConicMap
from skymap.metapost import MetaPostFigure
from skymap.geometry import Arc, Point

#m = AzimuthalEquidistantMap("test.pdf", north=True, celestial=True)
#m = EquidistantCylindricalMap("test.pdf", celestial=True, reference_longitude=-15, reference_scale=30)
m = EquidistantConicMap("test.pdf", celestial=True, standard_parallel1=25, standard_parallel2=47, reference_longitude=30)
m.render()




