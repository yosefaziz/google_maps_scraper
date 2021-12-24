from export_to_google_cloud import set_credentials
from gmaps_scraper import GoogleMapsScraper
from input_file_preprocessor import get_yaml_setup


if __name__ == "__main__":
    settings = get_yaml_setup()
    api_key = settings["GOOGLE_CLOUD"]["Maps"]["api_key"]
    bucket = settings["GOOGLE_CLOUD"]["Storage"]["bucket_name"]
    cred = settings["GOOGLE_CLOUD"]["credentials_file_path"]
    file_name = settings["LOCAL"]["input_file_name"]
    proj = settings["GOOGLE_CLOUD"]["project_id"]
    search_radius = settings["LOCAL"]["search_radius_km"]

    set_credentials(cred)
    scraper = GoogleMapsScraper(api_key, search_radius, proj, bucket, file_name)
    scraper.run()
