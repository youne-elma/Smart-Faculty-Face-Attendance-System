from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import cv2
import numpy as np

from app.config.settings import settings


class CameraConnectionError(RuntimeError):
    pass


class CameraFrameDecodeError(RuntimeError):
    pass


class CameraStreamFrameError(RuntimeError):
    pass


class Esp32CameraClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.base_url = base_url or settings.esp32_cam_url
        self.timeout_seconds = timeout_seconds or settings.camera_timeout_seconds

    def status(self) -> dict[str, object]:
        try:
            self._request(self.base_url, read_body=False)
        except CameraConnectionError as exc:
            return {
                "available": False,
                "url": self.base_url,
                "error": str(exc),
            }

        return {
            "available": True,
            "url": self.base_url,
            "snapshot_url": self.snapshot_url,
            "stream_url": settings.esp32_cam_stream_url,
        }

    def fetch_snapshot(self) -> bytes:
        try:
            return self.fetch_snapshot_image()
        except (CameraConnectionError, CameraFrameDecodeError):
            return self.fetch_stream_frame_image()

    def fetch_snapshot_image(self) -> bytes:
        urls = self._snapshot_candidates()
        last_error: Exception | None = None

        for url in urls:
            try:
                image_bytes = self._request(url)
                self._decode_frame(image_bytes)
                return image_bytes
            except (CameraConnectionError, CameraFrameDecodeError) as exc:
                last_error = exc

        raise CameraConnectionError(
            f"Unable to fetch a decodable snapshot from ESP32-CAM at {self.base_url}: {last_error}"
        )

    def fetch_stream_frame_image(self) -> bytes:
        stream_bytes = self._request(
            settings.esp32_cam_stream_url,
            max_bytes=settings.camera_stream_read_bytes,
        )
        return self._extract_jpeg_from_stream(stream_bytes)

    def fetch_frame(self) -> np.ndarray:
        image_bytes = self.fetch_snapshot()
        return self._decode_frame(image_bytes)

    def frame_info(self) -> dict[str, object]:
        frame = self.fetch_frame()
        height, width, channels = frame.shape
        return {
            "available": True,
            "snapshot_url": self.snapshot_url,
            "stream_url": settings.esp32_cam_stream_url,
            "width": width,
            "height": height,
            "channels": channels,
        }

    @property
    def snapshot_url(self) -> str:
        return urljoin(self.base_url, settings.esp32_cam_snapshot_path)

    def _snapshot_candidates(self) -> list[str]:
        return [
            self.snapshot_url,
            self.base_url,
        ]

    def _request(
        self,
        url: str,
        read_body: bool = True,
        max_bytes: int | None = None,
    ) -> bytes:
        request = Request(url, headers={"User-Agent": "pfe-face-attendance/0.1"})

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                if read_body:
                    if max_bytes is not None:
                        return response.read(max_bytes)
                    return response.read()
                return b""
        except HTTPError as exc:
            raise CameraConnectionError(f"HTTP {exc.code} from {url}") from exc
        except URLError as exc:
            raise CameraConnectionError(f"Connection error for {url}: {exc.reason}") from exc
        except TimeoutError as exc:
            raise CameraConnectionError(f"Timeout while connecting to {url}") from exc

    def _extract_jpeg_from_stream(self, stream_bytes: bytes) -> bytes:
        start = stream_bytes.find(b"\xff\xd8")
        end = stream_bytes.find(b"\xff\xd9", start + 2)

        if start == -1 or end == -1:
            raise CameraStreamFrameError(
                "Could not extract a JPEG frame from the ESP32-CAM stream"
            )

        return stream_bytes[start : end + 2]

    def _decode_frame(self, image_bytes: bytes) -> np.ndarray:
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if frame is None:
            raise CameraFrameDecodeError("ESP32-CAM response could not be decoded as an image")

        return frame
