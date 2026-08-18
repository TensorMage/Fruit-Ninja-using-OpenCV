from __future__ import annotations
import random
import pygame
import config

class Bomb:
    def __init__(self, position: pygame.Vector2, velocity: pygame.Vector2) -> None:
        self.position = position
        self.velocity = velocity
        self.radius = random.uniform(32, 42)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-220, 220)
        self.sliced = False
        self.missed = False

    @classmethod
    def launch(cls, difficulty: float, speed_multiplier: float) -> "Bomb":
        x = random.randint(100, config.SCREEN_WIDTH - 100)
        vx = random.uniform(-230, 230) * speed_multiplier
        vy = random.uniform(-900, -650) * speed_multiplier * (0.95 + difficulty * 0.08)
        return cls(pygame.Vector2(x, config.SCREEN_HEIGHT + 70), pygame.Vector2(vx, vy))

    def update(self, dt: float, slow: float = 1.0) -> bool:
        step = dt * slow
        self.velocity.y += config.GRAVITY * step
        self.position += self.velocity * step
        self.rotation += self.rotation_speed * step
        if self.position.y - self.radius > config.SCREEN_HEIGHT + 70:
            self.missed = True
            return False
        return not self.sliced

    def slice(self) -> None:
        self.sliced = True

    def draw(self, surface: pygame.Surface) -> None:
        size = int(self.radius * 2.8)
        layer = pygame.Surface((size, size), pygame.SRCALPHA)
        center = pygame.Vector2(size / 2, size / 2)
        pygame.draw.circle(layer, (24, 26, 33), center, int(self.radius))
        pygame.draw.circle(layer, (78, 82, 95), center - pygame.Vector2(8, 10), int(self.radius * 0.45))
        pygame.draw.rect(layer, (126, 83, 39), (center.x - 7, center.y - self.radius - 12, 14, 18), border_radius=4)
        pygame.draw.line(layer, (255, 196, 64), (center.x, center.y - self.radius - 13), (center.x + 22, center.y - self.radius - 28), 4)
        pygame.draw.circle(layer, (255, 70, 49), (int(center.x + 25), int(center.y - self.radius - 30)), 7)
        rotated = pygame.transform.rotate(layer, self.rotation)
        surface.blit(rotated, rotated.get_rect(center=self.position))
