"""
HTTP Basic Authentication 유틸리티
"""

import logging
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from excel_tool.common.config.setting import get_odata_users, config

logger = logging.getLogger(__name__)

security = HTTPBasic()


def verify_credentials(credentials: HTTPBasicCredentials) -> Optional[str]:
    """
    사용자 인증 정보 검증

    Args:
        credentials: HTTP Basic 인증 정보

    Returns:
        인증된 사용자명 또는 None
    """
    try:
        users_data = get_odata_users()
        users = users_data.get("users", [])

        for user in users:
            # 타이밍 공격 방지를 위해 secrets.compare_digest 사용
            username_match = secrets.compare_digest(
                credentials.username.encode("utf-8"),
                user["username"].encode("utf-8")
            )
            password_match = secrets.compare_digest(
                credentials.password.encode("utf-8"),
                user["password"].encode("utf-8")
            )

            if username_match and password_match:
                return credentials.username

        return None

    except Exception as e:
        logger.warning(f"Failed to verify credentials: {e}")
        # DEV 환경에서 Secret Manager 설정이 없으면 인증 우회
        if config().ENVIRONMENT == "DEV":
            logger.warning("DEV mode: Authentication bypassed due to missing credentials")
            return credentials.username
        return None


def get_current_user(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    현재 인증된 사용자 반환 (FastAPI Dependency)

    Raises:
        HTTPException: 인증 실패 시 401 에러
    """
    username = verify_credentials(credentials)

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return username
