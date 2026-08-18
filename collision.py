from __future__ import annotations
import pygame
def segment_circle_intersects(
    start: pygame.Vector2,
    end: pygame.Vector2,
    center: pygame.Vector2,
    radius: float,
) -> bool:
    segment = end - start
    length_sq = segment.length_squared()
    if length_sq <= 0.0001:
        return center.distance_to(start) <= radius
    t = max(0.0, min(1.0, (center - start).dot(segment) / length_sq))
    closest = start + segment * t
    return center.distance_to(closest) <= radius
