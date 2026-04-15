"""
Core configuration settings for Erebus backend.
AWS RDS PostgreSQL + ElastiCache Redis + S3
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse
from pathlib import Path

# Load .env early so os.getenv() calls below always see the values,
# regardless of which module imported config.py first.
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path, override=True)
except ImportError:
    pass  # python-dotenv not installed; rely on shell environment

logger = logging.getLogger(__name__)


@dataclass
class DatabaseSettings:
    """AWS RDS PostgreSQL configuration"""
    url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/erebus"
    ))
    pool_size: int = 5
    max_overflow: int = 10
    echo_sql: bool = field(default_factory=lambda: os.getenv("DB_ECHO", "false").lower() == "true")
    ssl_mode: str = "require"
    
    def __post_init__(self):
        try:
            parsed = urlparse(self.url)
            if parsed.scheme not in ('postgresql', 'postgres'):
                raise ValueError(f"Invalid database scheme: {parsed.scheme}")
            safe_url = f"{parsed.scheme}://{parsed.username}:***@{parsed.hostname}:{parsed.port or 5432}/{parsed.path.lstrip('/')}"
            logger.info(f"Database configured: {safe_url}")
        except Exception as e:
            logger.error(f"Invalid DATABASE_URL: {e}")
            raise
    
    def get_connection_args(self) -> dict:
        parsed = urlparse(self.url)
        return {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "database": parsed.path.lstrip('/'),
            "user": parsed.username,
            "password": parsed.password,
            "sslmode": self.ssl_mode,
            "connect_timeout": 10,
        }


@dataclass
class RedisSettings:
    """AWS ElastiCache Redis configuration"""
    url: str = field(default_factory=lambda: os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0"
    ))
    ttl_default: int = 3600
    ttl_alpha_scores: int = 300
    ttl_company_data: int = 86400
    enabled: bool = field(default_factory=lambda: os.getenv("REDIS_ENABLED", "true").lower() == "true")
    ssl: bool = True
    
    def __post_init__(self):
        try:
            parsed = urlparse(self.url)
            if parsed.scheme not in ('redis', 'rediss'):
                raise ValueError(f"Invalid Redis scheme: {parsed.scheme}")
            if parsed.password:
                safe_url = f"{parsed.scheme}://:***@{parsed.hostname}:{parsed.port or 6379}/{parsed.path.lstrip('/')}"
            else:
                safe_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port or 6379}/{parsed.path.lstrip('/')}"
            logger.info(f"Redis configured: {safe_url} (enabled: {self.enabled})")
        except Exception as e:
            logger.error(f"Invalid REDIS_URL: {e}")
            raise


@dataclass
class AWSSettings:
    """AWS configuration"""
    access_key_id: Optional[str] = field(default_factory=lambda: os.getenv("AWS_ACCESS_KEY_ID"))
    secret_access_key: Optional[str] = field(default_factory=lambda: os.getenv("AWS_SECRET_ACCESS_KEY"))
    region: str = field(default_factory=lambda: os.getenv("AWS_REGION", "ap-south-1"))
    s3_bucket_name: str = field(default_factory=lambda: os.getenv("S3_BUCKET_NAME", "erebus-documents"))

    # ── OCR — S3 prefix (still needed for upload routing) ───────────────────
    ocr_s3_prefix: str = field(default_factory=lambda: os.getenv("OCR_S3_PREFIX", "ocr-uploads"))

    @property
    def is_configured(self) -> bool:
        return bool(self.access_key_id and self.secret_access_key)


@dataclass
class Settings:
    """Main application settings"""
    
    aws:      AWSSettings      = field(default_factory=AWSSettings)
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    redis:    RedisSettings    = field(default_factory=RedisSettings)
    
    app_name: str = "Erebus"
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "change-me-in-production"))
    
    def __post_init__(self):
        warnings = []
        
        if not self.aws.is_configured:
            warnings.append(
                "AWS credentials not configured. "
                "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY. "
                "S3 features will be unavailable."
            )
        
        if self.environment == "production":
            if self.secret_key == "change-me-in-production":
                raise ValueError("SECRET_KEY must be set in production")
            if "localhost" in self.database.url:
                raise ValueError("Cannot use localhost database in production")
            if "localhost" in self.redis.url:
                raise ValueError("Cannot use localhost Redis in production")
        
        for warning in warnings:
            logger.warning(warning)


settings = Settings()