"""
Pydantic Models
요청/응답 스키마 정의
"""
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl



# Request Models


class ExcelGenerateRequest(BaseModel):
    """Excel 생성 요청 스키마"""

    project_id: str = Field(
        ...,
        description="프로젝트 ID (S3 저장 경로에 사용)",
        examples=["proj_001", "proj_abc"]
    )

    dataset_id: str = Field(
        ...,
        description="데이터셋 ID (S3 저장 경로에 사용)",
        examples=["ds_abc123", "dataset_001"]
    )

    template_id: str = Field(
        ...,
        description="템플릿 ID (S3 저장 경로에 사용)",
        examples=["tvf_wkdiw121", "tvf_campaign_result"]
    )

    tvf_name: str = Field(
        ...,
        description="TVF 이름 (파일명에 사용)",
        examples=["monthly_summary", "campaign_result"]
    )

    odata_url: str = Field(
        ...,
        description="OData 엔드포인트 URL",
        examples=["https://api.example.com/dataset/{dataset_id}/templates/{template_id}/odata"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "proj_001",
                "dataset_id": "ds_abc123",
                "template_id": "tvf_wkdiw121",
                "tvf_name": "monthly_summary",
                "odata_url": "https://api.example.com/dataset/{dataset_id}/templates/{template_id}/odata"
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

    project_id: str = Field(
        ...,
        description="프로젝트 ID"
    )

    dataset_id: str = Field(
        ...,
        description="데이터셋 ID"
    )

    template_id: str = Field(
        ...,
        description="템플릿 ID"
    )

    tvf_name: str = Field(
        ...,
        description="TVF 이름"
    )

    odata_url: str = Field(
        ...,
        description="Excel에 포함된 OData URL"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "download_url": "https://s3.amazonaws.com/bucket/parrot/dataset/excel/proj_001/ds_abc123/tvf_wkdiw121/ds_abc123_monthly_summary.xlsx?...",
                "s3_key": "parrot/dataset/excel/proj_001/ds_abc123/tvf_wkdiw121/ds_abc123_monthly_summary.xlsx",
                "expires_in": 3600,
                "filename": "ds_abc123_monthly_summary.xlsx",
                "project_id": "proj_001",
                "dataset_id": "ds_abc123",
                "template_id": "tvf_wkdiw121",
                "tvf_name": "monthly_summary",
                "odata_url": "https://api.example.com/dataset/{dataset_id}/templates/{template_id}/odata"
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
