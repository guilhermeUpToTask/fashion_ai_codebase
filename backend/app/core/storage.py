import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from core.config import settings
from io import BytesIO

# TODO: needs to implement async operations to not block the fastapi async endpoints(consider aioboto3)


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )
    # TODO: This function creates a new client every time. For high performance,
    # you might consider a singleton pattern or dependency injection.


def upload_file_to_s3(file_obj: BytesIO, bucket_name: str, object_name: str):
    """Uploads a file-like object to an S3 bucket and returns the S3 URI."""
    try:
        s3_client = get_s3_client()
        file_obj.seek(0)  # set pointer at the start
        s3_client.upload_fileobj(file_obj, bucket_name, object_name)
        return f"s3://{bucket_name}/{object_name}"
    except ClientError as e:
        # Needs to logging later
        raise


def download_file_from_s3(bucket_name: str, key: str) -> BytesIO:
    """
    Downloads an object from S3 given its bucket and key, and returns
    a BytesIO stream containing the object's bytes.

    Raises:
        ValueError: If the URI is not a valid S3 URI.
        RuntimeError: If the download fails due to AWS/Boto errors.
    """

    try:
        # positional args: Bucket, Key, Fileobj
        s3_client = get_s3_client()
        file_obj = BytesIO()
        s3_client.download_fileobj(bucket_name, key, file_obj)
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"Failed to download s3://{bucket_name}/{key}: {e}") from e

    file_obj.seek(0)  # rewind to the start
    return file_obj


def generate_presigned_url(bucket: str, key: str, expires_in: int = 300) -> str:
    try:
        s3_client = get_s3_client()
        url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires_in
        )
        return url
    except ClientError as e:
        raise


def delete_file_from_s3(bucket_name: str, key: str) -> None:
    """
    Delete a single object from S3. Raises RuntimeError on failure.
    Note: S3 delete is idempotent — deleting a missing object is not an error.
    """
    try:
        s3_client = get_s3_client()
        res = s3_client.delete_object(Bucket=bucket_name, Key=key)

        status = res.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status is None or not (200 <= int(status) < 300):
            raise RuntimeError(
                f"S3 delete returned unexpected status {status} for s3://{bucket_name}/{key}"
            )

    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"Failed to delete s3://{bucket_name}/{key}: {e}") from e


def delete_files_from_s3_batch(bucket_name: str, keys: list[str]) -> None:
    """
    Delete multiple objects from S3 in a single request.
    Raises RuntimeError if any object deletion fails.
    """
    if not keys:
        return

    try:
        s3_client = get_s3_client()
        objects = [{"Key": k} for k in keys]
        print("Objects", objects)
        res = s3_client.delete_objects(
            Bucket=bucket_name, Delete={"Objects": objects, "Quiet": False}
        )

        errors = res.get("Errors", [])
        if errors:
            failed_keys = [e.get("Key") for e in errors]
            raise RuntimeError(f"Failed to delete S3 objects: {failed_keys}")

    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"Failed to delete s3://{bucket_name}/{keys}: {e}") from e
