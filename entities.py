from __future__ import annotations
from dataclasses import dataclass
import pygame
@dataclass(slots=True)
class FloatingText:
    text: str
    position: pygame.Vector2
    color: tuple[int, int, int]
    lifetime: float
    age: float = 0.0

    def update(self, dt: float) -> bool:
        self.age += dt
        self.position.y -= 48 * dt
        return self.age < self.lifetime

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        alpha = max(0, min(255, int(255 * (1 - self.age / self.lifetime))))
        image = font.render(self.text, True, self.color)
        image.set_alpha(alpha)
        surface.blit(image, image.get_rect(center=self.position))
