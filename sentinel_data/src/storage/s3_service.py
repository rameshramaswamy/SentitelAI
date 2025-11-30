# sentinel_data/src/storage/s3_service.py
import asyncio
import aioboto3
import logging
from botocore.exceptions import ClientError
from src.config import settings

logger = logging.getLogger("data.s3")

class S3Service:
    def __init__(self):
        self.session = aioboto3.Session()
        self.config = {
            "endpoint_url": settings.S3_ENDPOINT,
            "aws_access_key_id": settings.S3_ACCESS_KEY,
            "aws_secret_access_key": settings.S3_SECRET_KEY,
        }
        self.bucket = settings.S3_BUCKET_NAME

    async def initialize_bucket(self):
        """Ensures bucket exists (Dev helper)."""
        async with self.session.client("s3", **self.config) as s3:
            try:
                await s3.head_bucket(Bucket=self.bucket)
                logger.info(f"Bucket '{self.bucket}' exists.")
            except ClientError:
                logger.info(f"Creating bucket '{self.bucket}'...")
                await s3.create_bucket(Bucket=self.bucket)

    async def upload_bytes(self, key: str, data: bytes, content_type: str = "audio/pcm"):
        """Uploads raw bytes to S3."""
        async with self.session.client("s3", **self.config) as s3:
            try:
                await s3.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=data,
                    ContentType=content_type
                )
                logger.info(f"Uploaded {len(data)} bytes to s3://{self.bucket}/{key}")
                return f"s3://{self.bucket}/{key}"
            except Exception as e:
                logger.error(f"Upload failed: {e}")
                raise e
    async def upload_file(self, file_path: str, key: str):
        """High-performance file upload."""
        def _upload_sync():
            import boto3
            # Create a sync client just for this thread to use TransferConfig
            s3_sync = boto3.client(
                "s3", 
                endpoint_url=self.config["endpoint_url"],
                aws_access_key_id=self.config["aws_access_key_id"],
                aws_secret_access_key=self.config["aws_secret_access_key"]
            )
            s3_sync.upload_file(file_path, self.bucket, key)

        loop = asyncio.get_running_loop()
        # Offload IO blocking task to a thread
        await loop.run_in_executor(None, _upload_sync)
        logger.info(f"Offloaded upload of {key} complete.")