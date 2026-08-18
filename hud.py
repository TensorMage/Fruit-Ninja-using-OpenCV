from __future__ import annotations
import pygame

def draw_hud(surface: pygame.Surface, font: pygame.font.Font, score: int, combo: int, multiplier: int, lives: int, timer: float | None, shield: bool) -> None:
    white = (255, 250, 235)
    yellow = (255, 213, 75)
    score_img = font.render(f"SCORE {score}", True, white)
    combo_img = font.render(f"COMBO {combo}  x{multiplier}", True, yellow if combo else white)
    lives_img = font.render(f"LIVES {lives}", True, (255, 110, 110) if lives <= 1 else white)
    surface.blit(score_img, (28, 22))
    surface.blit(combo_img, combo_img.get_rect(midtop=(surface.get_width() // 2, 22)))
    surface.blit(lives_img, lives_img.get_rect(topright=(surface.get_width() - 28, 22)))
    y = 62
    if timer is not None:
        timer_img = font.render(f"TIME {max(0, int(timer))}", True, white)
        surface.blit(timer_img, timer_img.get_rect(topright=(surface.get_width() - 28, y)))
        y += 38
    if shield:
        shield_img = font.render("SHIELD READY", True, (160, 190, 255))
        surface.blit(shield_img, shield_img.get_rect(topright=(surface.get_width() - 28, y)))
