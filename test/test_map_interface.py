import unittest
from skymap.atlas.cambridge_star_atlas import (
    CambridgeStarAtlasPage,
    CambridgeStarAtlasLegend,
    CambridgeStarAtlasMap,
)


class MapInterfaceTest(unittest.TestCase):
    def test_interface_conic(self):
        chart_number = 2
        c = CambridgeStarAtlasPage("map_test1")
        CambridgeStarAtlasLegend(c, chart_number)
        CambridgeStarAtlasMap(c, chart_number)
        c.render()

        chart_number = 15
        c = CambridgeStarAtlasPage("map_test2")
        CambridgeStarAtlasLegend(c, chart_number)
        CambridgeStarAtlasMap(c, chart_number)
        c.render()

    def test_interface_cylindrical(self):
        chart_number = 8
        c = CambridgeStarAtlasPage("map_test3")
        CambridgeStarAtlasLegend(c, chart_number)
        CambridgeStarAtlasMap(c, chart_number)
        c.render()

        chart_number = 13
        c = CambridgeStarAtlasPage("map_test4")
        CambridgeStarAtlasLegend(c, chart_number)
        CambridgeStarAtlasMap(c, chart_number)
        c.render()

    def test_interface_azimuthal(self):
        chart_number = 1
        c = CambridgeStarAtlasPage("map_test5")
        CambridgeStarAtlasLegend(c, chart_number)
        CambridgeStarAtlasMap(c, chart_number)
        c.render()

        chart_number = 20
        c = CambridgeStarAtlasPage("map_test6")
        CambridgeStarAtlasLegend(c, chart_number)
        CambridgeStarAtlasMap(c, chart_number)
        c.render()
