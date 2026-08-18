from __future__ import annotations
import math
import random
from dataclasses import dataclass
from enum import Enum
import pygame
import config

class FruitKind(str, Enum):
    APPLE = "Apple"
    ORANGE = "Orange"
    WATERMELON = "Watermelon"
    BANANA = "Banana"
    STRAWBERRY = "Strawberry"
    FREEZE = "Freeze Fruit"
    GOLDEN = "Golden Fruit"
    SHIELD = "Bomb Shield"
FRUIT_STYLES = {
    FruitKind.APPLE: ((221, 44, 50), (255, 95, 95), (115, 26, 35), 36),
    FruitKind.ORANGE: ((245, 134, 30), (255, 190, 68), (154, 82, 24), 38),
    FruitKind.WATERMELON: ((54, 184, 88), (255, 73, 98), (23, 97, 54), 48),
    FruitKind.BANANA: ((245, 214, 72), (255, 240, 135), (133, 101, 33), 40),
    FruitKind.STRAWBERRY: ((227, 43, 83), (255, 110, 135), (113, 26, 54), 32),
    FruitKind.FREEZE: ((68, 205, 255), (200, 245, 255), (28, 112, 158), 39),
    FruitKind.GOLDEN: ((255, 203, 55), (255, 246, 142), (159, 109, 25), 41),
    FruitKind.SHIELD: ((85, 120, 255), (178, 203, 255), (35, 51, 144), 39),
}
@dataclass(slots=True)
class FruitHalf:
    position: pygame.Vector2
    velocity: pygame.Vector2
    color: tuple[int, int, int]
    radius: float
    rotation: float
    rotation_speed: float
    side: int
    age: float = 0.0
    lifetime: float = 1.2

    def update(self, dt: float, slow: float = 1.0) -> bool:
        step = dt * slow
        self.age += dt
        self.velocity.y += config.GRAVITY * step
        self.position += self.velocity * step
        self.rotation += self.rotation_speed * step
        return self.age < self.lifetime and self.position.y < config.SCREEN_HEIGHT + 160

    def draw(self, surface: pygame.Surface) -> None:
        alpha = max(0, min(255, int(255 * (1 - self.age / self.lifetime))))
        size = int(self.radius * 2.4)
        layer = pygame.Surface((size, size), pygame.SRCALPHA)
        rect = pygame.Rect(0, 0, int(self.radius), int(self.radius * 1.75))
        rect.center = (size // 2 + self.side * int(self.radius * 0.25), size // 2)
        pygame.draw.ellipse(layer, (*self.color, alpha), rect)
        pygame.draw.line(layer, (255, 230, 210, alpha), (size // 2, int(size * 0.2)), (size // 2, int(size * 0.8)), 3)
        rotated = pygame.transform.rotate(layer, self.rotation)
        surface.blit(rotated, rotated.get_rect(center=self.position))


class Fruit:
    def __init__(self, kind: FruitKind, position: pygame.Vector2, velocity: pygame.Vector2, radius: float | None = None) -> None:
        self.kind = kind
        base, highlight, shadow, default_radius = FRUIT_STYLES[kind]
        self.base_color = base
        self.highlight_color = highlight
        self.shadow_color = shadow
        self.radius = radius or random.uniform(default_radius * 0.86, default_radius * 1.12)
        self.position = position
        self.velocity = velocity
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-190, 190)
        self.sliced = False
        self.missed = False
        self.is_special = kind in {FruitKind.FREEZE, FruitKind.GOLDEN, FruitKind.SHIELD}
        self.seed_offsets = [
            (random.uniform(-0.45, 0.45), random.uniform(-0.35, 0.45))
            for _ in range(8)
        ]

    @classmethod
    def launch(cls, difficulty: float, speed_multiplier: float, kind: FruitKind | None = None) -> "Fruit":
        if kind is None:
            kind = random.choice([FruitKind.APPLE, FruitKind.ORANGE, FruitKind.WATERMELON, FruitKind.BANANA, FruitKind.STRAWBERRY])
        x = random.randint(90, config.SCREEN_WIDTH - 90)
        vx = random.uniform(-250, 250) * speed_multiplier
        if x < config.SCREEN_WIDTH * 0.25:
            vx = abs(vx) + 80
        elif x > config.SCREEN_WIDTH * 0.75:
            vx = -abs(vx) - 80
        vy = random.uniform(-940, -690) * speed_multiplier * (0.92 + difficulty * 0.08)
        return cls(kind, pygame.Vector2(x, config.SCREEN_HEIGHT + 60), pygame.Vector2(vx, vy))

    def update(self, dt: float, slow: float = 1.0) -> bool:
        step = dt * slow
        self.velocity.y += config.GRAVITY * step
        self.position += self.velocity * step
        self.rotation += self.rotation_speed * step
        if self.position.y - self.radius > config.SCREEN_HEIGHT + 60:
            self.missed = not self.sliced
            return False
        return not self.sliced

    def slice(self) -> list[FruitHalf]:
        self.sliced = True
        left = FruitHalf(self.position.copy(), pygame.Vector2(-180, -120), self.base_color, self.radius, self.rotation, -260, -1)
        right = FruitHalf(self.position.copy(), pygame.Vector2(180, -120), self.highlight_color, self.radius, self.rotation, 260, 1)
        return [left, right]

    def draw(self, surface: pygame.Surface) -> None:
        size = int(self.radius * 2.5)
        layer = pygame.Surface((size, size), pygame.SRCALPHA)
        center = pygame.Vector2(size / 2, size / 2)

        if self.kind == FruitKind.BANANA:
            rect = pygame.Rect(0, 0, int(self.radius * 1.65), int(self.radius * 0.82))
            rect.center = center
            pygame.draw.arc(layer, self.base_color, rect.inflate(18, 28), math.radians(15), math.radians(185), 18)
            pygame.draw.arc(layer, self.highlight_color, rect.inflate(3, 10), math.radians(25), math.radians(175), 5)
        elif self.kind == FruitKind.SHIELD:
            pts = [(center.x, center.y - self.radius), (center.x + self.radius * 0.85, center.y - self.radius * 0.25), (center.x + self.radius * 0.55, center.y + self.radius * 0.85), (center.x, center.y + self.radius * 1.1), (center.x - self.radius * 0.55, center.y + self.radius * 0.85), (center.x - self.radius * 0.85, center.y - self.radius * 0.25)]
            pygame.draw.polygon(layer, self.base_color, pts)
            pygame.draw.polygon(layer, self.highlight_color, pts, 4)
        else:
            pygame.draw.circle(layer, self.shadow_color, center + pygame.Vector2(5, 7), int(self.radius))
            pygame.draw.circle(layer, self.base_color, center, int(self.radius))
            pygame.draw.circle(layer, self.highlight_color, center - pygame.Vector2(self.radius * 0.33, self.radius * 0.35), int(self.radius * 0.32))
            if self.kind == FruitKind.WATERMELON:
                pygame.draw.circle(layer, (35, 140, 70), center, int(self.radius), 7)
                pygame.draw.circle(layer, (248, 77, 100), center, int(self.radius * 0.72))
            if self.kind == FruitKind.STRAWBERRY:
                for x_offset, y_offset in self.seed_offsets:
                    px = center.x + x_offset * self.radius
                    py = center.y + y_offset * self.radius
                    pygame.draw.circle(layer, (255, 230, 120), (int(px), int(py)), 2)
            if self.is_special:
                pygame.draw.circle(layer, (255, 255, 255), center, int(self.radius * 1.12), 3)

        rotated = pygame.transform.rotate(layer, self.rotation)
        surface.blit(rotated, rotated.get_rect(center=self.position))
