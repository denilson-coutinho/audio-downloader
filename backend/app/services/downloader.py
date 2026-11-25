from __future__ import annotations

import asyncio
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import tempfile
from threading import Event
from typing import Any
from zipfile import ZipFile

import yt_dlp
from yt_dlp.utils import DownloadError

from app.config import Settings


class DownloaderError(Exception):
    """Base error exposed by the download service."""


class FFmpegUnavailableError(DownloaderError):
    pass


class VideoUnavailableError(DownloaderError):
    pass


class DownloadFailedError(DownloaderError):
    pass


class ProcessingTimeoutError(DownloaderError):
    pass


@dataclass(slots=True)
class DownloadedFile:
    path: Path
    filename: str
    _temporary_directory: tempfile.TemporaryDirectory[str]

    def cleanup(self) -> None:
        self._temporary_directory.cleanup()


_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="media-download")


def _safe_filename(title: str | None) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._ -]+", "", title or "audio")
    normalized = re.sub(r"\s+", " ", normalized).strip(" ._-")[:120]
    return f"{normalized or 'audio'}.mp3"


def _is_unavailable(message: str) -> bool:
    markers = ("unavailable", "private video", "removed", "does not exist")
    return any(marker in message.lower() for marker in markers)


def download_audio(url: str, config: Settings) -> DownloadedFile:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise FFmpegUnavailableError(
            "FFmpeg não está instalado ou não está disponível no PATH do servidor."
        )

    temporary_directory = tempfile.TemporaryDirectory(prefix="youtube-download-")
    working_directory = Path(temporary_directory.name)
    options: dict[str, Any] = {
        "format": "bestaudio/best",
        "outtmpl": str(working_directory / "source.%(ext)s"),
        "noplaylist": True,
        "playlist_items": "1",
        "max_filesize": config.max_file_size_bytes,
        "socket_timeout": config.socket_timeout_seconds,
        "retries": 2,
        "fragment_retries": 2,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=True)

        mp3_files = list(working_directory.glob("*.mp3"))
        if not mp3_files:
            raise DownloadFailedError("Não foi possível gerar o arquivo MP3.")

        audio_path = mp3_files[0]
        if audio_path.stat().st_size > config.max_file_size_bytes:
            raise DownloadFailedError("O arquivo excede o limite permitido pelo servidor.")

        return DownloadedFile(
            path=audio_path,
            filename=_safe_filename(info.get("title") if info else None),
            _temporary_directory=temporary_directory,
        )
    except DownloadError as exc:
        temporary_directory.cleanup()
        if _is_unavailable(str(exc)):
            raise VideoUnavailableError("O vídeo não está disponível para download.") from exc
        raise DownloadFailedError("Falha ao baixar ou converter o áudio.") from exc
    except DownloaderError:
        temporary_directory.cleanup()
        raise
    except Exception as exc:
        temporary_directory.cleanup()
        raise DownloadFailedError("Falha ao baixar ou converter o áudio.") from exc


def _download_zip(urls: list[str], config: Settings, stopped: Event) -> DownloadedFile:
    temporary_directory = tempfile.TemporaryDirectory(prefix="youtube-zip-")
    zip_path = Path(temporary_directory.name) / "audios.zip"
    total_size = 0
    size_error = "O ZIP excede o limite de tamanho permitido pelo servidor."

    try:
        with ZipFile(zip_path, "w") as archive:
            for index, url in enumerate(urls, start=1):
                if stopped.is_set():
                    raise ProcessingTimeoutError()
                try:
                    audio = download_audio(url, config)
                except (VideoUnavailableError, DownloadFailedError) as exc:
                    raise type(exc)(f"Link {index}: {exc}") from exc
                try:
                    if stopped.is_set():
                        raise ProcessingTimeoutError()
                    total_size += audio.path.stat().st_size
                    if total_size > config.max_file_size_bytes:
                        raise DownloadFailedError(size_error)
                    archive.write(audio.path, arcname=f"{index:02d} - {audio.filename}")
                finally:
                    audio.cleanup()

        if zip_path.stat().st_size > config.max_file_size_bytes:
            raise DownloadFailedError(size_error)
        return DownloadedFile(zip_path, "audios.zip", temporary_directory)
    except DownloaderError:
        temporary_directory.cleanup()
        raise
    except OSError as exc:
        temporary_directory.cleanup()
        raise DownloadFailedError("Não foi possível criar o arquivo ZIP.") from exc
    except BaseException:
        temporary_directory.cleanup()
        raise


def _cleanup_late_result(future: Future[DownloadedFile]) -> None:
    try:
        future.result().cleanup()
    except Exception:
        pass


async def _run_with_timeout(
    work: Callable[[], DownloadedFile], config: Settings, stopped: Event
) -> DownloadedFile:
    concurrent_future = _executor.submit(work)
    async_future = asyncio.wrap_future(concurrent_future)
    try:
        return await asyncio.wait_for(
            async_future, timeout=config.processing_timeout_seconds
        )
    except (TimeoutError, asyncio.CancelledError) as exc:
        stopped.set()
        concurrent_future.add_done_callback(_cleanup_late_result)
        if isinstance(exc, asyncio.CancelledError):
            raise
        raise ProcessingTimeoutError(
            "O processamento excedeu o tempo limite do servidor."
        ) from exc


async def download_audio_with_timeout(url: str, config: Settings) -> DownloadedFile:
    return await _run_with_timeout(lambda: download_audio(url, config), config, Event())


async def download_zip_with_timeout(urls: list[str], config: Settings) -> DownloadedFile:
    stopped = Event()
    return await _run_with_timeout(lambda: _download_zip(urls, config, stopped), config, stopped)

