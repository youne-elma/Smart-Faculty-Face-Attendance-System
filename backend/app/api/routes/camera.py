from fastapi import APIRouter, HTTPException, Response

from app.services.camera.esp32_camera import (
    CameraConnectionError,
    CameraFrameDecodeError,
    CameraStreamFrameError,
    Esp32CameraClient,
)

router = APIRouter()


@router.get("/status")
def camera_status() -> dict[str, object]:
    client = Esp32CameraClient()
    return client.status()


@router.get("/snapshot")
def camera_snapshot() -> Response:
    client = Esp32CameraClient()

    try:
        image_bytes = client.fetch_snapshot()
    except CameraConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except CameraStreamFrameError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return Response(content=image_bytes, media_type="image/jpeg")


@router.get("/frame-info")
def camera_frame_info() -> dict[str, object]:
    client = Esp32CameraClient()

    try:
        return client.frame_info()
    except CameraConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except CameraStreamFrameError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except CameraFrameDecodeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
