"""This module runs the Google Maps Places API scraper"""

from __future__ import annotations

import time
from typing import Any, Iterable, Tuple

import geopy.distance
import googlemaps
import pandas as pd

from export_to_google_cloud import ExportToGoogleCloudStorage
from gmaps_scrape_postprocessor import GMapsScrapePostprocessor
from input_file_preprocessor import InputFilePreprocessor


class GoogleMapsScraper:
    """This class runs the scrape for the whole input file"""
    postprocessor = GMapsScrapePostprocessor()

    def __init__(
            self,
            api_key: str,
            big_radius_km: float,
            gcp_project_id: str,
            bucket_name: str,
            input_file: str
    ):
        """Inits GoogleMapsScraper with the respective setup

        Args:
            api_key: Google Maps API key
            big_radius_km: Search Radius in km
            gcp_project_id: The Google Cloud Platform project id
            bucket_name: Name of the Google Cloud Storage bucket
            input_file: File name of the excel sheet including the areas which should be scraped
        """
        self.api_key = api_key
        self.gmaps = googlemaps.Client(key=api_key)
        self.big_radius_km = big_radius_km
        self.diameter_km = big_radius_km * 2
        self.preprocessor = InputFilePreprocessor(big_radius_km)
        self.small_radius_km = self.preprocessor.calculate_small_radius()
        self.gcp_project_id = gcp_project_id
        self.bucket_name = bucket_name
        self.input_file = input_file

    def run(self) -> None:
        """Runs the scrape throughout all rows within the input excel

        Returns:
            None
        """
        lat_long_import_df = pd.read_excel(self.input_file)
        for row in lat_long_import_df.itertuples():
            area_scraper = AreaScraper(self.api_key, self.big_radius_km, self.gcp_project_id,
                                       self.bucket_name, self.input_file, row)
            exported_file_name = area_scraper.scrape_area()
            storage_exporter = ExportToGoogleCloudStorage(self.gcp_project_id,
                                                          self.bucket_name,
                                                          exported_file_name)
            storage_exporter.upload_to_cloud_bucket()


