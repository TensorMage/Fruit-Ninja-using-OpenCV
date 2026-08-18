
from __future__ import annotations
import pygame

class Button:
    def __init__(self, rect: pygame.Rect, text: str, action: str) -> None:
        self.rect = rect
        self.text = text
        self.action = action

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, mouse_pos: tuple[int, int]) -> None:
        hovered = self.rect.collidepoint(mouse_pos)
        shadow = self.rect.move(3, 4)
        color = (255, 188, 204) if hovered else (232, 88, 133)
        border = (255, 242, 224) if hovered else (83, 25, 48)
        pygame.draw.rect(surface, (41, 18, 34), shadow, border_radius=4)
        pygame.draw.rect(surface, color, self.rect, border_radius=4)
        pygame.draw.rect(surface, border, self.rect, 3, border_radius=4)
        pygame.draw.line(surface, (255, 235, 222), (self.rect.left + 8, self.rect.top + 7), (self.rect.right - 8, self.rect.top + 7), 2)
        image = font.render(self.text, True, (39, 17, 31))
        surface.blit(image, image.get_rect(center=self.rect.center))

    def handle(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            return self.action
        return None
