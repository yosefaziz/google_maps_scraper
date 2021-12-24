from __future__ import annotations

import os
import re

import pandas as pd


class GMapsScrapePostprocessor:
    """
    This class contains methods which are used to post-process the scraped data from the GMaps API
    """
    @staticmethod
    def union_dataframes(
            big_radius_df: pd.DataFrame,
            small_radius_df: pd.DataFrame
    ) -> pd.DataFrame:
        """triggers the run for the big and small radius and concatenates both dataframes to one

        Args:
            big_radius_df: Dataframe of the extracted data with the big search-radius
            small_radius_df: Dataframe of the extracted data with the small search-radius

        Returns:
            unionized_df: dataframe with scraped data from the run with the big + small radius
        """
        unionized_df = pd.concat([big_radius_df, small_radius_df])
        unionized_df = unionized_df.reset_index()
        return unionized_df

    @staticmethod
    def save_csv(scrape_df: pd.DataFrame, file_name: str, sub_folder: str) -> str:
        """saves csv file without overwriting old versions

        Args:
            scrape_df: Dataframe of the scraped Google Maps data
            file_name: Name of the export csv-file
            sub_folder: Name of the folder within the current directory in which the csv-file
                        should be saved

        Returns:
             file_name: Name of the exported csv
        """
        i = 0
        while True:
            i += 1
            file_path = f"./{sub_folder}/{file_name}"
            if os.path.isfile(file_path):
                file_name = re.sub(r"(_\d+)?\.csv", f"_{i}.csv", file_name)
            else:
                try:
                    scrape_df.to_csv(file_path, index=False)
                except FileNotFoundError:
                    os.makedirs(sub_folder)
                    scrape_df.to_csv(file_path, index=False)
                return file_name
