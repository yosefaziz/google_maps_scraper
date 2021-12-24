from __future__ import annotations

from ast import literal_eval
from math import floor, sqrt
from typing import List, Tuple
import yaml

import geopy.distance


class InputFilePreprocessor:
    """
    This class contains methods that are used to pre-process the scraped data from the GMaps API
    """
    def __init__(self, big_radius_km: float):
        """Inits InputFilePreprocessor with the radius from the setup file.

        Args:
            big_radius_km: Google Maps search radius in km
        """
        self.diameter_km = big_radius_km * 2

    def calculate_amount_of_requests(
        self,
        upper_left_coords: Tuple[float, float],
        lower_right_coords: Tuple[float, float],
        upper_right_coords: Tuple[float, float],
    ) -> Tuple[int, int]:
        """measures the distance in between horizontal and vertical coordinates and divides it by
        the diameter to get the number of requests

        Args:
            upper_left_coords: Upper left Google Maps coordinates in the excel sheet
            lower_right_coords: Lower right Google Maps coordinates in the excel sheet
            upper_right_coords: Upper right Google Maps coordinates in the excel sheet
        Returns:
            amount_of_requests_per_col: Amount of API calls per vertical line of the iteration
            amount_of_requests_per_row: Amount of API calls per horizontal line of the iteration
        """
        area_width_km = geopy.distance.geodesic(upper_left_coords, upper_right_coords).km
        area_length_km = geopy.distance.geodesic(lower_right_coords, upper_right_coords).km
        self.validate_amount_of_requests(area_width_km, self.diameter_km)
        self.validate_amount_of_requests(area_length_km, self.diameter_km)
        amount_of_requests_per_row = floor(area_width_km / self.diameter_km)
        amount_of_requests_per_col = floor(area_length_km / self.diameter_km)
        return amount_of_requests_per_row, amount_of_requests_per_col

    def calculate_small_radius(self) -> float:
        """As we have a square of 4 big radius circles, you can build a diagonal line through the
        center of two squares to create a right triangle, which allows you to use the Pythagorean
        theorem. As the legs (a, b) are the same and the distance in between two circle-centers
        equal one diameter, the formula to get the hypotenuse is sqrt(2*d²).
        Now you have a diagonal line including 2 radii and the diameter of the small radius, which
        leads to the final formula: sqrt(2d²)-d
        Visualization: /images/small_circle_calculation.jpg

        Returns:
            small_radius_km: Search radius for the small-radius-iteration
        """
        if self.diameter_km <= 0:
            raise ValueError("diameter must be bigger than 0!")
        small_radius_km = sqrt(2 * (self.diameter_km ** 2)) - self.diameter_km
        return small_radius_km

    def validate_coordinates_position(
            self,
            upper_left_coords: Tuple[float, float],
            lower_right_coords: Tuple[float, float]
    ) -> None:
        """runs value validation for coordinates and raises an exception in case latitude or
        longitude are in crossing each other. In theory, this is a possible outcome, but as this is
        very costly, the user should better choose lat/lng-coordinates within a range.

        Args:
            upper_left_coords: Coordinates of the upper left node
            lower_right_coords: Coordinates of the lower right node

        Returns:
            None
        """
        self.validate_coordinates_values(upper_left_coords)
        self.validate_coordinates_values(lower_right_coords)

        if lower_right_coords[0] > upper_left_coords[0]:
            raise Exception("""The lower right coordinates' latitude must not be higher than the
                   upper left one's""")
        if upper_left_coords[1] > lower_right_coords[1]:
            raise Exception("""The upper left coordinates' longitude must not be higher than the
                   upper right one's""")

    def search_terms_to_list(self, search_terms: str) -> List[str]:
        """converts a comma-separated string into a list and drops empty values

        Args:
            search_terms: String of search terms (comma separated)

        Returns:
            search_terms: List of search terms
        """
        self._validate_search_terms(search_terms)
        search_terms = search_terms.split(",")
        stripped_search_terms = [term.strip() for term in search_terms]
        cleaned_search_terms = [term for term in stripped_search_terms if term]
        return cleaned_search_terms

    @staticmethod
    def _validate_search_terms(search_terms: str) -> None:
        """verifies whether the search term field in the excel sheet is empty or not

        Args:
            search_terms: search terms from the excel field

        Returns:
            None
        """
        cleaned_search_terms = search_terms.strip()
        if not cleaned_search_terms:
            raise ValueError("You need to list the search terms for Google Maps")

    @staticmethod
    def coords_to_tuple(coords: str) -> Tuple[float, float]:
        """Converts coordinates from a string to a tuple

        Args:
            coords: Google Maps coordinates from the excel sheet

        Returns:
            coord_tuple: Google Maps coordinates from the excel sheet as a tuple
        """
        try:
            coord_tuple = literal_eval(coords)
            return coord_tuple
        except ValueError:
            raise Exception("Both coordinates must be floats")
        except SyntaxError:
            raise Exception("The two coordinates must be separated by a comma")

    @staticmethod
    def validate_coordinates_values(coords: Tuple[float, float]) -> None:
        """validates whether latitude or longitude values are in the right range

        Args:
            coords:

        Returns:
            None
        """
        if not 90 > coords[0] > -90:
            raise ValueError("Latitude must be in between 90° and -90°")
        if not 180 > coords[1] > -180:
            raise ValueError("Longitude must be in between 180° and -180°")

    @staticmethod
    def validate_amount_of_requests(geodesic_distance, diameter) -> None:
        """As the code needs to build 4 circles before calculating the small circle in the middle,
        you need at least 4 circles, which means 2 diameters on a horizontal and a vertical line.

        Returns:
            None
        """
        amount_of_circles_per_plane = geodesic_distance/diameter
        if 2 > amount_of_circles_per_plane:
            raise ValueError("""The search field is too small/the radius to big. Get sure that the
            radius fits into the area at least 4 times on the horizontal and vertical plane""")


def get_yaml_setup() -> dict:
    """reads the configuration-file (yaml)

    Returns:
        setup: Dictionary with all configuration variables
    """
    with open('../setup.yaml', 'r') as file:
        setup = yaml.load(file, Loader=yaml.FullLoader)
    return setup
