from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

@dataclass(slots=True)
class Particle:
    position: pygame.Vector2
    velocity: pygame.Vector2
    color: tuple[int, int, int]
    radius: float
    lifetime: float
    age: float = 0.0
    gravity: float = 260.0

    def update(self, dt: float) -> bool:
        self.age += dt
        self.velocity.y += self.gravity * dt
        self.position += self.velocity * dt
        return self.age < self.lifetime

    def draw(self, surface: pygame.Surface) -> None:
        alpha = max(0, min(255, int(255 * (1 - self.age / self.lifetime))))
        color = (*self.color, alpha)
        layer = pygame.Surface((int(self.radius * 4), int(self.radius * 4)), pygame.SRCALPHA)
        pygame.draw.circle(layer, color, (layer.get_width() // 2, layer.get_height() // 2), int(self.radius))
        surface.blit(layer, layer.get_rect(center=self.position))


def burst(position: pygame.Vector2, color: tuple[int, int, int], count: int = 24, power: float = 360) -> list[Particle]:
    particles: list[Particle] = []
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(power * 0.25, power)
        velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
        particles.append(
            Particle(
                position=position.copy(),
                velocity=velocity,
                color=color,
                radius=random.uniform(2.5, 6.5),
                lifetime=random.uniform(0.35, 0.85),
            )
        )
    return particles
