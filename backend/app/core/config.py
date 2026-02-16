import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://quartu_user:quartu_pass@quartu-postgres:5432/quartu_abusivismo")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "quartu_user")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "quartu_pass_secure_12345")
    MINIO_BUCKET: str = "quartu-documents"

settings = Settings()
