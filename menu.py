from __future__ import annotations

import pygame

import config
from game.modes import ModeName
from ui.buttons import Button


def title_fonts() -> tuple[pygame.font.Font, pygame.font.Font, pygame.font.Font]:
    return (
        pygame.font.SysFont("impact", 84),
        pygame.font.SysFont("trebuchetms", 28, bold=True),
        pygame.font.SysFont("trebuchetms", 23, bold=True),
    )


class MainMenu:
    def __init__(self) -> None:
        self.title_font, self.subtitle_font, self.button_font = title_fonts()
        labels = [
            ("Classic", ModeName.CLASSIC.value),
            ("Time Rush", ModeName.TIME_RUSH.value),
            ("Bomb Rush", ModeName.BOMB_RUSH.value),
            ("Combo Master", ModeName.COMBO_MASTER.value),
            ("Boss Mode", ModeName.BOSS_MODE.value),
            ("Leaderboard", "leaderboard"),
            ("Quit", "quit"),
        ]
        self.buttons: list[Button] = []
        start_y = 245
        for i, (label, action) in enumerate(labels):
            rect = pygame.Rect(0, start_y + i * 58, 310, 44)
            rect.centerx = config.SCREEN_WIDTH // 2
            self.buttons.append(Button(rect, label, action))

    def draw_background(self, surface: pygame.Surface) -> None:
        surface.fill((34, 20, 38))
        for y in range(0, config.SCREEN_HEIGHT, 8):
            shade = 38 + int(40 * y / config.SCREEN_HEIGHT)
            pygame.draw.line(surface, (shade, 24, shade + 12), (0, y), (config.SCREEN_WIDTH, y))
        for x in range(-180, config.SCREEN_WIDTH + 220, 90):
            pygame.draw.line(surface, (255, 169, 191), (x, config.SCREEN_HEIGHT), (x + 330, 0), 2)
        pygame.draw.rect(surface, (24, 48, 62), (0, config.SCREEN_HEIGHT - 92, config.SCREEN_WIDTH, 92))
        for x in range(40, config.SCREEN_WIDTH, 120):
            pygame.draw.arc(surface, (109, 184, 188), (x, config.SCREEN_HEIGHT - 68, 90, 42), 3.2, 6.1, 3)
        petal_color = (255, 180, 202)
        for x, y in ((108, 112), (180, 190), (1090, 105), (1170, 222), (980, 575), (202, 535)):
            pygame.draw.ellipse(surface, petal_color, (x, y, 16, 9))
            pygame.draw.line(surface, (108, 38, 74), (x + 3, y + 4), (x + 13, y + 5), 1)

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_background(surface)
        mouse = pygame.mouse.get_pos()
        title = self.title_font.render("FRUIT FURY", True, (255, 231, 151))
        shadow = self.title_font.render("FRUIT FURY", True, (67, 13, 47))
        surface.blit(shadow, shadow.get_rect(center=(config.SCREEN_WIDTH // 2 + 5, 108)))
        surface.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, 102)))
        subtitle = self.subtitle_font.render("HAND-TRACKED BLADE ARENA", True, (255, 219, 229))
        surface.blit(subtitle, subtitle.get_rect(center=(config.SCREEN_WIDTH // 2, 168)))
        for button in self.buttons:
            button.draw(surface, self.button_font, mouse)

    def handle(self, event: pygame.event.Event) -> str | None:
        for button in self.buttons:
            action = button.handle(event)
            if action:
                return action
        return None
