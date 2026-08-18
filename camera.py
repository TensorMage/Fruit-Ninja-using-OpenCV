from __future__ import annotations
import pygame
import config
try:
    import cv2
except Exception as exc:
    cv2 = None
    print(f"OpenCV unavailable: {exc}")


class Camera:
    def __init__(self) -> None:
        self.available = False
        self.capture = None
        if cv2 is None:
            return
        try:
            self.capture = cv2.VideoCapture(config.CAMERA_INDEX)
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
            self.available = bool(self.capture.isOpened())
            if not self.available:
                print("Camera unavailable.Hand-controlled slicing is disabled until a camera is available.")
        except Exception as exc:
            print(f"Camera initialization failed: {exc}")
            self.available = False

    def read(self):
        if not self.available or self.capture is None or cv2 is None:
            return None, None
        ok,frame=self.capture.read()
        if not ok or frame is None:
            print("Camera frame read failed.")
            self.available=False
            return None,None
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame, rgb

    def frame_to_surface(self, frame) -> pygame.Surface | None:
        if frame is None or cv2 is None:
            return None
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        return pygame.image.frombuffer(rgb.tobytes(), (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), "RGB")

    def release(self) -> None:
        if self.capture is not None:
            self.capture.release()
