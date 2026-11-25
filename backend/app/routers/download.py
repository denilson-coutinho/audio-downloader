from collections.abc import Awaitable

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas import BatchDownloadRequest, DownloadRequest, ErrorResponse
from app.services.downloader import (
    DownloadedFile,
    DownloadFailedError,
    FFmpegUnavailableError,
    ProcessingTimeoutError,
    VideoUnavailableError,
    download_audio_with_timeout,
    download_zip_with_timeout,
)


router = APIRouter(prefix="/api", tags=["download"])
error_responses = {
    400: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
    504: {"model": ErrorResponse},
}


@router.post("/download", response_class=FileResponse, responses=error_responses)
async def download(request: DownloadRequest, background_tasks: BackgroundTasks) -> FileResponse:
    return await _file_response(
        download_audio_with_timeout(request.url, settings), "audio/mpeg", background_tasks
    )


@router.post("/download/zip", response_class=FileResponse, responses=error_responses)
async def download_zip(
    request: BatchDownloadRequest, background_tasks: BackgroundTasks
) -> FileResponse:
    return await _file_response(
        download_zip_with_timeout(request.urls, settings), "application/zip", background_tasks
    )


async def _file_response(
    work: Awaitable[DownloadedFile], media_type: str, background_tasks: BackgroundTasks
) -> FileResponse:
    try:
        result = await work
    except VideoUnavailableError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FFmpegUnavailableError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except DownloadFailedError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ProcessingTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc

    background_tasks.add_task(result.cleanup)
    return FileResponse(
        path=result.path,
        media_type=media_type,
        filename=result.filename,
        background=background_tasks,
    )

