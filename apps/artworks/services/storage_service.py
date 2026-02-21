"""
Storage Service - S3/MinIO integration for artwork storage.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    Service for managing file storage (S3/MinIO).

    Falls back to local storage if USE_S3 is False.
    """

    def __init__(self):
        self.use_s3 = getattr(settings, 'USE_S3', False)
        if self.use_s3:
            import boto3
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1'),
                endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
            )
            self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def upload_file(self, file_path, object_name=None):
        """
        Upload a file to S3/MinIO.

        Args:
            file_path: Local file path
            object_name: S3 object key (default: filename)

        Returns:
            URL of the uploaded file, or None if failed
        """
        if not self.use_s3:
            logger.info("S3 disabled, using local storage")
            return None

        if object_name is None:
            import os
            object_name = os.path.basename(file_path)

        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_name)
            url = self._get_file_url(object_name)
            logger.info(f"File uploaded to S3: {url}")
            return url
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return None

    def delete_file(self, object_name):
        """Delete a file from S3/MinIO."""
        if not self.use_s3:
            return

        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            logger.info(f"File deleted from S3: {object_name}")
        except Exception as e:
            logger.error(f"S3 delete failed: {e}")

    def generate_presigned_url(self, object_name, expiration=3600):
        """
        Generate a pre-signed URL for temporary access.

        Args:
            object_name: S3 object key
            expiration: URL validity in seconds (default: 1 hour)

        Returns:
            Pre-signed URL string
        """
        if not self.use_s3:
            return None

        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_name
                },
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Pre-signed URL generation failed: {e}")
            return None

    def _get_file_url(self, object_name):
        """Get the public URL of an S3 object."""
        endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
        if endpoint:
            return f"{endpoint}/{self.bucket_name}/{object_name}"
        region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        return f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{object_name}"
