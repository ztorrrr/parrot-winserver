"""
Excel Generator Handler
Windows COM을 사용하여 Power Query OData 연결이 포함된 Excel 파일 생성
"""
import logging
import tempfile
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ExcelGenerator:
    """
    Windows COM을 사용하여 Excel 파일을 직접 생성
    Power Query를 통한 OData 연결 설정
    """

    def __init__(self):
        """초기화"""
        self.excel = None
        self.workbook = None

    def __enter__(self):
        """Context manager 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료 - 리소스 정리"""
        self.cleanup()

    def cleanup(self):
        """Excel COM 객체 정리"""
        try:
            if self.workbook:
                try:
                    self.workbook.Close(False)
                except Exception as e:
                    logger.warning(f"Error closing workbook: {e}")
                finally:
                    self.workbook = None

            if self.excel:
                try:
                    self.excel.ScreenUpdating = True
                    self.excel.EnableEvents = True
                    self.excel.DisplayAlerts = True
                except Exception as e:
                    logger.warning(f"Error restoring Excel properties: {e}")

                try:
                    self.excel.Quit()
                except Exception as e:
                    logger.warning(f"Error quitting Excel: {e}")
                finally:
                    self.excel = None

        except Exception as e:
            logger.error(f"Error cleaning up Excel COM objects: {e}")

    def create_odata_excel(
        self,
        odata_url: str,
        table_name: str = "Data",
        output_path: Optional[str] = None,
        auth_type: str = "webapi",
        auth_token: Optional[str] = None
    ) -> str:
        """
        OData 연결이 포함된 Excel 파일 생성

        Args:
            odata_url: OData 엔드포인트 URL
            table_name: Excel 테이블 이름
            output_path: 출력 파일 경로 (None이면 임시 파일 생성)
            auth_type: 인증 방식 ("basic" | "webapi")
            auth_token: Bearer 인증 토큰 (webapi 방식일 때 사용)

        Returns:
            생성된 Excel 파일 경로
        """
        import pythoncom
        import win32com.client

        # COM 스레드 초기화
        pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)

        try:
            # 출력 경로 설정
            if output_path is None:
                output_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".xlsx",
                    dir=tempfile.gettempdir()
                )
                output_path = output_file.name
                output_file.close()
            else:
                output_path = str(Path(output_path).absolute())

            # Excel 애플리케이션 시작
            logger.info("Starting Excel COM application...")
            self.excel = self._create_excel_instance(win32com)

            # Excel이 완전히 초기화되도록 대기
            time.sleep(0.5)

            # Excel 속성 설정
            self._configure_excel_properties()

            # 새 워크북 생성
            logger.info("Creating new workbook...")
            self.workbook = self._create_workbook()

            # 첫 번째 워크시트 가져오기
            worksheet = self.workbook.Worksheets(1)
            worksheet.Name = table_name

            # Power Query M 코드 생성
            m_code = self._generate_m_code(odata_url, auth_type, auth_token)
            query_name = f"Query_{table_name}"

            # 쿼리 추가 시도
            try:
                self._add_power_query(worksheet, m_code, query_name)
            except Exception as e:
                logger.error(f"Error adding query: {e}")
                self._add_connection_guide(worksheet, odata_url, table_name, auth_type, auth_token)

            # 파일 저장
            self.workbook.SaveAs(output_path, FileFormat=51)  # xlOpenXMLWorkbook

            # 워크북 닫기
            self.workbook.Close(True)
            self.workbook = None

            # Excel 종료
            self.excel.Quit()
            self.excel = None

            return output_path

        except Exception as e:
            logger.error(f"Error creating Excel with OData connection: {e}", exc_info=True)
            self.cleanup()
            raise
        finally:
            pythoncom.CoUninitialize()

    def _create_excel_instance(self, win32com):
        """Excel 인스턴스 생성"""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                return win32com.client.DispatchEx("Excel.Application")
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.warning(f"Failed to create new Excel instance, trying existing: {e}")
                    return win32com.client.Dispatch("Excel.Application")
                logger.warning(f"Retry {retry_count}/{max_retries}: {e}")
                time.sleep(1)

    def _configure_excel_properties(self):
        """Excel 속성 설정"""
        try:
            self.excel.Visible = False
            self.excel.DisplayAlerts = False
            self.excel.ScreenUpdating = False
            self.excel.EnableEvents = False
            logger.info("Excel properties configured successfully")
        except Exception as e:
            logger.warning(f"Some Excel properties could not be set: {e}")

    def _create_workbook(self):
        """새 워크북 생성"""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                workbook = self.excel.Workbooks.Add()
                logger.info("Workbook created successfully")
                return workbook
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise
                logger.warning(f"Retry creating workbook {retry_count}/{max_retries}: {e}")
                time.sleep(1)

    def _generate_m_code(self, odata_url: str, auth_type: str, auth_token: Optional[str] = None) -> str:
        """Power Query M 코드 생성"""
        if auth_type == "webapi" and auth_token:
            return f'''
let
    Source = OData.Feed(
        "{odata_url}",
        null,
        [
            Implementation="2.0",
            Headers=[Authorization="Bearer {auth_token}"]
        ]
    )
in
    Source
'''
        else:
            return f'''
let
    Source = OData.Feed("{odata_url}", null, [Implementation="2.0"])
in
    Source
'''

    def _add_power_query(self, worksheet, m_code: str, query_name: str):
        """Power Query 추가"""
        # WorkbookQuery 객체 생성
        self.workbook.Queries.Add(
            Name=query_name,
            Formula=m_code
        )

        # 쿼리를 테이블로 로드
        list_object = worksheet.ListObjects.Add(
            SourceType=0,  # xlSrcExternal
            Source=f"OLEDB;Provider=Microsoft.Mashup.OleDb.1;Data Source=$Workbook$;Location={query_name};Extended Properties=\"\"",
            Destination=worksheet.Range("A1")
        )

        # 쿼리 테이블 설정
        query_table = list_object.QueryTable
        query_table.CommandType = 6  # xlCmdSql
        query_table.CommandText = f"SELECT * FROM [{query_name}]"
        query_table.RowNumbers = False
        query_table.FillAdjacentFormulas = False
        query_table.PreserveFormatting = True
        query_table.RefreshOnFileOpen = False
        query_table.RefreshStyle = 1  # xlInsertDeleteCells
        query_table.SavePassword = False
        query_table.SaveData = True
        query_table.AdjustColumnWidth = True
        query_table.RefreshPeriod = 0
        query_table.PreserveColumnInfo = True
        query_table.SourceConnectionFile = ""
        query_table.BackgroundQuery = True

        logger.info("Power Query connection added successfully")

    def _add_connection_guide(
        self,
        worksheet,
        odata_url: str,
        table_name: str,
        auth_type: str,
        auth_token: Optional[str] = None
    ):
        """연결 정보 및 가이드 추가 (Power Query 실패 시)"""
        try:
            worksheet.Range("A1").Value = "OData 데이터 템플릿"
            worksheet.Range("A2").Value = "URL:"
            worksheet.Range("B2").Value = odata_url
            worksheet.Range("A3").Value = "인증 방식:"
            worksheet.Range("B3").Value = "Bearer Token" if auth_type == "webapi" else "Basic (ID/PW)"

            if auth_type == "webapi" and auth_token:
                worksheet.Range("A4").Value = "인증 토큰:"
                worksheet.Range("B4").Value = f"Bearer {auth_token}"

            worksheet.Range("A6").Value = "사용 방법:"
            worksheet.Range("A7").Value = "1. 상단 '데이터' 탭 클릭"
            worksheet.Range("A8").Value = "2. '쿼리 및 연결' 클릭"
            worksheet.Range("A9").Value = "3. 쿼리를 우클릭하여 '다음으로 로드'"
            worksheet.Range("A10").Value = "4. '연결만 만들기' + '데이터 모델에 이 데이터 추가' 선택"

            if auth_type == "webapi":
                worksheet.Range("A11").Value = "5. 인증 창이 나타나면 토큰이 이미 설정되어 있습니다."
            else:
                worksheet.Range("A11").Value = "5. 인증 창에서 '기본' 탭 선택 후 ID/PW 입력"

            # 서식 설정
            worksheet.Range("A1").Font.Bold = True
            worksheet.Range("A1").Font.Size = 14
            worksheet.Range("A2:A11").Font.Bold = True
            worksheet.Range("B2:B4").Font.Color = -16776961  # 파란색
            worksheet.Columns("A:B").AutoFit()

        except Exception as e:
            logger.error(f"Error adding connection guide: {e}")


def create_excel_with_odata(
    odata_url: str,
    table_name: str = "Data",
    output_path: Optional[str] = None,
    auth_type: str = "webapi",
    auth_token: Optional[str] = None
) -> str:
    """
    편의 함수: OData 연결이 포함된 Excel 파일 생성

    Args:
        odata_url: OData 엔드포인트 URL
        table_name: Excel 테이블 이름
        output_path: 출력 파일 경로
        auth_type: 인증 방식 ("basic" | "webapi")
        auth_token: Bearer 인증 토큰 (webapi 방식일 때 사용)

    Returns:
        생성된 Excel 파일 경로
    """
    generator = ExcelGenerator()
    try:
        return generator.create_odata_excel(odata_url, table_name, output_path, auth_type, auth_token)
    finally:
        generator.cleanup()
