# Parrot Windows Server

- OData 연결이 포함된 Excel 파일을 생성하는 Windows 전용 서비스.
- BigQuery TVF 결과 테이블에 대한 OData 엔드포인트 URL을 받아, Power Query가 설정된 Excel 파일을 생성하고 S3에 업로드.


## 주요 기능
- **Excel 파일 생성**: Windows COM 자동화로 OData 연결이 포함된 Excel 파일 생성
- **S3 업로드**: 생성된 Excel 파일을 S3에 업로드하고 presigned URL 반환
- AWS Secret Manager 기반 사용자 인증

## 요구사항

- **Windows Server** (Windows COM 필수)
- **Microsoft Excel**
- **Python 3.11+**
- **AWS Credentials** 설정 (S3, Secret Manager 접근용)

## 시작하기

### 1. 의존성 설치

```bash
pip install uv
uv sync
```

### 2. 서버 실행

```bash
uv run python main.py
```

서버 시작 시 표시:
```
========================================================
         Excel Generator Service
========================================================
  Environment: DEV
  Host:        0.0.0.0
  Port:        8889
  S3 Bucket:   milot-dev
========================================================
```

## API 엔드포인트


### Excel 생성

```bash
POST /excel/generate
Authorization: Basic <credentials>
Content-Type: application/json

{
  "dataset_id": "ds_abc123",
  "tvf_table_name": "tvf_monthly_summary",
  "odata_url": "https://api.example.com/odata/analytics/tvf_monthly_summary"
}
```

**응답 예시:**
```json
{
  "success": true,
  "download_url": "https://s3.amazonaws.com/...",
  "s3_key": "parrot/dataset/excel/ds_abc123/tvf_monthly_summary/ds_abc123_tvf_monthly_summary_20240201_143052.xlsx",
  "expires_in": 3600,
  "filename": "ds_abc123_tvf_monthly_summary_20240201_143052.xlsx",
  "dataset_id": "ds_abc123",
  "tvf_table_name": "tvf_monthly_summary",
  "odata_url": "https://api.example.com/odata/analytics/tvf_monthly_summary"
}
```

## S3 저장 경로

```
parrot/dataset/excel/{dataset_id}/{tvf_table_name}/{dataset_id}_{tvf_table_name}_{timestamp}.xlsx
```

## 인증 설정

- 반환된 엑셀 파일에서 데이터 로드 시 인증 필요
- AWS Secret Manager에 사용자 정보 저장:
  - **Secret Key**: `{environment}/parrot/odata/userauth`
- **형식**:
```json
{
  "users": [
    {"username": "user1", "password": "password1"},
    {"username": "user2", "password": "password2"}
  ]
}
```

## 프로젝트 구조

```
parrot-winserver/
├── main.py                              # 서버 실행
├── excel_tool/
│   ├── router.py                        # API 엔드포인트
│   ├── model.py                         # Request/Response 스키마
│   ├── common/
│   │   ├── config/
│   │   │   ├── constant.py              # 상수 정의
│   │   │   └── setting.py               # 환경별 설정
│   │   └── util/
│   │       ├── auth.py                  # HTTP Basic Auth
│   │       ├── s3.py                    # S3 유틸리티
│   │       └── secret_manager.py        # AWS Secret Manager
│   └── handler/
│       ├── excel_generator.py           # Excel COM 생성
│       └── s3_handler.py                # S3 업로드 처리
├── pyproject.toml                       # 의존성
└── CLAUDE.md                            # 개발 가이드
```