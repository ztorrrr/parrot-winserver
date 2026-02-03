#!/usr/bin/env python
"""
Excel Generator Service
OData 연결이 포함된 Excel 파일 생성 서비스
"""
import logging
import os
import shutil
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

# Python 바이트코드 캐싱 비활성화
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from excel_tool.common.config.setting import get_config
from excel_tool.router import router

# 설정 및 로거
config = get_config()
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 수명 주기 관리"""
    # Startup
    logger.info(f"Starting Excel Generator Service ({config.ENVIRONMENT})")
    yield
    # Shutdown
    logger.info("Shutting down Excel Generator Service")


# FastAPI 애플리케이션
app = FastAPI(
    title="Excel Generator Service",
    description="TVF 결과 테이블에 대한 OData 엔드포인트가 연결된 Excel 파일 생성 API",
    version="1.0.0",
    docs_url=config.DOCS_URL,
    redoc_url=config.REDOC_URL,
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(router)


def clear_pycache():
    """__pycache__ 디렉토리 정리"""
    project_root = Path(__file__).parent
    cache_dirs = list(project_root.rglob('__pycache__'))

    for cache_dir in cache_dirs:
        # .venv 디렉토리는 건너뜀
        if '.venv' in str(cache_dir):
            continue
        try:
            shutil.rmtree(cache_dir)
        except Exception:
            pass


def main():
    """서버 실행"""
    clear_pycache()

    print(f"""
========================================================
         Excel Generator Service
========================================================
  Environment: {config.ENVIRONMENT}
  Host:        {config.HOST}
  Port:        {config.PORT}
  S3 Bucket:   {config.S3_BUCKET_NAME or '(not configured)'}
========================================================

Starting server...

API Endpoints:
  Health:          http://{config.HOST}:{config.PORT}/health
  Generate Excel:  http://{config.HOST}:{config.PORT}/excel/generate
  API Docs:        http://{config.HOST}:{config.PORT}{config.DOCS_URL or '/docs'}
""")

    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.ENVIRONMENT == "DEV",
        reload_dirs=["excel_tool"] if config.ENVIRONMENT == "DEV" else None,
        reload_delay=0.25,
        log_level=config.LOG_LEVEL.lower(),
        use_colors=True,
        access_log=True
    )


if __name__ == "__main__":
    main()
