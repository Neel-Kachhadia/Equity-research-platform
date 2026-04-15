#!/usr/bin/env python3
"""
backend/tests/test_uploads.py

Integration tests for the S3 upload service and API endpoints.
Requires real AWS credentials in the environment (reads from .env).

Run from the backend/ directory:
    python -m pytest tests/test_uploads.py -v                   # all tests
    python -m pytest tests/test_uploads.py -v -k "not s3"       # skip live S3 calls
    python -m pytest tests/test_uploads.py -v -k "smoke"        # quick sanity only

Marks:
  s3        — tests that call real AWS S3 (need credentials + bucket)
  unit      — pure Python logic, no AWS calls
  smoke     — fast subset for CI/CD
"""

import os
import sys
from pathlib import Path

import pytest

# ── Make sure project root is on sys.path ─────────────────────────────────────
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Load .env before importing service (mirrors main.py startup)
try:
    from dotenv import load_dotenv
    env_path = BACKEND_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def aws_configured() -> bool:
    """Skip S3 tests if AWS credentials are absent."""
    configured = bool(
        os.getenv("AWS_ACCESS_KEY_ID") and
        os.getenv("AWS_SECRET_ACCESS_KEY") and
        os.getenv("S3_BUCKET_NAME")
    )
    return configured


@pytest.fixture(scope="session")
def uploaded_key(aws_configured) -> str:
    """
    Session-scoped fixture: upload a tiny test file to S3 once,
    return its file_key for subsequent tests, then delete it.
    """
    if not aws_configured:
        pytest.skip("AWS not configured — skipping live S3 test")

    from modules.uploads.service import generate_upload_url
    import requests

    result = generate_upload_url(
        file_name    = "pytest_fixture.txt",
        content_type = "text/plain",
        prefix       = "uploads/test",
    )

    # Actually PUT the file to S3
    payload = b"hello from pytest"
    resp = requests.put(
        result.upload_url,
        data    = payload,
        headers = {"Content-Type": "text/plain"},
        timeout = 30,
    )
    assert resp.status_code == 200, f"S3 PUT failed: {resp.status_code} {resp.text}"

    yield result.file_key

    # Teardown — delete the test object
    from modules.uploads.service import delete_file
    delete_file(result.file_key)


# ══════════════════════════════════════════════════════════════════════════════
# UNIT TESTS — no AWS calls
# ══════════════════════════════════════════════════════════════════════════════

class TestValidation:
    """Pure validation logic — no network calls."""

    @pytest.mark.unit
    @pytest.mark.smoke
    def test_valid_mime_passes(self):
        from modules.uploads.service import _validate_mime
        # Should not raise
        _validate_mime("application/pdf")
        _validate_mime("text/plain")
        _validate_mime("image/png")

    @pytest.mark.unit
    @pytest.mark.smoke
    def test_blocked_mime_raises(self):
        from modules.uploads.service import _validate_mime
        with pytest.raises(ValueError, match="not allowed"):
            _validate_mime("application/x-executable")

    @pytest.mark.unit
    @pytest.mark.smoke
    def test_valid_filename_passes(self):
        from modules.uploads.service import _validate_filename
        _validate_filename("report.pdf")
        _validate_filename("My File (Final v2).xlsx")
        _validate_filename("data-2024_Q1.csv")

    @pytest.mark.unit
    def test_empty_filename_raises(self):
        from modules.uploads.service import _validate_filename
        with pytest.raises(ValueError):
            _validate_filename("")

    @pytest.mark.unit
    def test_long_filename_raises(self):
        from modules.uploads.service import _validate_filename
        with pytest.raises(ValueError):
            _validate_filename("x" * 256 + ".pdf")

    @pytest.mark.unit
    def test_path_traversal_rejected_by_filename(self):
        from modules.uploads.service import _validate_filename
        with pytest.raises(ValueError):
            _validate_filename("../../etc/passwd")


class TestFileKeyGeneration:
    """File key builder tests — deterministic properties."""

    @pytest.mark.unit
    @pytest.mark.smoke
    def test_key_contains_prefix(self):
        from modules.uploads.service import _build_file_key
        key = _build_file_key("uploads", "report.pdf")
        assert key.startswith("uploads/")

    @pytest.mark.unit
    def test_key_contains_extension(self):
        from modules.uploads.service import _build_file_key
        key = _build_file_key("uploads", "document.pdf")
        assert key.endswith(".pdf")

    @pytest.mark.unit
    def test_keys_are_unique(self):
        from modules.uploads.service import _build_file_key
        keys = {_build_file_key("uploads", "test.txt") for _ in range(50)}
        assert len(keys) == 50, "File keys are not unique!"

    @pytest.mark.unit
    def test_key_contains_date_path(self):
        from modules.uploads.service import _build_file_key
        from datetime import datetime
        key = _build_file_key("filings", "annual.pdf")
        date_part = datetime.utcnow().strftime("%Y/%m")
        assert date_part in key

    @pytest.mark.unit
    def test_key_no_double_slash(self):
        from modules.uploads.service import _build_file_key
        key = _build_file_key("uploads/", "file.txt")
        assert "//" not in key


