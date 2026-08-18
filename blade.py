from __future__ import annotations
import math
from collections import deque
from dataclasses import dataclass
import pygame
import config

@dataclass(slots=True)
class TrailPoint:
    position: pygame.Vector2
    age: float = 0.0

class Blade:
    def __init__(self)->None:
        self.points:deque[TrailPoint]=deque(maxlen=config.MAX_TRAIL_POINTS)
        self.speed=0.0
        self.active=False

    def update(self,position:tuple[int,int]|None,dt:float)->None:
        for point in self.points:
            point.age += dt
        while self.points and self.points[0].age>config.TRAIL_POINT_LIFETIME:
            self.points.popleft()

        if position is None:
            self.active = False
            self.points.clear()
            self.speed = 0.0
            return

        current = pygame.Vector2(position)
        if self.points:
            previous = self.points[-1].position
            distance = current.distance_to(previous)
            self.speed = distance / max(dt, 0.001)
            if distance < 2:
                self.active = False
            else:
                self.active = self.speed >= config.MIN_SLICE_SPEED
        self.points.append(TrailPoint(current))

    def segments(self) -> list[tuple[pygame.Vector2, pygame.Vector2]]:
        if len(self.points) < 2 or not self.active:
            return []
        pts = [p.position for p in self.points]
        return list(zip(pts[:-1], pts[1:]))

    def draw(self, surface: pygame.Surface) -> None:
        if len(self.points) < 2:
            return
        pts = list(self.points)
        for index in range(1, len(pts)):
            a = pts[index - 1]
            b = pts[index]
            freshness = max(0.0, 1.0 - b.age / config.TRAIL_POINT_LIFETIME)
            width = max(2, int(18 * freshness))
            color = (255, 255, 255)
            glow = (90, 225, 255)
            pygame.draw.line(surface,glow,a.position, b.position,width + 8)
            pygame.draw.line(surface, color,a.position, b.position, width)
        tip = pts[-1].position
        pulse=4+int(math.sin(pygame.time.get_ticks() * 0.014) * 2)
        pygame.draw.circle(surface,(255, 255, 255),tip,7 +pulse)
        pygame.draw.circle(surface,(55, 205, 255),tip,14+pulse,2)
