from __future__ import annotations
import pygame
import config
class SoundManager:
    def __init__(self) -> None:
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            pygame.mixer.init()
            self.enabled = True
        except Exception as exc:
            print(f"Audio disabled: {exc}")

    def load(self) -> None:
        if not self.enabled:
            return
        names = ["slice", "bomb", "button", "combo", "special", "game_over", "victory"]
        for name in names:
            path = config.ASSETS_DIR / "sounds" / f"{name}.wav"
            if path.exists():
                try:
                    sound = pygame.mixer.Sound(path)
                    sound.set_volume(config.SOUND_VOLUME)
                    self.sounds[name] = sound
                except Exception as exc:
                    print(f"Could not load sound {path}: {exc}")

    def play(self, name: str) -> None:
        sound = self.sounds.get(name)
        if sound is not None:
            sound.play()
