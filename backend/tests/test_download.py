from io import BytesIO
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock
from zipfile import ZipFile

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.config import Settings
from app.services.downloader import DownloadedFile, DownloadFailedError, VideoUnavailableError


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not-a-url",
        "https://example.com/watch?v=abc",
        "http://localhost/video",
        "https://youtube.com.evil.example/watch?v=abc",
    ],
)
def test_rejects_invalid_urls(url: str) -> None:
    response = client.post("/api/download", json={"url": url, "format": "mp3"})
    assert response.status_code == 422


def test_rejects_unsupported_format() -> None:
    response = client.post(
        "/api/download",
        json={"url": "https://www.youtube.com/watch?v=abc", "format": "webm"},
    )
    assert response.status_code == 422


def test_download_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    mocked_download = AsyncMock(side_effect=DownloadFailedError("falha controlada"))
    monkeypatch.setattr("app.routers.download.download_audio_with_timeout", mocked_download)

    response = client.post(
        "/api/download",
        json={"url": "https://youtu.be/abcdefghijk", "format": "mp3"},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "falha controlada"}


def test_successful_download_and_temporary_file_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    temporary_directory = tempfile.TemporaryDirectory()
    audio_path = Path(temporary_directory.name) / "audio.mp3"
    audio_path.write_bytes(b"fake-mp3-content")
    result = DownloadedFile(audio_path, "sample.mp3", temporary_directory)
    mocked_download = AsyncMock(return_value=result)
    monkeypatch.setattr("app.routers.download.download_audio_with_timeout", mocked_download)

    response = client.post(
        "/api/download",
        json={"url": "https://www.youtube.com/watch?v=abcdefghijk", "format": "mp3"},
    )

    assert response.status_code == 200
    assert response.content == b"fake-mp3-content"
    assert response.headers["content-type"] == "audio/mpeg"
    assert "sample.mp3" in response.headers["content-disposition"]
    assert not audio_path.exists()


batch_urls = ["https://youtu.be/abcdefghijk", "https://youtu.be/12345678901"]


@pytest.mark.parametrize("urls", [batch_urls[:1], batch_urls * 6, [batch_urls[0], "http://localhost/video"]])
def test_rejects_invalid_batches(urls: list[str]) -> None:
    assert client.post("/api/download/zip", json={"urls": urls}).status_code == 422


@pytest.mark.parametrize("second_link_fails", [False, True])
def test_zip_download_and_cleanup(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, second_link_fails: bool
) -> None:
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))

    def mock_audio(url: str, _config: Settings) -> DownloadedFile:
        if second_link_fails and url == batch_urls[1]:
            raise VideoUnavailableError("Vídeo indisponível.")
        directory = tempfile.TemporaryDirectory()
        path = Path(directory.name) / "audio.mp3"
        path.write_bytes(url.encode())
        return DownloadedFile(path, "sample.mp3", directory)

    monkeypatch.setattr("app.services.downloader.download_audio", mock_audio)

    response = client.post("/api/download/zip", json={"urls": batch_urls})

    if second_link_fails:
        assert response.status_code == 400
        assert response.json() == {"detail": "Link 2: Vídeo indisponível."}
    else:
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert "audios.zip" in response.headers["content-disposition"]
        with ZipFile(BytesIO(response.content)) as archive:
            assert archive.namelist() == ["01 - sample.mp3", "02 - sample.mp3"]
            assert [archive.read(name) for name in archive.namelist()] == [
                url.encode() for url in batch_urls
            ]
    assert not list(tmp_path.iterdir())

