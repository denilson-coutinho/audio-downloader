from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import AfterValidator, BaseModel, Field


ALLOWED_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}


def validate_youtube_url(value: str) -> str:
    candidate = value.strip()
    try:
        parsed = urlsplit(candidate)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Informe uma URL válida do YouTube") from exc

    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname not in ALLOWED_YOUTUBE_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 80, 443}
        or not parsed.path
    ):
        raise ValueError("Informe uma URL válida do YouTube")
    return candidate


YouTubeUrl = Annotated[str, AfterValidator(validate_youtube_url)]


class DownloadRequest(BaseModel):
    url: YouTubeUrl
    format: Literal["mp3"]


class BatchDownloadRequest(BaseModel):
    urls: list[YouTubeUrl] = Field(min_length=2, max_length=10)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ErrorResponse(BaseModel):
    detail: str

