import unittest

from gmaps_scraper import AreaScraper


class TestAreaScraper(unittest.TestCase):
    """Unit testing relevant functions in the AreaScraper"""
    scraper = AreaScraper

    def test_new_longitude(self):
        """Tests whether the addition of a great circle distance is calculated right on the
        longitude"""
        result = self.scraper.add_km_to_longitude(previous_node=(0, 0), added_distance_km=1)
        self.assertAlmostEqual(result, 0.008983152841195215)

    def test_new_latitude(self):
        """Tests whether the addition of a great circle distance is calculated right on the
        latitude"""
        result = self.scraper.add_km_to_latitude(previous_node=(0, 0), added_distance_km=1)
        self.assertAlmostEqual(result, -0.009043694769749644)

    def test_get_longitude_in_iteration(self):
        """Tests whether the iteration adds a distance on the start longitude and the following
        one"""
        longitude = self.scraper.get_longitude_in_iteration(start_longitude=1,
                                                            node=(1, 1),
                                                            diameter_km=1,
                                                            column_number=0)
        self.assertEqual(longitude, 1)

        longitude = self.scraper.get_longitude_in_iteration(start_longitude=1,
                                                            node=(1, 1),
                                                            diameter_km=1,
                                                            column_number=1)
        self.assertAlmostEqual(longitude, 1.0089845120674696)

    def test_get_latitude_in_iteration(self):
        """Tests whether the iteration adds a distance on the start latitude and the following
        one"""
        latitude = self.scraper.get_latitude_in_iteration(start_latitude=1,
                                                          node=(1, 1),
                                                          diameter_km=1,
                                                          row_number=0)
        self.assertEqual(latitude, 1)

        latitude = self.scraper.get_latitude_in_iteration(start_latitude=1,
                                                          node=(1, 1),
                                                          diameter_km=1,
                                                          row_number=1)
        self.assertAlmostEqual(latitude, 0.9909563326404907)
