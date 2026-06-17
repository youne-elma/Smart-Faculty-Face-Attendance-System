from threading import Event, RLock, Thread
from time import sleep

from app.config.settings import settings
from app.models.attendance import AttendanceRecognitionResult, IdentificationStatus
from app.services.attendance.attendance_service import (
    AttendanceService,
    AttendanceSessionNotFoundError,
)
from app.services.camera.esp32_leds import Esp32LedClient, LedControlError


class IdentificationAlreadyRunningError(RuntimeError):
    pass


class IdentificationManager:
    def __init__(self) -> None:
        self._lock = RLock()
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._session_id: int | None = None
        self._last_result: AttendanceRecognitionResult | None = None
        self._last_error: str | None = None

    def start(self, session_id: int) -> IdentificationStatus:
        if AttendanceService().repository.get_session(session_id) is None:
            raise AttendanceSessionNotFoundError(f"Attendance session not found: {session_id}")

        with self._lock:
            if self._thread and self._thread.is_alive():
                if self._session_id == session_id:
                    return self.status()
                raise IdentificationAlreadyRunningError(
                    f"Identification is already running for session {self._session_id}"
                )

            self._stop_event.clear()
            self._session_id = session_id
            self._last_result = None
            self._last_error = None
            self._thread = Thread(
                target=self._run_loop,
                args=(session_id,),
                name=f"identification-session-{session_id}",
                daemon=True,
            )
            self._thread.start()

        return self.status()

    def stop(self) -> IdentificationStatus:
        with self._lock:
            self._stop_event.set()

        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=3)

        self._safe_leds_off()
        return self.status()

    def status(self) -> IdentificationStatus:
        with self._lock:
            running = bool(self._thread and self._thread.is_alive())
            return IdentificationStatus(
                running=running,
                session_id=self._session_id if running else None,
                last_result=self._last_result,
                last_error=self._last_error,
            )

    def _run_loop(self, session_id: int) -> None:
        led_client = Esp32LedClient()
        service = AttendanceService()

        self._safe_led_call(led_client.ready, True)
        self._safe_led_call(led_client.processing, False)
        self._safe_led_call(led_client.recognized, False)

        while not self._stop_event.is_set():
            try:
                result = service.recognize_attendance(
                    session_id,
                    processing_callback=lambda enabled: self._safe_led_call(
                        led_client.processing,
                        enabled,
                    ),
                )
                self._set_last_result(result)

                should_pulse_recognized = (
                    result.recognized
                    and result.status == "present"
                    and result.message == "Attendance marked as present"
                )
                if should_pulse_recognized:
                    self._safe_led_call(led_client.recognized, True)
                    sleep(settings.recognized_led_pulse_seconds)
                    self._safe_led_call(led_client.recognized, False)
            except Exception as exc:
                self._set_last_error(str(exc))
            finally:
                self._safe_led_call(led_client.processing, False)

            self._stop_event.wait(settings.identification_loop_interval_seconds)

        self._safe_led_call(led_client.processing, False)
        self._safe_led_call(led_client.recognized, False)
        self._safe_led_call(led_client.ready, False)

    def _set_last_result(self, result: AttendanceRecognitionResult) -> None:
        with self._lock:
            self._last_result = result
            self._last_error = None

    def _set_last_error(self, error: str) -> None:
        with self._lock:
            self._last_error = error

    def _safe_led_call(self, callback, enabled: bool) -> None:
        try:
            callback(enabled)
        except LedControlError as exc:
            self._set_last_error(str(exc))

    def _safe_leds_off(self) -> None:
        try:
            Esp32LedClient().all_off()
        except LedControlError as exc:
            self._set_last_error(str(exc))


identification_manager = IdentificationManager()
