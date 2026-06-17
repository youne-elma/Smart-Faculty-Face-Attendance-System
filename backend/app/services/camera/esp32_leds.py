from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from app.config.settings import settings


class LedControlError(RuntimeError):
    pass


class Esp32LedClient:
    valid_leds = {"ready", "processing", "recognized"}

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.base_url = base_url or settings.esp32_led_base_url or settings.esp32_cam_url
        self.timeout_seconds = timeout_seconds or settings.led_timeout_seconds

    def ready(self, enabled: bool) -> None:
        self.set_led("ready", enabled)

    def processing(self, enabled: bool) -> None:
        self.set_led("processing", enabled)

    def recognized(self, enabled: bool) -> None:
        self.set_led("recognized", enabled)

    def all_off(self) -> None:
        for led in ["processing", "recognized", "ready"]:
            self.set_led(led, False)

    def set_led(self, led: str, enabled: bool) -> None:
        if led not in self.valid_leds:
            raise LedControlError(f"Unsupported LED: {led}")

        query = urlencode({"led": led, "state": "on" if enabled else "off"})
        url = f"{urljoin(self.base_url, '/control-led')}?{query}"
        request = Request(url, headers={"User-Agent": "pfe-face-attendance/0.1"})

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                response.read(128)
        except HTTPError as exc:
            raise LedControlError(f"LED control HTTP {exc.code} for {led}") from exc
        except URLError as exc:
            raise LedControlError(f"LED control connection error for {led}: {exc.reason}") from exc
        except TimeoutError as exc:
            raise LedControlError(f"LED control timeout for {led}") from exc