class AreaScraper(GoogleMapsScraper):
    """
    Within the input file, there are different areas per row, which should be scraped. This class
    provides the scraping for every individual area within the iteration.
    """

    def __init__(
            self,
            api_key: str,
            big_radius_km: float,
            gcp_project_id: str,
            bucket_name: str,
            input_file: str,
            row: Iterable[Tuple[Any, ...]]
    ):
        """Inits GoogleMapsScraper with the respective setup

        Args:
            api_key: Google Maps API key
            big_radius_km: Search Radius in km
            gcp_project_id: The Google Cloud Platform project id
            bucket_name: Name of the Google Cloud Storage bucket
            input_file: File name of the excel sheet including the areas which should be scraped
            row: Row information from the input excel sheet
        """
        super().__init__(api_key, big_radius_km, gcp_project_id, bucket_name, input_file)
        self.area_block = row.area_block
        self.country = row.country
        self.search_terms = self.preprocessor.search_terms_to_list(
            row.search_terms_comma_separated
        )

        self.upper_left_coords = self.preprocessor.coords_to_tuple(row.upper_left_coordinates)
        self.lower_right_coords = self.preprocessor.coords_to_tuple(row.lower_right_coordinates)
        self.upper_right_coords = (self.upper_left_coords[0], self.lower_right_coords[1])

        self.amount_of_requests_per_row, self.amount_of_requests_per_col = \
            self.preprocessor.calculate_amount_of_requests(self.upper_left_coords,
                                                           self.lower_right_coords,
                                                           self.upper_right_coords)

    def scrape_area(self) -> str:
        """Scrapes the specific area row within the excel sheet with the big and small radius

        Returns:
            file_name: File name of the scrape-extraction
        """
        big_radius_df = self._scrape_single_radius("big")
        small_radius_df = self._scrape_single_radius("small")
        unionised_df = self.postprocessor.union_dataframes(big_radius_df, small_radius_df)
        file_name = self.postprocessor.save_csv(
            unionised_df,
            f"{self.area_block}_googlemaps_scrape.csv",
            sub_folder="scrapes"
        )
        return file_name

    def _scrape_single_radius(self, radius_type: str) -> pd.DataFrame:
        """decides which type of run it is (big/small radii) and loops through the nodes

        Args:
            radius_type: Big radius (iteration 1) or small radius (iteration 2)

        Returns:
            area_radius_df: dataframe with the scraped data from the requested radius
        """
        self.preprocessor.validate_coordinates_position(self.upper_left_coords,
                                                        self.lower_right_coords)
        self._calculate_estimated_costs()

        if radius_type == "big":
            start_longitude = self.add_km_to_longitude(self.upper_left_coords, self.big_radius_km)
            start_latitude = self.add_km_to_latitude(self.upper_left_coords, self.big_radius_km)
            radius_km = self.big_radius_km
        elif radius_type == "small":
            start_longitude = self.add_km_to_longitude(self.upper_left_coords, self.diameter_km)
            start_latitude = self.add_km_to_latitude(self.upper_left_coords, self.diameter_km)
            radius_km = self.small_radius_km
        else:
            raise ValueError("Please use 'big' or 'small' as the radius type")

        area_radius_df = self._iterate_through_nodes(start_latitude, start_longitude, radius_km)
        return area_radius_df

    @staticmethod
    def add_km_to_latitude(previous_node: Tuple[float, float], added_distance_km: float) -> float:
        """calculates the latitude for the next node by adding the diameter to the south

        Args:
            previous_node: Coords of the node used before this one
            added_distance_km: Distance that needs to be added in kilometers

        Returns:
            new_latitude: Previous latitude + great-circle-distance to the south
        """
        added_diameter_distance = geopy.distance.distance(kilometers=added_distance_km)
        new_latitude = added_diameter_distance.destination(point=previous_node,
                                                           bearing=180).latitude
        return new_latitude

    @staticmethod
    def add_km_to_longitude(previous_node: Tuple[float, float], added_distance_km: float) -> float:
        """calculates the longitude for the next node by adding the diameter to the east

        Args:
            previous_node: Coords of the node used before this one
            added_distance_km: distance that needs to be added in km

        Returns:
            new_longitude: Previous latitude + great-circle distance to the east
        """
        added_diameter_distance = geopy.distance.distance(kilometers=added_distance_km)
        new_longitude = added_diameter_distance.destination(point=previous_node,
                                                            bearing=90).longitude
        return new_longitude

    def _calculate_estimated_costs(self) -> None:
        """shows the estimated cost before running. as you can do up to 3 requests per node, the
        price will vary in this range. After printing the cost, sleep for 5s in case that script
        needs to be canceled

        Returns:
            None
        """
        PRICE_PER_REQUEST = 0.002
        MAX_REQUESTS_PER_NODE = 3
        amount_of_coordinates = self.amount_of_requests_per_row * self.amount_of_requests_per_col
        amount_of_search_terms = len(self.search_terms)
        amount_of_requests = amount_of_coordinates * amount_of_search_terms
        min_cost = round(amount_of_requests * PRICE_PER_REQUEST, 2)
        max_cost = round(amount_of_requests * MAX_REQUESTS_PER_NODE * PRICE_PER_REQUEST, 2)

        print(
            f"Estimated requests for {self.area_block}: {amount_of_requests} - """,
            f"{amount_of_requests * 3}"
        )
        print(f"Estimated costs for {self.area_block}: ${min_cost} - ${max_cost}")
        time.sleep(5)

    def _iterate_through_nodes(
        self, start_latitude: float, start_longitude: float, radius_km: float
    ) -> pd.DataFrame:
        """runs iterations through vertical and horizontal lines, which are one diameter away from
        each other

        Args:
            start_latitude: Latitude at which the iteration starts
            start_longitude: Longitude at which the iteration starts
            radius_km: Radius in which the Google Maps API looks up locations

        Returns:
            area_df: dataframe with the scraped data from the requested radius
        """
        scrape_node = (start_latitude, start_longitude)
        area_df = pd.DataFrame()
        latitude = start_latitude

        # go through each node within a vertical line
        for row_number in range(self.amount_of_requests_per_col):
            longitude = start_longitude
            latitude = self.get_latitude_in_iteration(latitude,
                                                      scrape_node,
                                                      self.diameter_km,
                                                      row_number)

            # go through each node within a horizontal line
            for column_number in range(self.amount_of_requests_per_row):
                longitude = self.get_longitude_in_iteration(longitude,
                                                            scrape_node,
                                                            self.diameter_km,
                                                            column_number)
                scrape_node = (latitude, longitude)

                area_df = self._add_area_data_to_api_scrape(radius_km, area_df, scrape_node)

        return area_df

    def _add_area_data_to_api_scrape(
            self,
            radius_km: float,
            area_df: pd.DataFrame,
            node: Tuple[float, float]
    ) -> pd.DataFrame:
        """fills in the node information into the dataframe

        Args:
            radius_km: Radius in which the Google Maps API looks up locations
            area_df: Previous DataFrame of the iteration
            node: current coordinate node

        Returns:
            area_df: Previous DataFrame added with current area data
        """
        for search_term in self.search_terms:
            df_temp = self._get_data_from_location_node(node, search_term, radius_km)
            df_temp["search_term"] = search_term
            df_temp["radius_size_km"] = radius_km
            df_temp["lat_long"] = ", ".join(str(coord_value) for coord_value in node)
            df_temp["area_block"] = self.area_block
            df_temp["country"] = self.country
            area_df = area_df.append(df_temp)
        return area_df

    def _get_data_from_location_node(
        self,
        current_node: Tuple[float, float],
        search_term: str,
        radius_km: float
    ) -> pd.DataFrame:
        """extracts location information from all request-pages into a dataframe

        Args:
            current_node: Coordinates for the current node
            search_term: Current term looked up in Google Maps
            radius_km: Search radius in km

        Returns:
            df: dataframe with Google Maps API results for the current node
        """
        request = self._build_api_request(radius_km, current_node, search_term)
        api_result_df = self._get_data_from_api_request(request)
        # One Google Maps API only shows the first 20 results. If there are more then 20, this
        # requests the next results
        try:
            next_page = request["next_page_token"]
        except KeyError:
            next_page = None
        i = 1
        while next_page in request.keys():
            i += 1
            if i > 3:
                raise Exception(f"""API request unexpectedly exceeded 3 requests for one node.
                                Search_term: {search_term}, Node: {current_node}""")
            request = self._build_api_request(radius_km, current_node, search_term, next_page)
            api_result_df = self._append_api_results_to_dataframe(request, api_result_df)
        return api_result_df

    def _build_api_request(
        self,
        radius_km: float,
        location_node: Tuple[float, float],
        search_term: str,
        page_token: str = None
    ) -> dict:
        """
        Searches for {search_term} within a {radius_km} perimeter at the coordinates {location_node}
        e.g. 'Cafés 200m around the Humboldt University Berlin'

        Args:
            radius_km: Search radius in km
            location_node: Coordinates for the current node
            search_term: Current term looked up in Google Maps
            page_token: Token that can be used to return up to 20 additional results

        Returns:
            request: The output from the Google Maps GET API-request
        """
        radius_m = radius_km * 1000
        request = self.gmaps.places_nearby(
            location=location_node,
            keyword=search_term,
            radius=radius_m,
            page_token=page_token
        )
        return request

    @staticmethod
    def get_longitude_in_iteration(
            start_longitude: float,
            node: Tuple[float, float],
            diameter_km: float,
            column_number: int
    ) -> float:
        """In case the first node is the first one, this does not calculate the next longitude

        Args:
            start_longitude: Longitude coordinates at which the iteration starts
            node: Current coordinates-node
            diameter_km: Diameter of the search radius in kilometers
            column_number: The current count of the iteration within the vertical line

        Returns:
            longitude: Longitude coordinates at which the API request should extract information
        """
        if column_number == 0:
            longitude = start_longitude
        else:
            longitude = AreaScraper.add_km_to_longitude(node, diameter_km)
        return longitude

    @staticmethod
    def get_latitude_in_iteration(
            start_latitude: float,
            node: Tuple[float, float],
            diameter_km: float,
            row_number: int
    ) -> float:
        """In case the first node is the first one, this does not calculate the next latitude

        Args:
            start_latitude: Latitude coordinates at which the iteration starts
            node: Current coordinates-node
            diameter_km: Diameter of the search radius in kilometers
            row_number: The current count of the iteration within the horizontal line

        Returns:
            latitude: Latitude coordinates at which the API request should extract information
        """
        if row_number == 0:
            latitude = start_latitude
        else:
            latitude = AreaScraper.add_km_to_latitude(node, diameter_km)
        return latitude

    @staticmethod
    def _get_data_from_api_request(request: dict) -> pd.DataFrame:
        """Pulls data from the gmaps places API request

        Args:
            request: Google Maps API request

        Returns:
            api_result_df: Dataframe with all Google Maps API request results
        """
        result = request["results"]
        api_result_df = pd.DataFrame(result)
        return api_result_df

    @staticmethod
    def _append_api_results_to_dataframe(
        request: dict,
        main_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Takes the results from the API request and appends them to the previous results

        Args:
            request: Google Maps API request
            main_df: Dataframe which contains the previous results of the current location node

        Returns:
            main_df: Appended dataframe with previous and current results of the current location
                     node
        """
        df_temp = pd.DataFrame(request["results"])
        main_df = main_df.append(df_temp)
        return main_df
