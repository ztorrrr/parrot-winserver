"""
Pydantic Models
요청/응답 스키마 정의
"""
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl



# Request Models


class ExcelGenerateRequest(BaseModel):
    """Excel 생성 요청 스키마"""

    dataset_id: str = Field(
        ...,
        description="데이터셋 ID (S3 저장 경로에 사용)",
        examples=["ds_abc123", "dataset_001"]
    )

    tvf_table_name: str = Field(
        ...,
        description="BigQuery TVF 결과 테이블명 (S3 저장 경로 및 파일명에 사용)",
        examples=["tvf_monthly_summary", "tvf_campaign_result"]
    )

    odata_url: str = Field(
        ...,
        description="OData 엔드포인트 URL",
        examples=["https://api.example.com/odata/analytics/tvf_monthly_summary"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "dataset_id": "ds_abc123",
                "tvf_table_name": "tvf_monthly_summary",
                "odata_url": "https://api.example.com/odata/analytics/tvf_monthly_summary"
            }
        }



# Response Models


class ExcelGenerateResponse(BaseModel):
    """Excel 생성 성공 응답 스키마"""

    success: bool = Field(
        default=True,
        description="성공 여부"
    )

    download_url: str = Field(
        ...,
        description="S3 presigned 다운로드 URL"
    )

    s3_key: str = Field(
        ...,
        description="S3 저장 경로 (key)"
    )

    expires_in: int = Field(
        ...,
        description="다운로드 URL 만료 시간 (초)"
    )

    filename: str = Field(
        ...,
        description="생성된 파일명"
    )

    dataset_id: str = Field(
        ...,
        description="데이터셋 ID"
    )

    tvf_table_name: str = Field(
        ...,
        description="BigQuery TVF 결과 테이블명"
    )

    odata_url: str = Field(
        ...,
        description="Excel에 포함된 OData URL"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "download_url": "https://s3.amazonaws.com/bucket/parrot/dataset/excel/ds_abc123/tvf_monthly_summary/ds_abc123_tvf_monthly_summary_20240201_143052.xlsx?...",
                "s3_key": "parrot/dataset/excel/ds_abc123/tvf_monthly_summary/ds_abc123_tvf_monthly_summary_20240201_143052.xlsx",
                "expires_in": 3600,
                "filename": "ds_abc123_tvf_monthly_summary_20240201_143052.xlsx",
                "dataset_id": "ds_abc123",
                "tvf_table_name": "tvf_monthly_summary",
                "odata_url": "https://api.example.com/odata/analytics/tvf_monthly_summary"
            }
        }


class ErrorDetail(BaseModel):
    """에러 상세 정보"""

    code: str = Field(
        ...,
        description="에러 코드"
    )

    message: str = Field(
        ...,
        description="에러 메시지"
    )

    details: Optional[str] = Field(
        None,
        description="추가 상세 정보"
    )


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""

    success: bool = Field(
        default=False,
        description="성공 여부"
    )

    error: ErrorDetail = Field(
        ...,
        description="에러 상세 정보"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "S3_NOT_CONFIGURED",
                    "message": "S3 is not configured. Please set S3_BUCKET_NAME environment variable."
                }
            }
        }


class HealthResponse(BaseModel):
    """헬스 체크 응답 스키마"""

    status: str = Field(
        ...,
        description="서비스 상태"
    )

    service: str = Field(
        ...,
        description="서비스 이름"
    )

    environment: str = Field(
        ...,
        description="실행 환경"
    )

    s3_configured: bool = Field(
        ...,
        description="S3 설정 여부"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "Excel Generator Service",
                "environment": "DEV",
                "s3_configured": True
            }
        }