class TestCanonicalUrl:
    """S3 URL construction — no network."""

    @pytest.mark.unit
    @pytest.mark.smoke
    def test_url_format(self):
        from modules.uploads.service import _canonical_url
        from core.config import settings
        url = _canonical_url("uploads/2024/04/abc.pdf")
        assert url.startswith("https://")
        assert settings.aws.s3_bucket_name in url
        assert settings.aws.region in url
        assert "uploads/2024/04/abc.pdf" in url

    @pytest.mark.unit
    def test_path_traversal_rejected_by_download(self):
        from modules.uploads.service import generate_download_url
        with pytest.raises(ValueError):
            generate_download_url("../../secret")


class TestPydanticSchemas:
    """Pydantic request model validation."""

    @pytest.mark.unit
    @pytest.mark.smoke
    def test_valid_upload_request(self):
        from modules.uploads.schemas import GenerateUploadUrlRequest
        req = GenerateUploadUrlRequest(
            file_name = "report.pdf",
            file_type = "application/pdf",
        )
        assert req.prefix == "uploads"

    @pytest.mark.unit
    def test_invalid_prefix_rejected(self):
        from pydantic import ValidationError
        from modules.uploads.schemas import GenerateUploadUrlRequest
        with pytest.raises(ValidationError):
            GenerateUploadUrlRequest(
                file_name = "x.pdf",
                file_type = "application/pdf",
                prefix    = "../../etc",
            )

    @pytest.mark.unit
    def test_invalid_mime_format_rejected(self):
        from pydantic import ValidationError
        from modules.uploads.schemas import GenerateUploadUrlRequest
        with pytest.raises(ValidationError):
            GenerateUploadUrlRequest(
                file_name = "x.pdf",
                file_type = "notamimetype",
            )

    @pytest.mark.unit
    def test_path_traversal_in_filename_rejected(self):
        from pydantic import ValidationError
        from modules.uploads.schemas import GenerateUploadUrlRequest
        with pytest.raises(ValidationError):
            GenerateUploadUrlRequest(
                file_name = "../../../etc/passwd",
                file_type = "application/pdf",
            )

    @pytest.mark.unit
    def test_download_url_path_traversal_rejected(self):
        from pydantic import ValidationError
        from modules.uploads.schemas import GenerateDownloadUrlRequest
        with pytest.raises(ValidationError):
            GenerateDownloadUrlRequest(file_key="../secret")

    @pytest.mark.unit
    def test_metadata_max_keys_enforced(self):
        from pydantic import ValidationError
        from modules.uploads.schemas import GenerateUploadUrlRequest
        with pytest.raises(ValidationError):
            GenerateUploadUrlRequest(
                file_name = "x.pdf",
                file_type = "application/pdf",
                metadata  = {f"k{i}": "v" for i in range(11)},  # 11 keys > max 10
            )


# ══════════════════════════════════════════════════════════════════════════════
# S3 INTEGRATION TESTS — require real AWS credentials
# ══════════════════════════════════════════════════════════════════════════════

class TestPresignedUploadUrl:

    @pytest.mark.s3
    def test_generate_upload_url_returns_correct_shape(self, aws_configured):
        if not aws_configured:
            pytest.skip("AWS not configured")
        from modules.uploads.service import generate_upload_url
        result = generate_upload_url("test_doc.pdf", "application/pdf")
        assert result.upload_url.startswith("https://")
        assert "X-Amz-Signature" in result.upload_url
        assert result.file_key.startswith("uploads/")
        assert result.file_url.startswith("https://")
        assert result.file_key.endswith(".pdf")

    @pytest.mark.s3
    def test_upload_url_accepts_put_request(self, uploaded_key):
        """Verify the presigned URL successfully accepted a PUT (fixture uploads)."""
        # If `uploaded_key` fixture didn't raise, the PUT succeeded
        assert uploaded_key is not None
        assert uploaded_key.startswith("uploads/test/")


