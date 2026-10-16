import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://insightpa_user:insightpa_pass@postgres:5432/insightpa_db")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "insightpa_user")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "insightpa_pass_secure_12345")
    MINIO_BUCKET: str = "insightpa-documents"

settings = Settings()
