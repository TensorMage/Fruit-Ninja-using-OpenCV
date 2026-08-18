from __future__ import annotations
from dataclasses import dataclass
from time import perf_counter
import config
try:
    import mediapipe as mp
except Exception as exc:
    mp = None
    _IMPORT_ERROR = str(exc)
else:
    _IMPORT_ERROR = ""

@dataclass(slots=True)
class HandPoint:
    position: tuple[int, int]
    wrist: tuple[int, int]
    palm: tuple[int, int]
    handedness: str = "Unknown"

class HandTracker:
    def __init__(self) -> None:
        self.available = False
        self.status = "HAND TRACKING UNAVAILABLE"
        self.landmarker = None
        self.started_at = perf_counter()
        self.last_timestamp_ms = -1

        if not config.USE_HAND_TRACKING:
            self.status = "HAND TRACKING DISABLED"
            return
        if mp is None:
            self.status = "MEDIAPIPE NOT INSTALLED"
            print(f"MediaPipe unavailable: {_IMPORT_ERROR}")
            return
        if not config.HAND_LANDMARKER_MODEL.is_file():
            self.status = "HAND MODEL MISSING"
            print(f"MediaPipe hand model missing: {config.HAND_LANDMARKER_MODEL}")
            return

        try:
            vision = mp.tasks.vision
            options = vision.HandLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(
                    model_asset_path=str(config.HAND_LANDMARKER_MODEL)
                ),
                running_mode=vision.RunningMode.VIDEO,
                num_hands=2,
                min_hand_detection_confidence=0.62,
                min_hand_presence_confidence=0.56,
                min_tracking_confidence=0.56,
            )
            self.landmarker = vision.HandLandmarker.create_from_options(options)
            self.available = True
        except Exception as exc:
            self.status = "HAND TRACKER START FAILED"
            print(f"MediaPipe HandLandmarker initialization failed: {exc}")

    def track(self, rgb_frame) -> HandPoint | None:
        if not self.available or rgb_frame is None or self.landmarker is None:
            return None
        try:
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            timestamp_ms = max(self.last_timestamp_ms + 1, int((perf_counter() - self.started_at) * 1000))
            self.last_timestamp_ms = timestamp_ms
            result = self.landmarker.detect_for_video(image, timestamp_ms)
        except Exception as exc:
            self.available = False
            self.status = "HAND TRACKING ERROR"
            print(f"MediaPipe tracking failed: {exc}")
            return None

        if not result.hand_landmarks:
            return None

        landmarks = result.hand_landmarks[0]
        handedness = "Unknown"
        if result.handedness and result.handedness[0]:
            handedness = getattr(result.handedness[0][0], "category_name", "Unknown") or "Unknown"

        return HandPoint(
            position=self._to_screen(landmarks[8].x, landmarks[8].y),
            wrist=self._to_screen(landmarks[0].x, landmarks[0].y),
            palm=self._to_screen(landmarks[9].x, landmarks[9].y),
            handedness=handedness,
        )

    @staticmethod
    def _to_screen(x_norm: float, y_norm: float) -> tuple[int, int]:
        x = int(max(0.0, min(1.0, x_norm)) * config.SCREEN_WIDTH)
        y = int(max(0.0, min(1.0, y_norm)) * config.SCREEN_HEIGHT)
        return x, y

    def close(self) -> None:
        if self.landmarker is not None:
            self.landmarker.close()
