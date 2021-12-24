"""
Copy of the Google Cloud Function which gets triggered by a file creation in the Cloud Storage
bucket
"""
import google.cloud.bigquery
import yaml
from google.cloud import bigquery

from gmaps_scraper.export_to_google_cloud import build_gcp_client


def get_yaml_settings() -> dict:
    """reads the configuration-file (yaml)

    Returns:
        setup: Dictionary with all configuration variables
    """
    with open("../../setup.yaml", "r") as file:
        setup = yaml.load(file)
    return setup


def load_csv_into_bigquery(uri: str, table_id: str, client: google.cloud.bigquery.Client):
    job_config = bigquery.LoadJobConfig(
        skip_leading_rows=1,
        source_format=bigquery.SourceFormat.CSV,
        autodetect=True,
        schema_update_options="ALLOW_FIELD_ADDITION"
    )
    load_job = client.load_table_from_uri(uri, table_id, job_config=job_config)
    load_job.result()


def push_csv_to_bigquery(event: dict):
    setup = get_yaml_settings()
    project_id = setup["GOOGLE_CLOUD"]["project_id"]
    dataset_name = setup["GOOGLE_CLOUD"]["BigQuery"]["dataset"]
    bq_table_name = setup["GOOGLE_CLOUD"]["BigQuery"]["table_name"]
    table_id = f"{project_id}.{dataset_name}.{bq_table_name}"

    file = event
    uri = f"gs://{file['bucket']}/{file['name']}"
    client = build_gcp_client(bigquery, project_id)

    load_csv_into_bigquery(uri, table_id, client)
