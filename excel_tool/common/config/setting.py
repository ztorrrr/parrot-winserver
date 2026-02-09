import os
from dataclasses import dataclass
from functools import cache
from platform import system as sys

from cachetools.func import ttl_cache
from excel_tool.common.config.constant import (
    SERVICE,
    DEFAULT_REGION,
    DEFAULT_HOST,
    DEFAULT_PORT,
    S3_DATASET_EXCEL_PREFIX,
    S3_PRESIGNED_URL_EXPIRY,
)
from excel_tool.common.util import secret_manager


def is_local():
    """로컬 환경(macOS) 여부 확인"""
    return True if sys().lower().startswith("darwin") else False


@dataclass
class Config:
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "DEV")

    # Server Configuration
    HOST: str = DEFAULT_HOST
    PORT: int = DEFAULT_PORT

    # S3 Configuration
    S3_REGION: str = DEFAULT_REGION
    S3_BUCKET: str = os.getenv("S3_BUCKET_NAME", f"milot-{ENVIRONMENT.lower()}")
    S3_DATASET_EXCEL_PREFIX: str = S3_DATASET_EXCEL_PREFIX
    S3_PRESIGNED_URL_EXPIRY: int = S3_PRESIGNED_URL_EXPIRY

    @property
    def S3_BUCKET_NAME(self) -> str:
        """S3_BUCKET의 별칭 (하위 호환성)"""
        return self.S3_BUCKET

    # Documentation URLs
    DOCS_URL = "/docs"
    REDOC_URL = "/redoc"

    # CORS
    ALLOW_SITE = ["*"]

    # Logging
    LOG_LEVEL = "DEBUG"

    # Secret Manager Key Paths
    ODATA_USERS_KEY: str = f"{ENVIRONMENT.lower()}/{SERVICE}/odata/userauth"


@dataclass
class ProductionConfig(Config):
    """
    운영 환경 Config
    """

    DOCS_URL = "/docs"
    REDOC_URL = None
    LOG_LEVEL = "INFO"


@dataclass
class DevelopmentConfig(Config):
    """
    개발 환경 Config
    """

    TEST_MODE = True
    LOG_LEVEL = "DEBUG"


@dataclass
class TestConfig(Config):
    """
    테스트 환경 Config
    """

    TEST_MODE = True
    LOG_LEVEL = "DEBUG"


@cache
def config():
    """환경별 설정 반환"""
    env = Config().ENVIRONMENT.upper()
    if env == "PROD":
        return ProductionConfig()
    elif env == "DEV":
        return DevelopmentConfig()
    else:
        return TestConfig()


# Alias for compatibility
get_config = config


@ttl_cache()
def get_odata_users():
    """OData API 사용자 정보 조회 (Basic Auth용)"""
    return secret_manager.get_secret(config().ODATA_USERS_KEY)
