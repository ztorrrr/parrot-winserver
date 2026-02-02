import os
from dataclasses import dataclass
from functools import cache
from platform import system as sys

from cachetools.func import ttl_cache
from common.config.constant import SERVICE
from common.util import parameterstore, secret_manager


def is_local():
    return True if sys().lower().startswith("darwin") else False


@dataclass
class Config:
    """
    기본 세팅
    """

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "DEV")

    # Google Auth Key
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_SECRET_KEY: str = os.getenv("GOOGLE_SECRET_KEY", "")

    # SQLAlchemy
    POOL_SIZE = 5
    MAX_OVERFLOW = 10
    SQLALCHEMY_POOL_RECYCLE: int = 900
    SQLALCHEMY_ECHO: bool = False

    S3_BUCKET: str = f"milot-{ENVIRONMENT.lower()}"
    GCS_BUCKET: str = f"milot-{ENVIRONMENT.lower()}"
    BIGQUERY_DATASET: str = "parrot"

    # Dataset Pipeline SQS Queues
    DATASET_VALIDATOR_QUEUE: str = (
        f"parrot-dataset-validator-queue-{ENVIRONMENT.lower()}"
    )
    DATASET_VALIDATION_RESULT_QUEUE: str = (
        f"parrot-dataset-validation-result-queue-{ENVIRONMENT.lower()}"
    )
    DATASET_TRANSFORMER_QUEUE: str = (
        f"parrot-dataset-transformer-queue-{ENVIRONMENT.lower()}"
    )
    DATASET_SENDER_QUEUE: str = f"parrot-dataset-sender-queue-{ENVIRONMENT.lower()}"
    DATASET_COMPLETER_QUEUE: str = (
        f"parrot-dataset-completer-queue-{ENVIRONMENT.lower()}"
    )

    # Upload Pipeline SQS Queues
    UPLOAD_EXTRACTOR_QUEUE: str = f"parrot-upload-extractor-queue-{ENVIRONMENT.lower()}"
    UPLOAD_CONVERTER_QUEUE: str = f"parrot-upload-converter-queue-{ENVIRONMENT.lower()}"

    # Upload Preview DynamoDB Table
    UPLOAD_PREVIEW_TABLE: str = f"parrot-upload-preview-{ENVIRONMENT.lower()}"

    COMMON_KEY: str = f"{ENVIRONMENT.lower()}/{SERVICE}/common"

    # LLM Provider Keys
    # Anthropic (Claude) - 경로 예: dev/parrot/anthropic
    ANTHROPIC_KEY: str = f"{ENVIRONMENT.lower()}/{SERVICE}/anthropic"

    # 구글 Auth Key
    GOOGLE_AUTH_KEY: str = f"{ENVIRONMENT.lower()}/{SERVICE}/google/auth"
    # 구글 GCP Key
    GCP_KEY: str = f"{ENVIRONMENT.lower()}/{SERVICE}/gcp/mil-db"

    DOCS_URL = "/docs"
    REDOC_URL = "/redoc"

    ALLOW_SITE = ["*"]
    LOG_PATH = "conf/.log-config.yaml"

    SECRET_KEY = f"{SERVICE}-secret-key-{ENVIRONMENT.lower()}"
    DB_KEY = f"{ENVIRONMENT.lower()}/{SERVICE}/db/common"  # dev/parrot/db/common
    GOOGLE_USER_INFO = "https://www.googleapis.com/oauth2/v2/userinfo"

    # milot API URL (인증 요청용)
    MILOT_API_BASE_URL: str = "https://dev.api.milot.madup-dct.com"


@dataclass
class ProductionConfig(Config):
    """
    운영 환경 Config
    """

    DOCS_URL = None
    REDOC_URL = None

    SQLALCHEMY_ECHO: bool = False
    POOL_SIZE = 10
    MAX_OVERFLOW = 20

    # milot API URL (운영)
    MILOT_API_BASE_URL: str = "https://api.milot.madup-dct.com"


@dataclass
class DevelopmentConfig(Config):
    """
    개발 환경 Config
    """

    TEST_MODE = True
    SQLALCHEMY_ECHO: bool = False


@dataclass
class TestConfig(Config):
    pass


@cache
def config():
    env = Config().ENVIRONMENT.upper()
    if env == "PROD":
        return ProductionConfig()
    elif env == "DEV":
        return DevelopmentConfig()
    else:
        return TestConfig()


@ttl_cache()
def get_db_common_key():
    return secret_manager.get_secret(config().DB_KEY)


@ttl_cache()
def get_secret_key():
    return parameterstore.get_parameter_by_key(config().SECRET_KEY)


@ttl_cache()
def get_common_key():
    return secret_manager.get_secret(config().COMMON_KEY)


@ttl_cache()
def get_anthropic_key():
    """Anthropic (Claude) API 키 조회"""
    return secret_manager.get_secret(config().ANTHROPIC_KEY)


@ttl_cache()
def get_google_auth_key():
    return secret_manager.get_secret(config().GOOGLE_AUTH_KEY)


@cache
def get_gcp_key():
    """Google GCP (Gemini VertexAI) 키 조회"""
    return secret_manager.get_secret(config().GCP_KEY)


def setup_env():
    """
    LLM API 키 등 환경변수 설정

    AWS Secret Manager에서 키를 조회하여 환경변수로 설정합니다.
    - OPENAI_API_KEY: OpenAI API 키
    - ANTHROPIC_API_KEY: Anthropic (Claude) API 키
    - GOOGLE_CLOUD_PROJECT: GCP 프로젝트 ID
    """
    # OpenAI API 키
    common_key = get_common_key()
    os.environ["OPENAI_API_KEY"] = common_key.get("OPENAI_API_KEY", "")

    # Anthropic API 키
    try:
        anthropic_key = get_anthropic_key()
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass  # Anthropic 키가 없어도 무시

    # GCP 프로젝트 ID
    try:
        gcp_key = get_gcp_key()
        os.environ["GOOGLE_CLOUD_PROJECT"] = gcp_key.get("project_id", "")
    except Exception:
        pass  # GCP 키가 없어도 무시
