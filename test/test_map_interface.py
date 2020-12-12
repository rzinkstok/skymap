import unittest
from skymap.atlas.cambridge_star_atlas import (
    CambridgeStarAtlasPage,
    CambridgeStarAtlasLegend,
    CambridgeStarAtlasMap,
)


class MapInterfaceTest(unittest.TestCase):
    def test_interface(self):
        c = CambridgeStarAtlasPage("map_test1")
        chart_number = 5
        CambridgeStarAtlasLegend(c, chart_number)
        CambridgeStarAtlasMap(c, chart_number)
        c.render()
