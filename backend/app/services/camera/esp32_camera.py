from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from app.config.settings import settings


class CameraConnectionError(RuntimeError):
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
        }

    def fetch_snapshot(self) -> bytes:
        urls = self._snapshot_candidates()
        last_error: CameraConnectionError | None = None

        for url in urls:
            try:
                return self._request(url)
            except CameraConnectionError as exc:
                last_error = exc

        raise CameraConnectionError(
            f"Unable to fetch a snapshot from ESP32-CAM at {self.base_url}: {last_error}"
        )

    def _snapshot_candidates(self) -> list[str]:
        return [
            urljoin(self.base_url, "/capture"),
            self.base_url,
        ]

    def _request(self, url: str, read_body: bool = True) -> bytes:
        request = Request(url, headers={"User-Agent": "pfe-face-attendance/0.1"})

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                if read_body:
                    return response.read()
                return b""
        except HTTPError as exc:
            raise CameraConnectionError(f"HTTP {exc.code} from {url}") from exc
        except URLError as exc:
            raise CameraConnectionError(f"Connection error for {url}: {exc.reason}") from exc
        except TimeoutError as exc:
            raise CameraConnectionError(f"Timeout while connecting to {url}") from exc
