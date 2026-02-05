"""
API Router
Excel 생성 관련 엔드포인트 정의
"""
import logging
import os
import platform

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from excel_tool.common.config.setting import get_config
from excel_tool.common.util.auth import get_current_user
from excel_tool.handler.excel_generator import create_excel_with_odata
from excel_tool.handler.s3_handler import get_s3_handler
from excel_tool.model import (
    ErrorResponse,
    ExcelGenerateRequest,
    ExcelGenerateResponse,
    HealthResponse,
)

logger = logging.getLogger(__name__)
config = get_config()

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="헬스 체크",
    description="서비스 상태를 확인합니다."
)
async def health_check():
    s3_handler = get_s3_handler()

    return HealthResponse(
        status="healthy",
        service="Excel Generator Service",
        environment=config.ENVIRONMENT,
        s3_configured=s3_handler.is_configured()
    )


@router.post(
    "/excel/generate",
    response_model=ExcelGenerateResponse,
    responses={
        401: {"description": "Unauthorized - Invalid credentials"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        501: {"model": ErrorResponse, "description": "Service Not Configured"},
    },
    tags=["Excel"],
    summary="Excel 파일 생성",
    description="OData 연결이 포함된 Excel 파일을 생성하고 S3 다운로드 링크를 반환합니다. (Basic Auth 필요, Token 인증 방식)"
)
async def generate_excel(
    request: ExcelGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    OData 연결이 포함된 Excel 템플릿을 생성하고 S3 다운로드 링크 반환

    - OData URL을 Power Query로 연결한 Excel 파일 생성
    - S3에 업로드 후 presigned URL 반환
    - 임시 파일은 자동 삭제

    S3 저장 경로: parrot/dataset/excel/{project_id}/{dataset_id}/{template_id}/{filename}
    파일명 형식: {dataset_id}_{tvf_name}.xlsx
    """
    # 내부 설정값
    AUTH_TYPE = "webapi"

    try:
        # S3 설정 확인
        s3_handler = get_s3_handler()
        if not s3_handler.is_configured():
            return JSONResponse(
                status_code=501,
                content=ErrorResponse(
                    success=False,
                    error={
                        "code": "S3_NOT_CONFIGURED",
                        "message": "S3 is not configured. Please set S3_BUCKET_NAME environment variable."
                    }
                ).model_dump()
            )

        # Excel 워크시트 이름: template_id 사용
        excel_worksheet_name = request.template_id

        # Excel 파일 생성
        logger.info(
            f"[{current_user}] Generating Excel for project_id={request.project_id}, dataset_id={request.dataset_id}, "
            f"template_id={request.template_id}, tvf_name={request.tvf_name}, odata_url={request.odata_url}"
        )
        output_path = create_excel_with_odata(
            odata_url=request.odata_url,
            table_name=excel_worksheet_name,
            auth_type=AUTH_TYPE,
            auth_token=request.auth_token
        )

        # S3에 업로드
        upload_result = s3_handler.upload_dataset_excel(
            file_path=output_path,
            project_id=request.project_id,
            dataset_id=request.dataset_id,
            template_id=request.template_id,
            tvf_name=request.tvf_name
        )

        # 임시 파일 삭제 (백그라운드)
        background_tasks.add_task(os.unlink, output_path)

        logger.info(f"Excel generated and uploaded: {upload_result['key']}")

        return ExcelGenerateResponse(
            success=True,
            download_url=upload_result['url'],
            s3_key=upload_result['key'],
            expires_in=upload_result['expires_in'],
            filename=upload_result['filename'],
            project_id=request.project_id,
            dataset_id=request.dataset_id,
            template_id=request.template_id,
            tvf_name=request.tvf_name,
            odata_url=request.odata_url
        )

    except ImportError as e:
        current_os = platform.system()
        error_detail = str(e)

        if current_os != "Windows":
            # 비-Windows 환경에서 요청한 경우
            logger.error(f"Unsupported OS for Excel COM: {current_os} ({error_detail})")
            return JSONResponse(
                status_code=501,
                content=ErrorResponse(
                    success=False,
                    error={
                        "code": "UNSUPPORTED_PLATFORM",
                        "message": f"이 API는 Windows 서버에서만 사용 가능합니다. 현재 서버 OS: {current_os}",
                        "details": f"Windows COM 자동화는 Windows 환경에서만 지원됩니다. (Error: {error_detail})"
                    }
                ).model_dump()
            )
        else:
            # Windows이지만 pywin32가 설치되지 않은 경우
            logger.error(f"pywin32 not installed on Windows: {error_detail}")
            return JSONResponse(
                status_code=501,
                content=ErrorResponse(
                    success=False,
                    error={
                        "code": "PYWIN32_NOT_INSTALLED",
                        "message": "pywin32 모듈이 설치되지 않았습니다. Excel COM 자동화를 위해 pywin32를 설치해주세요.",
                        "details": f"pip install pywin32 명령으로 설치할 수 있습니다. (Error: {error_detail})"
                    }
                ).model_dump()
            )

    except Exception as e:
        logger.error(f"Error generating Excel: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                success=False,
                error={
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            ).model_dump()
        )
