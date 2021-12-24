import unittest

from input_file_preprocessor import *


class TestInputFilePreprocessor(unittest.TestCase):
    """Unit testing relevant functions in the InputFilePreprocessor"""
    preprocessor = InputFilePreprocessor(1)

    def test_calculate_small_radius(self):
        """Tests whether the small radius is calculated right"""
        big_radius = 1
        preprocessor = InputFilePreprocessor(big_radius)
        result = preprocessor.calculate_small_radius()
        self.assertAlmostEqual(result, 0.8284271)

        error_radii = [0, -1]
        for radius in error_radii:
            preprocessor = InputFilePreprocessor(radius)
            with self.assertRaises(ValueError):
                preprocessor.calculate_small_radius()

    def test_get_yaml_setup(self):
        """Tests the input within the setup.yaml"""
        yaml = get_yaml_setup()
        input_file_name = yaml['LOCAL']['input_file_name']
        self.assertIsInstance(input_file_name, str)
        search_radius = yaml['LOCAL']['search_radius_km']
        self.assertIsInstance(search_radius, (int, float))
        self.assertGreater(search_radius, 0)
        cred = yaml['GOOGLE_CLOUD']['credentials_file_path']
        self.assertIsInstance(cred, str)
        proj_id = yaml['GOOGLE_CLOUD']['project_id']
        self.assertIsInstance(proj_id, str)
        bucket = yaml['GOOGLE_CLOUD']['Storage']['bucket_name']
        self.assertIsInstance(bucket, str)
        save_file_name = yaml['GOOGLE_CLOUD']['Storage']['save_file_name']
        self.assertIsInstance(save_file_name, str)
        maps_api_key = yaml['GOOGLE_CLOUD']['Maps']['api_key']
        self.assertIsInstance(maps_api_key, str)

    def test_search_terms_to_list(self):
        """Tests whether the search terms are restructured from string to a list"""
        search_terms = "abc, def,,   ,ghi,123"
        result = self.preprocessor.search_terms_to_list(search_terms)
        self.assertEqual(result, ["abc", "def", "ghi", "123"])

    def test_calculate_amount_of_requests(self):
        """Tests whether the amount of requests per horizontal and vertical line within the node-
        loop is calculated right"""
        radius = 1
        preprocessor = InputFilePreprocessor(radius)
        upper_left_coord = (52.68910140425828, 13.060384819899381)
        lower_right_coord = (52.41019183750047, 13.775869390116974)
        upper_right_coord = (upper_left_coord[0], lower_right_coord[1])
        req_per_row, req_per_col = preprocessor.calculate_amount_of_requests(
            upper_left_coord,
            lower_right_coord,
            upper_right_coord
        )
        self.assertEqual((req_per_row, req_per_col), (24, 15))

    def test_validate_amount_of_requests(self):
        """Test whether an error is raised if 4 big radii don't fit in the to be scraped area"""
        radius = 1.5
        preprocessor = InputFilePreprocessor(radius)
        geodesic_distance = 4
        diameter = radius * 2
        with self.assertRaises(ValueError):
            preprocessor.validate_amount_of_requests(geodesic_distance, diameter)

    def test_validate_coordinates_values(self):
        """Tests whether latitudes [longitudes] are within -90 and 90 [-180 and 180]"""
        error_coords = [(91, 0), (-91, 0), (0, 181), (0, -181), (91, 181), (-91, 181), (91, -181),
                        (-91, -181)]
        for coords in error_coords:
            with self.assertRaises(ValueError):
                self.preprocessor.validate_coordinates_values(coords)

        good_coords = (0, 0)
        self.assertIsNone(self.preprocessor.validate_coordinates_values(good_coords))
