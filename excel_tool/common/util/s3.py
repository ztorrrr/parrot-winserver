"""
AWS S3 유틸리티
"""

import enum
import logging
import mimetypes
import os
import time
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError
from excel_tool.common.config.setting import config

logger = logging.getLogger(__name__)


class ExistCheckType(enum.Enum):
    FILE = "file"
    FOLDER = "folder"


class S3FilePath:
    def __init__(self):
        self.bucket = config().S3_BUCKET
        self.key = None

    @property
    def path(self):
        return os.path.join(self.bucket, self.key)

    @path.setter
    def path(self, filepath: str):
        if filepath.startswith("s3://"):
            filepath = filepath[len("s3://") :]

        ret = filepath.split("/", 1)
        self.bucket = ret[0]
        self.key = ret[1]

    def set(self, bucket, key):
        self.bucket = bucket
        self.key = key
        return self

    @property
    def filename(self):
        return os.path.basename(self.key) if self.key else None

    def _to_json(self) -> str:
        return self.path

    def __repr__(self):
        return self.path


class S3FilePaths:
    @staticmethod
    def serialize(paths: list) -> str:
        """S3FilePath 배열을 문자열로 직렬화"""
        str_list = []
        for path in paths:
            str_list.append(path.path)
        return ",".join(str_list)

    @staticmethod
    def deserialize(stream: str):
        """문자열을 S3FilePath 배열로 역직렬화"""
        if not stream:
            return None

        paths = []
        for s in stream.split(","):
            s3path = S3FilePath()
            s3path.path = s
            paths.append(s3path)
        return paths


DEFAULT_LOCAL_PATH = "/tmp"


def download_file(
    s3_path: S3FilePath,
    download_path=DEFAULT_LOCAL_PATH,
) -> str:
    """S3에서 로컬로 파일 다운로드"""
    local_file = os.path.join(download_path, s3_path.filename)

    s3 = boto3.client("s3")

    start = time.time()
    try:
        s3.download_file(s3_path.bucket, s3_path.key, local_file)
    except Exception as e:
        raise Exception(f"fail to download s3 file {s3_path}", e)

    download_time = time.time() - start

    logger.info(
        "success to download '%s' file(%d Bytes) from s3://%s (%.3f sec)",
        local_file,
        os.path.getsize(local_file),
        s3_path.path,
        download_time,
    )

    return local_file


def upload_file(
    local_file, s3_path: S3FilePath, remove_local_file: bool = False
) -> str:
    """로컬 파일을 S3에 업로드"""
    try:
        s3 = boto3.client("s3")

        start = time.time()

        abs_file = os.path.abspath(local_file)
        file_mime_type, _ = mimetypes.guess_type(local_file)
        s3.upload_file(
            abs_file,
            s3_path.bucket,
            s3_path.key,
            ExtraArgs={"ContentType": file_mime_type} if file_mime_type else {},
        )

        upload_time = time.time() - start

        location = s3.get_bucket_location(Bucket=s3_path.bucket)["LocationConstraint"]

        url = "https://s3-%s.amazonaws.com/%s" % (location, s3_path.path)

        logger.info(
            "success to upload '%s' file(%d Bytes) to s3://%s (%.3f sec)",
            abs_file,
            os.path.getsize(abs_file),
            s3_path.path,
            upload_time,
        )
    finally:
        if remove_local_file:
            os.remove(local_file)

    return url


def delete(s3_path: S3FilePath):
    """S3 파일 삭제"""
    s3 = boto3.client("s3")

    start = time.time()

    s3.delete_object(Bucket=s3_path.bucket, Key=s3_path.key)

    delete_time = time.time() - start

    logger.info("success to delete file s3://%s (%.3f sec)", s3_path.path, delete_time)


def move_file(src: S3FilePath, dst: S3FilePath) -> S3FilePath:
    """S3 파일 이동"""
    s3 = boto3.resource("s3")

    start = time.time()

    s3.Object(src.bucket, dst.key).copy_from(CopySource=str(src))
    s3.Object(src.bucket, src.key).delete()

    rename_time = time.time() - start

    logger.info("success to rename objects s3://%s (%.3f sec)", dst.path, rename_time)

    return dst


def is_exist(
    bucket: str, path: str, target: ExistCheckType = ExistCheckType.FOLDER
) -> bool:
    """S3 파일/폴더 존재 여부 확인"""
    s3 = boto3.client("s3")

    try:
        if target == ExistCheckType.FOLDER and not path.endswith("/"):
            path += "/"

        res = s3.list_objects_v2(Bucket=bucket, Prefix=path, MaxKeys=1)
        logger.debug(res)

        if res["KeyCount"] > 0:
            return True
        else:
            return False

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            return False
        else:
            logger.error(e, exc_info=True)
            raise e
    except Exception as e:
        logger.error(e, exc_info=True)
        raise e