class TestPresignedDownloadUrl:

    @pytest.mark.s3
    def test_download_url_for_uploaded_file(self, uploaded_key, aws_configured):
        if not aws_configured:
            pytest.skip("AWS not configured")
        import requests
        from modules.uploads.service import generate_download_url
        result = generate_download_url(uploaded_key)
        assert result.download_url.startswith("https://")
        assert result.expires_in == 3600
        # Verify the URL is actually accessible
        resp = requests.get(result.download_url, timeout=15)
        assert resp.status_code == 200
        assert resp.content == b"hello from pytest"

    @pytest.mark.s3
    def test_download_url_for_missing_file_raises(self, aws_configured):
        if not aws_configured:
            pytest.skip("AWS not configured")
        from modules.uploads.service import generate_download_url
        with pytest.raises(FileNotFoundError):
            generate_download_url("uploads/nonexistent/does_not_exist.pdf")


class TestDeleteFile:

    @pytest.mark.s3
    def test_delete_nonexistent_returns_false(self, aws_configured):
        if not aws_configured:
            pytest.skip("AWS not configured")
        from modules.uploads.service import delete_file
        result = delete_file("uploads/nonexistent/ghost_file.txt")
        assert result is False


class TestListFiles:

    @pytest.mark.s3
    def test_list_returns_list(self, aws_configured):
        if not aws_configured:
            pytest.skip("AWS not configured")
        from modules.uploads.service import list_files
        files = list_files(prefix="uploads", max_keys=10)
        assert isinstance(files, list)
        if files:
            assert "file_key"      in files[0]
            assert "file_url"      in files[0]
            assert "size_bytes"    in files[0]
            assert "last_modified" in files[0]


# ══════════════════════════════════════════════════════════════════════════════
# FASTAPI ENDPOINT TESTS (TestClient — no real HTTP, no real AWS)
# ══════════════════════════════════════════════════════════════════════════════

class TestApiEndpoints:
    """
    Tests the FastAPI router using TestClient with mocked S3 service.
    These run without any AWS credentials.
    """

    @pytest.fixture(autouse=True)
    def patch_service(self, monkeypatch):
        """Mock out service functions so tests never hit real S3."""
        import modules.uploads.service as svc
        from modules.uploads.service import PresignedUploadResult, PresignedDownloadResult

        monkeypatch.setattr(svc, "generate_upload_url", lambda **kwargs: PresignedUploadResult(
            upload_url = "https://mock-bucket.s3.ap-south-1.amazonaws.com/uploads/mock.pdf?sig=abc",
            file_key   = "uploads/2024/04/mockuuid.pdf",
            file_url   = "https://mock-bucket.s3.ap-south-1.amazonaws.com/uploads/2024/04/mockuuid.pdf",
            fields     = {},
        ))
        monkeypatch.setattr(svc, "generate_download_url", lambda **kwargs: PresignedDownloadResult(
            download_url = "https://mock-bucket.s3.ap-south-1.amazonaws.com/uploads/mock.pdf?sig=xyz",
            file_key     = "uploads/2024/04/mockuuid.pdf",
            expires_in   = 3600,
        ))
        monkeypatch.setattr(svc, "delete_file",  lambda **kwargs: True)
        monkeypatch.setattr(svc, "list_files",   lambda **kwargs: [])

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    @pytest.mark.unit
    @pytest.mark.smoke
    def test_generate_upload_url_200(self, client):
        resp = client.post("/uploads/generate-upload-url", json={
            "file_name": "report.pdf",
            "file_type": "application/pdf",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "upload_url" in body
        assert "file_key"   in body
        assert "file_url"   in body
        assert body["method"] == "PUT"

    @pytest.mark.unit
    def test_blocked_mime_returns_422(self, client):
        resp = client.post("/uploads/generate-upload-url", json={
            "file_name": "virus.exe",
            "file_type": "application/x-msdownload",
        })
        assert resp.status_code == 422

    @pytest.mark.unit
    def test_invalid_prefix_returns_422(self, client):
        resp = client.post("/uploads/generate-upload-url", json={
            "file_name": "doc.pdf",
            "file_type": "application/pdf",
            "prefix":    "../../etc",
        })
        assert resp.status_code == 422

    @pytest.mark.unit
    @pytest.mark.smoke
    def test_generate_download_url_200(self, client):
        resp = client.post("/uploads/generate-download-url", json={
            "file_key": "uploads/2024/04/test.pdf",
        })
        assert resp.status_code == 200
        assert "download_url" in resp.json()

    @pytest.mark.unit
    @pytest.mark.smoke
    def test_delete_file_200(self, client):
        resp = client.request("DELETE", "/uploads/file", json={
            "file_key": "uploads/2024/04/test.pdf",
        })
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    @pytest.mark.unit
    def test_list_files_200(self, client):
        resp = client.get("/uploads/files?prefix=uploads&max_keys=10")
        assert resp.status_code == 200
        body = resp.json()
        assert "files" in body
        assert "count" in body

    @pytest.mark.unit
    @pytest.mark.smoke
    def test_health_endpoint(self, client):
        resp = client.get("/uploads/health")
        assert resp.status_code == 200
        assert "status" in resp.json()
