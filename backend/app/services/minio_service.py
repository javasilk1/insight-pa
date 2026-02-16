from minio import Minio
from minio.error import S3Error
from core.config import settings
import io


class MinioService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )
        self.bucket = settings.MINIO_BUCKET

    def create_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload_file(self, file_data: bytes, filename: str, building_id: str) -> str:
        self.create_bucket()
        object_name = f"{building_id}/{filename}"
        self.client.put_object(
            self.bucket,
            object_name,
            io.BytesIO(file_data),
            length=len(file_data),
        )
        url = f"minio://{self.bucket}/{object_name}"
        return url

    def get_file(self, file_path: str) -> bytes:
        parts = file_path.replace("minio://", "").split("/", 1)
        bucket = parts[0]
        object_name = parts[1]
        response = self.client.get_object(bucket, object_name)
        return response.read()

    def delete_file(self, file_path: str):
        parts = file_path.replace("minio://", "").split("/", 1)
        bucket = parts[0]
        object_name = parts[1]
        self.client.remove_object(bucket, object_name)


minio_service = MinioService()
