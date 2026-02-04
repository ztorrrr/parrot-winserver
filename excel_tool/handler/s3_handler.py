"""
S3 Handler
Excel 파일 S3 업로드 및 presigned URL 생성 (common/util/s3.py 활용)
"""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from excel_tool.common.config.setting import get_config
from excel_tool.common.util.s3 import (
    S3FilePath,
    upload_file,
    generate_presigned_url,
    delete as s3_delete,
)

logger = logging.getLogger(__name__)


class S3Handler:
    """S3 파일 업로드 및 다운로드 URL 생성 핸들러"""

    def __init__(self):
        self.setting = get_config()

    def _create_s3_path(self, key: str) -> S3FilePath:
        """S3FilePath 객체 생성"""
        s3_path = S3FilePath()
        s3_path.set(self.setting.S3_BUCKET, key)
        return s3_path

    def upload_excel_file(self, file_path: str, key: str) -> str:
        """
        Excel 파일을 S3에 업로드

        Args:
            file_path: 로컬 파일 경로
            key: S3 object key

        Returns:
            업로드된 S3 URL
        """
        s3_path = self._create_s3_path(key)
        url = upload_file(file_path, s3_path)
        logger.info(f"Uploaded Excel to s3://{s3_path.bucket}/{key}")
        return url

    def get_presigned_url(self, key: str, expiry: int = None) -> str:
        """
        다운로드용 presigned URL 생성

        Args:
            key: S3 object key
            expiry: URL 만료 시간 (초), None이면 설정값 사용

        Returns:
            Presigned URL
        """
        if expiry is None:
            expiry = self.setting.S3_PRESIGNED_URL_EXPIRY

        url = generate_presigned_url(self.setting.S3_BUCKET, key, expiry)
        logger.info(f"Generated presigned URL for {key} (expires in {expiry}s)")
        return url

    def upload_dataset_excel(
        self,
        file_path: str,
        dataset_id: str,
        template_id: str,
        tvf_name: str,
        expiry: int = None
    ) -> Dict[str, Any]:
        """
        데이터셋 Excel 파일을 S3에 업로드하고 다운로드 URL 반환

        저장 경로: parrot/dataset/excel/{dataset_id}/{template_id}/{filename}
        파일명: {dataset_id}_{tvf_name}.xlsx

        Args:
            file_path: 로컬 Excel 파일 경로
            dataset_id: 데이터셋 ID
            template_id: 템플릿 ID
            tvf_name: TVF 이름
            expiry: URL 만료 시간 (초)

        Returns:
            {
                'key': S3 object key,
                'url': presigned URL,
                'filename': 파일명,
                'expires_in': 만료 시간 (초)
            }
        """
        if expiry is None:
            expiry = self.setting.S3_PRESIGNED_URL_EXPIRY

        # 파일명 생성: {dataset_id}_{tvf_name}.xlsx
        filename = f"{dataset_id}_{tvf_name}.xlsx"

        # S3 key 생성: parrot/dataset/excel/{dataset_id}/{template_id}/{filename}
        key = f"{self.setting.S3_DATASET_EXCEL_PREFIX}/{dataset_id}/{template_id}/{filename}"

        # 업로드
        self.upload_excel_file(file_path, key)

        # Presigned URL 생성
        url = self.get_presigned_url(key, expiry)

        return {
            'key': key,
            'url': url,
            'filename': filename,
            'expires_in': expiry
        }

    def delete_file(self, key: str) -> bool:
        """
        S3에서 파일 삭제

        Args:
            key: S3 object key

        Returns:
            성공 여부
        """
        try:
            s3_path = self._create_s3_path(key)
            s3_delete(s3_path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False

    def is_configured(self) -> bool:
        """S3 설정이 완료되었는지 확인"""
        return bool(self.setting.S3_BUCKET)


# 싱글톤 인스턴스
_s3_handler: Optional[S3Handler] = None


def get_s3_handler() -> S3Handler:
    """S3Handler 싱글톤 인스턴스 반환"""
    global _s3_handler
    if _s3_handler is None:
        _s3_handler = S3Handler()
    return _s3_handler
