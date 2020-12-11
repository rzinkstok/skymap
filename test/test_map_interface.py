import unittest
from skymap.atlas.cambridge_star_atlas import (
    CambridgeStarAtlasPage,
    CambridgeStarAtlasLegend,
)
from skymap.map import MapArea, MapAreaClipMode


class MapInterfaceTest(unittest.TestCase):
    def test_interface(self):
        c = CambridgeStarAtlasPage("map_test1")
        CambridgeStarAtlasLegend(c, 5)
        MapArea(
            c,
            c.llcorner,
            c.urcorner,
            None,
            0,
            30,
            c.center,
            MapAreaClipMode.paper,
            [],
            True,
        )
        c.render()
