import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory: root of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "EvidenceRAG")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "evidencerag-super-secret-development-key-32-chars-minimum")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'storage' / 'evidencerag.db'}")

    # Storage Paths
    UPLOAD_DIR: Path = BASE_DIR / "storage" / "uploads"
    REPORTS_DIR: Path = BASE_DIR / "storage" / "reports"
    MODELS_DIR: Path = BASE_DIR / "models"

    # Security & Admin Registration
    ADMIN_INVITE_CODE: str = os.getenv("ADMIN_INVITE_CODE", "AdminSecret@2026")

    # OCR
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")

    # AI / LLM / RAG Settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # Verification Config
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.85"))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))

    def __init__(self):
        # Ensure directories exist
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.MODELS_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
