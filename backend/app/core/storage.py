import boto3
import botocore
from botocore.exceptions import BotoCoreError, ClientError
from core.config import settings
from io import BytesIO


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )
    # This function creates a new client every time. For high performance,
    # you might consider a singleton pattern or dependency injection.


def upload_file_to_s3(file_obj: BytesIO, bucket_name: str, object_name: str):
    """Uploads a file-like object to an S3 bucket and returns the S3 URI."""
    s3_client = get_s3_client()
    try:
        file_obj.seek(0)  # set pointer at the start
        s3_client.upload_fileobj(file_obj, bucket_name, object_name)
        return f"s3://{bucket_name}/{object_name}"
    except ClientError as e:
        # Needs to logging later
        raise


def download_file_from_s3(bucket: str, key: str) -> BytesIO:
    """
    Downloads an object from S3 given its bucket and key, and returns
    a BytesIO stream containing the object's bytes.

    Raises:
        ValueError: If the URI is not a valid S3 URI.
        RuntimeError: If the download fails due to AWS/Boto errors.
    """
    s3_client = get_s3_client()
    file_obj = BytesIO()
    try:
        # positional args: Bucket, Key, Fileobj
        s3_client.download_fileobj(bucket, key, file_obj)
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"Failed to download s3://{bucket}/{key}: {e}") from e

    file_obj.seek(0)   # rewind to the start
    return file_obj
