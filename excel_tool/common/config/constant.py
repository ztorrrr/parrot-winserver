import re

# 서비스 설정
SERVICE = "parrot"
# DB_SERVICE = "parrot-rds"
DEFAULT_REGION = "ap-northeast-2"

# Server
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8889

# CORS 설정
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

# 로깅 제외 패턴
SKIP_LOGGING_PATTERNS = [
    ".json",
    "/docs",
    "/redoc",
    "/openapi",
    "/favicon",
    ".js",
    ".css",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    "/static/",
    "/assets/",
]

SKIP_LOGGING_REGEX = re.compile(
    "|".join(f"({pattern})" for pattern in SKIP_LOGGING_PATTERNS)
)

# S3 경로 Prefix
S3_DATASET_EXCEL_PREFIX = "parrot/dataset/excel"  # Excel 파일 저장 경로
S3_PRESIGNED_URL_EXPIRY = 3600  # 1시간