def list_objects(bucket: str, prefix: str, delimiter: str = "") -> List[str]:
    """S3 버킷의 객체 목록 조회 (페이지네이션 지원)"""
    s3 = boto3.client("s3")
    files = []

    try:
        # Pagination 처리
        continuation_token = None
        max_iterations = 100  # 최대 100,000개 객체 (1000 * 100)
        iteration = 0

        while True:
            iteration += 1
            if iteration > max_iterations:
                logger.warning(
                    f"S3 list_objects max iterations reached: {max_iterations} (조회된 파일: {len(files)}개)"
                )
                break

            params = {"Bucket": bucket, "Prefix": prefix, "Delimiter": delimiter}

            if continuation_token:
                params["ContinuationToken"] = continuation_token

            response = s3.list_objects_v2(**params)

            if "Contents" in response:
                files.extend([obj["Key"] for obj in response["Contents"]])

            # 더 이상 결과가 없으면 종료
            if not response.get("IsTruncated"):
                break

            continuation_token = response.get("NextContinuationToken")

        return files

    except ClientError as e:
        logger.error(f"Failed to list objects from s3://{bucket}/{prefix}: {e}")
        return []


def get_object_content(bucket: str, key: str) -> bytes:
    """S3 객체 내용 읽기"""
    s3 = boto3.client("s3")

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    except ClientError as e:
        logger.error(f"Failed to get object from s3://{bucket}/{key}: {e}")
        raise


def put_object(
    bucket: str, key: str, body: bytes, content_type: str = None, metadata: dict = None
) -> bool:
    """S3에 객체 업로드"""
    s3 = boto3.client("s3")

    try:
        args = {"Bucket": bucket, "Key": key, "Body": body}

        if content_type:
            args["ContentType"] = content_type

        if metadata:
            args["Metadata"] = metadata

        s3.put_object(**args)

        logger.info(f"Successfully uploaded to s3://{bucket}/{key}")
        return True

    except ClientError as e:
        logger.error(f"Failed to upload to s3://{bucket}/{key}: {e}")
        return False


def delete_objects_batch(bucket: str, keys: List[str]) -> int:
    """여러 S3 객체 일괄 삭제"""
    if not keys:
        return 0

    s3 = boto3.client("s3")
    deleted_count = 0

    # 최대 1000개씩 삭제
    for i in range(0, len(keys), 1000):
        batch = keys[i : i + 1000]

        try:
            response = s3.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": key} for key in batch], "Quiet": True},
            )

            deleted_count += len(response.get("Deleted", []))

            if "Errors" in response:
                for error in response["Errors"]:
                    logger.error(
                        f"Failed to delete {error['Key']}: {error['Message']}"
                    )

        except ClientError as e:
            logger.error(f"Failed to delete batch from s3://{bucket}: {e}")

    logger.info(f"Deleted {deleted_count} objects from s3://{bucket}")
    return deleted_count


def generate_presigned_url(
    bucket: str, key: str, expiration: int = 300
) -> Optional[str]:
    """S3 객체의 presigned URL 생성 - GET용 (기본 5분 유효)"""
    s3 = boto3.client("s3")

    try:
        url = s3.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expiration
        )
        return url

    except ClientError as e:
        logger.error(f"Failed to generate presigned URL for s3://{bucket}/{key}: {e}")
        return None


def generate_presigned_url_for_put(
    bucket: str,
    key: str,
    content_type: str = "application/octet-stream",
    expiration: int = 3600,
) -> Optional[str]:
    """S3 업로드용 presigned URL 생성 - PUT용 (기본 1시간 유효)"""
    s3 = boto3.client("s3")

    try:
        url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expiration,
        )
        logger.info(f"Generated upload presigned URL: s3://{bucket}/{key}")
        return url

    except ClientError as e:
        logger.error(
            f"Failed to generate upload presigned URL for s3://{bucket}/{key}: {e}"
        )
        return None


def get_object_size(bucket: str, key: str) -> Optional[int]:
    """S3 객체 크기 조회 (bytes)"""
    s3 = boto3.client("s3")

    try:
        response = s3.head_object(Bucket=bucket, Key=key)
        return response["ContentLength"]

    except ClientError as e:
        logger.error(f"Failed to get object size for s3://{bucket}/{key}: {e}")
        return None
