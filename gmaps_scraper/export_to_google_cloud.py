import os

from google.cloud import storage


class ExportToGoogleCloudStorage:
    """This class provides the upload of files into the Google Cloud Storage"""
    def __init__(self, project_name: str, bucket_name: str, file_name: str):
        """Inits ExportToGoogleCloudStorage with the respective Storage information

        Args:
            project_name: Name of the Google Cloud Project
            bucket_name: Name of the Google Cloud Storage bucket
            file_name: Name of the file within the bucket
        """
        self.project_name = project_name
        self.bucket_name = bucket_name
        self.file_name = "scrapes/" + file_name

    def upload_to_cloud_bucket(self) -> None:
        """Uploads a blob into the Google Cloud Storage

        Returns:
            None
        """
        storage_client = build_gcp_client(storage, self.project_name)
        bucket = storage_client.get_bucket(self.bucket_name)
        blob = bucket.blob(self.file_name)
        blob.upload_from_filename(self.file_name)


def set_credentials(credentials_file_path: str) -> None:
    """Sets the env variable with the Google Cloud credentials, so that you get access to your
    project

    Args:
        credentials_file_path: File path to the Google Cloud service account credentials

    Returns:
        None
    """
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file_path


def build_gcp_client(service, project_name: str):
    """Builds a connection to the Google Cloud client of any service

    Args:
        service: Class of the respective service from the google.cloud package (e.g. bigquery,
                 storage etc.)
                 [type: google.cloud.SERVICENAME]
        project_name: Name of the Google Cloud Platform project
    Returns:
        client: Client of the respective Google Cloud Platform service
                [type: google.cloud.SERVICENAME.client.Client]
    """
    client = service.Client(project=project_name)
    return client
