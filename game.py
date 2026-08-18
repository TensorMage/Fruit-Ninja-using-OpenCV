
from __future__ import annotations
import math
import random
from enum import Enum

import pygame

import config
from cv.blade import Blade
from cv.camera import Camera
from cv.hand_tracker import HandTracker
from game.audio import SoundManager
from game.bomb import Bomb
from game.collision import segment_circle_intersects
from game.entities import FloatingText
from game.fruit import Fruit, FruitHalf, FruitKind
from game.modes import MODES, ModeName, ModeSettings
from game.particles import Particle, burst
from ui.hud import draw_hud
from ui.leaderboard import Leaderboard
from ui.buttons import Button
from ui.menu import MainMenu


class AppState(str, Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    LEADERBOARD = "leaderboard"
    NAME_ENTRY = "name_entry"
    VICTORY = "victory"


class Boss:
    def __init__(self) -> None:
        self.position = pygame.Vector2(config.SCREEN_WIDTH / 2, 180)
        self.radius = 78
        self.health = 100
        self.max_health = 100
        self.phase_time = 0.0
        self.hit_cooldown = 0.0

    def update(self, dt: float) -> None:
        self.phase_time += dt
        speed = 1.0 + (1 - self.health / self.max_health) * 1.7
        self.position.x = config.SCREEN_WIDTH / 2 + math.sin(self.phase_time * 1.6 * speed) * 360
        self.position.y = 165 + math.sin(self.phase_time * 2.2 * speed) * 70
        self.hit_cooldown = max(0.0, self.hit_cooldown - dt)

    def try_hit(self, blade: Blade) -> bool:
        if self.hit_cooldown > 0:
            return False
        for start, end in blade.segments():
            if segment_circle_intersects(start, end, self.position, self.radius):
                self.health = max(0, self.health - 8)
                self.hit_cooldown = 0.38
                return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.circle(surface, (120, 34, 92), self.position, self.radius)
        pygame.draw.circle(surface, (235, 92, 143), self.position - pygame.Vector2(18, 20), int(self.radius * 0.55))
        pygame.draw.circle(surface, (255, 228, 106), self.position, self.radius + 8, 4)
        eye_y = self.position.y - 12
        pygame.draw.circle(surface, (20, 20, 24), (int(self.position.x - 25), int(eye_y)), 8)
        pygame.draw.circle(surface, (20, 20, 24), (int(self.position.x + 25), int(eye_y)), 8)
        bar = pygame.Rect(0, 0, 420, 24)
        bar.center = (config.SCREEN_WIDTH // 2, 94)
        pygame.draw.rect(surface, (55, 25, 34), bar, border_radius=8)
        fill = bar.copy()
        fill.width = int(bar.width * self.health / self.max_health)
        pygame.draw.rect(surface, (255, 86, 104), fill, border_radius=8)
        label = font.render("BOSS", True, (255, 245, 235))
        surface.blit(label, label.get_rect(center=bar.center))


class FruitFury:
    """Complete Pygame app for webcam-controlled fruit slicing."""

    def __init__(self) -> None:
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("Fruit Fury - OpenCV Hand-Tracking Edition")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = AppState.MENU

        self.menu = MainMenu()
        self.leaderboard = Leaderboard()
        self.leaderboard_scroll = 0
        self.leaderboard_notice = ""
        self.camera = Camera()
        self.tracker = HandTracker()
        self.blade = Blade()
        self.sound = SoundManager()
        self.sound.load()

        self.font_big = pygame.font.SysFont("arialblack", 68)
        self.font_medium = pygame.font.SysFont("arial", 32, bold=True)
        self.font_small = pygame.font.SysFont("arial", 22, bold=True)
        self.font_tiny = pygame.font.SysFont("arial", 18, bold=True)

        self.mode_settings = MODES[ModeName.CLASSIC]
        self.last_camera_frame = None
        self.reset_game(self.mode_settings)
        self.player_name = ""

    def reset_game(self, settings: ModeSettings) -> None:
        self.mode_settings = settings
        self.fruits: list[Fruit] = []
        self.bombs: list[Bomb] = []
        self.halves: list[FruitHalf] = []
        self.particles: list[Particle] = []
        self.texts: list[FloatingText] = []
        self.blade = Blade()
        self.score = 0
        self.combo = 0
        self.highest_combo = 0
        self.fruits_sliced = 0
        self.bombs_hit = 0
        self.lives = settings.lives
        self.elapsed = 0.0
        self.spawn_timer = 0.25
        self.combo_timer = 0.0
        self.freeze_timer = 0.0
        self.shield_timer = 0.0
        self.screen_shake = 0.0
        self.boss = Boss() if settings.boss else None
        self.game_over_saved = False

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            dt = min(dt, 0.04)
            self.handle_events()
            self.update(dt)
            self.draw()
        self.camera.release()
        self.tracker.close()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event)
            if self.state == AppState.MENU:
                action = self.menu.handle(event)
                if action:
                    self.handle_menu_action(action)
            elif self.state in {AppState.GAME_OVER, AppState.VICTORY}:
                self.handle_game_over_click(event)
            elif self.state == AppState.LEADERBOARD:
                self.handle_leaderboard_click(event)
            elif self.state == AppState.PAUSED:
                self.handle_pause_click(event)

    def handle_key(self, event: pygame.event.Event) -> None:
        if self.state == AppState.NAME_ENTRY:
            if event.key == pygame.K_RETURN:
                self.save_score_and_menu()
            elif event.key == pygame.K_BACKSPACE:
                self.player_name = self.player_name[:-1]
            elif len(self.player_name) < 12 and event.unicode and event.unicode.isprintable():
                self.player_name += event.unicode.upper()
            return
        if event.key == pygame.K_q:
            self.running = False
        elif event.key == pygame.K_ESCAPE:
            if self.state == AppState.PLAYING:
                self.state = AppState.PAUSED
            elif self.state == AppState.PAUSED:
                self.state = AppState.PLAYING
            elif self.state in {AppState.LEADERBOARD, AppState.GAME_OVER, AppState.VICTORY}:
                self.state = AppState.MENU
        elif event.key == pygame.K_r and self.state in {AppState.PLAYING, AppState.PAUSED, AppState.GAME_OVER, AppState.VICTORY}:
            self.reset_game(self.mode_settings)
            self.state = AppState.PLAYING
        elif event.key == pygame.K_m:
            self.state = AppState.MENU

    def handle_menu_action(self, action: str) -> None:
        self.sound.play("button")
        if action == "quit":
            self.running = False
        elif action == "leaderboard":
            self.leaderboard_scroll = 0
            self.leaderboard_notice = ""
            self.state = AppState.LEADERBOARD
        else:
            mode = ModeName(action)
            self.reset_game(MODES[mode])
            self.state = AppState.PLAYING

    def update(self, dt: float) -> None:
        if self.state != AppState.PLAYING:
            return
        frame, rgb = self.camera.read()
        hand = self.tracker.track(rgb)
        blade_pos = hand.position if hand else None
        self.blade.update(blade_pos, dt)
        self.last_camera_frame = frame

        self.elapsed += dt
        self.freeze_timer = max(0.0, self.freeze_timer - dt)
        self.shield_timer = max(0.0, self.shield_timer - dt)
        self.combo_timer = max(0.0, self.combo_timer - dt)
        self.screen_shake = max(0.0, self.screen_shake - dt)
        if self.combo_timer <= 0:
            self.combo = 0
        slow = config.FREEZE_FACTOR if self.freeze_timer > 0 else 1.0

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_wave()
            self.spawn_timer = self.next_spawn_interval()

        for fruit in list(self.fruits):
            if not fruit.update(dt, slow):
                self.fruits.remove(fruit)
                if fruit.missed and self.mode_settings.name in {ModeName.CLASSIC, ModeName.COMBO_MASTER} and not fruit.is_special:
                    if self.mode_settings.name == ModeName.COMBO_MASTER:
                        self.combo = 0
                    self.lose_life(1)

        for bomb in list(self.bombs):
            if not bomb.update(dt, slow):
                self.bombs.remove(bomb)

        self.halves = [half for half in self.halves if half.update(dt, slow)]
        self.particles = [p for p in self.particles if p.update(dt)]
        self.texts = [t for t in self.texts if t.update(dt)]
        self.handle_collisions()
        self.update_boss(dt)

        if self.mode_settings.duration is not None and self.elapsed >= self.mode_settings.duration:
            self.finish_game()
        if self.lives <= 0:
            self.finish_game()

    def difficulty(self) -> float:
        raw = 1.0 + self.score * config.DIFFICULTY_PER_SCORE + self.elapsed * config.DIFFICULTY_PER_SECOND
        return min(config.MAX_DIFFICULTY, raw)

    def next_spawn_interval(self) -> float:
        interval = config.FRUIT_SPAWN_INTERVAL / (self.mode_settings.spawn_multiplier * self.difficulty())
        return random.uniform(interval * 0.65, interval * 1.18)

    def spawn_wave(self) -> None:
        difficulty = self.difficulty()
        count = 1 + int(random.random() < min(0.65, (difficulty - 1) * 0.42))
        if difficulty > 1.75 and random.random() < 0.35:
            count += 1
        for _ in range(count):
            roll = random.random()
            bomb_chance = min(0.48, self.mode_settings.bomb_probability + (difficulty - 1) * 0.035)
            if roll < bomb_chance:
                self.bombs.append(Bomb.launch(difficulty, self.mode_settings.speed_multiplier))
            else:
                kind = self.random_fruit_kind()
                self.fruits.append(Fruit.launch(difficulty, self.mode_settings.speed_multiplier, kind))

    def random_fruit_kind(self) -> FruitKind:
        if random.random() < config.SPECIAL_PROBABILITY:
            return random.choice([FruitKind.FREEZE, FruitKind.GOLDEN, FruitKind.SHIELD])
        return random.choice([FruitKind.APPLE, FruitKind.ORANGE, FruitKind.WATERMELON, FruitKind.BANANA, FruitKind.STRAWBERRY])

    def multiplier(self) -> int:
        bonus = self.mode_settings.combo_multiplier_bonus
        if self.combo >= 10:
            return 10 + bonus
        if self.combo >= 5:
            return 5 + bonus
        if self.combo >= 3:
            return 3 + bonus
        if self.combo >= 2:
            return 2 + bonus
        return 1 + bonus if self.combo > 0 and bonus else 1

    def handle_collisions(self) -> None:
        segments = self.blade.segments()
        if not segments:
            return
        for fruit in list(self.fruits):
            if any(segment_circle_intersects(start, end, fruit.position, fruit.radius + config.BLADE_RADIUS) for start, end in segments):
                self.slice_fruit(fruit)
        for bomb in list(self.bombs):
            if any(segment_circle_intersects(start, end, bomb.position, bomb.radius + config.BLADE_RADIUS) for start, end in segments):
                self.slice_bomb(bomb)

    def slice_fruit(self, fruit: Fruit) -> None:
        if fruit not in self.fruits:
            return
        self.fruits.remove(fruit)
        self.halves.extend(fruit.slice())
        self.particles.extend(burst(fruit.position, fruit.base_color, 26 if not fruit.is_special else 42))
        self.combo += 1
        self.combo_timer = config.COMBO_TIMEOUT
        self.highest_combo = max(self.highest_combo, self.combo)
        self.fruits_sliced += 1

        points = config.GOLDEN_FRUIT_SCORE if fruit.kind == FruitKind.GOLDEN else config.BASE_FRUIT_SCORE
        points *= self.multiplier()
        self.score += points
        self.texts.append(FloatingText(f"+{points}", fruit.position.copy(), (255, 241, 112), config.SCORE_FLOAT_LIFETIME))
        self.sound.play("special" if fruit.is_special else "slice")
        if fruit.kind == FruitKind.FREEZE:
            self.freeze_timer = config.FREEZE_DURATION
            self.announce("FREEZE!")
        elif fruit.kind == FruitKind.SHIELD:
            self.shield_timer = config.SHIELD_DURATION
            self.announce("SHIELD!")
        elif fruit.kind == FruitKind.GOLDEN:
            self.announce("GOLDEN!")
        elif self.combo in {3, 5, 10, 15}:
            self.sound.play("combo")
            self.announce(f"{self.combo} FRUIT COMBO!")

    def slice_bomb(self, bomb: Bomb) -> None:
        if bomb not in self.bombs:
            return
        self.bombs.remove(bomb)
        bomb.slice()
        self.particles.extend(burst(bomb.position, (255, 94, 48), 55, 520))
        self.texts.append(FloatingText("BOOM!", bomb.position.copy(), (255, 82, 54), 1.0))
        self.sound.play("bomb")
        self.bombs_hit += 1
        self.combo = 0
        self.combo_timer = 0.0
        self.screen_shake = 0.45
        if self.shield_timer > 0:
            self.shield_timer = 0
            self.announce("SHIELD BLOCK!")
        else:
            self.lose_life(1)

    def lose_life(self, amount: int) -> None:
        self.lives = max(0, self.lives - amount)
        self.screen_shake = max(self.screen_shake, 0.20)

    def update_boss(self, dt: float) -> None:
        if self.boss is None:
            return
        self.boss.update(dt)
        if self.boss.try_hit(self.blade):
            self.score += 25 * self.multiplier()
            self.combo += 1
            self.combo_timer = config.COMBO_TIMEOUT
            self.highest_combo = max(self.highest_combo, self.combo)
            self.particles.extend(burst(self.boss.position, (255, 86, 104), 35, 430))
            self.sound.play("slice")
        if random.random() < dt * (0.55 + (1 - self.boss.health / self.boss.max_health) * 1.2):
            if random.random() < 0.36:
                self.bombs.append(Bomb.launch(self.difficulty(), 1.15))
            else:
                self.fruits.append(Fruit.launch(self.difficulty(), 1.1))
        if self.boss.health <= 0:
            self.sound.play("victory")
            if self.leaderboard.qualifies(self.score):
                self.player_name = ""
                self.state = AppState.NAME_ENTRY
            else:
                self.state = AppState.VICTORY

    def announce(self, text: str) -> None:
        self.texts.append(FloatingText(text, pygame.Vector2(config.SCREEN_WIDTH / 2, 150), (255, 255, 255), 1.15))

    def finish_game(self) -> None:
        self.sound.play("game_over")
        if self.leaderboard.qualifies(self.score):
            self.player_name = ""
            self.state = AppState.NAME_ENTRY
        else:
            self.state = AppState.GAME_OVER

    def save_score_and_menu(self) -> None:
        self.leaderboard.add(self.player_name or "PLAYER", self.score, self.mode_settings.name.value)
        self.state = AppState.GAME_OVER

    def draw(self) -> None:
        if self.state == AppState.MENU:
            self.menu.draw(self.screen)
        elif self.state == AppState.LEADERBOARD:
            self.draw_leaderboard()
        elif self.state == AppState.NAME_ENTRY:
            self.draw_world()
            self.draw_name_entry()
        elif self.state in {AppState.PLAYING, AppState.PAUSED, AppState.GAME_OVER, AppState.VICTORY}:
            self.draw_world()
            if self.state == AppState.PAUSED:
                self.draw_pause()
            elif self.state == AppState.GAME_OVER:
                self.draw_game_over("GAME OVER")
            elif self.state == AppState.VICTORY:
                self.draw_game_over("VICTORY!")
        pygame.display.flip()

    def draw_world(self) -> None:
        offset = pygame.Vector2(0, 0)
        if self.screen_shake > 0:
            magnitude = int(14 * self.screen_shake)
            offset = pygame.Vector2(random.randint(-magnitude, magnitude), random.randint(-magnitude, magnitude))
        world = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.draw_background(world)
        if config.SHOW_CAMERA_PREVIEW and hasattr(self, "last_camera_frame"):
            preview = self.camera.frame_to_surface(self.last_camera_frame)
            if preview is not None:
                preview.set_alpha(config.CAMERA_PREVIEW_ALPHA)
                world.blit(preview, (0, 0))
        for fruit in self.fruits:
            fruit.draw(world)
        for bomb in self.bombs:
            bomb.draw(world)
        for half in self.halves:
            half.draw(world)
        if self.boss is not None:
            self.boss.draw(world, self.font_small)
        for particle in self.particles:
            particle.draw(world)
        self.blade.draw(world)
        for text in self.texts:
            text.draw(world, self.font_medium)
        timer = None
        if self.mode_settings.duration is not None:
            timer = self.mode_settings.duration - self.elapsed
        draw_hud(world, self.font_small, self.score, self.combo, self.multiplier(), self.lives, timer, self.shield_timer > 0)
        if not self.blade.active and len(self.blade.points) == 0:
            if not self.camera.available:
                status = "CAMERA NOT FOUND"
            elif not self.tracker.available:
                status = self.tracker.status
            else:
                status = "SHOW YOUR INDEX FINGER"
            image = self.font_small.render(status, True, (255, 218, 82))
            world.blit(image, image.get_rect(midbottom=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 78)))
        if self.freeze_timer > 0:
            freeze = self.font_small.render("FREEZE ACTIVE", True, (135, 225, 255))
            world.blit(freeze, freeze.get_rect(midtop=(config.SCREEN_WIDTH // 2, 62)))
        self.screen.blit(world, offset)

    def draw_background(self, surface: pygame.Surface) -> None:
        surface.fill((30, 20, 35))
        for y in range(0, config.SCREEN_HEIGHT, 10):
            shade = 34 + int(34 * y / config.SCREEN_HEIGHT)
            pygame.draw.line(surface, (shade, 26, shade + 13), (0, y), (config.SCREEN_WIDTH, y))
        for x in range(-100, config.SCREEN_WIDTH + 130, 115):
            pygame.draw.line(surface, (115, 50, 96), (x, 0), (x + 260, config.SCREEN_HEIGHT), 1)
        pygame.draw.rect(surface, (20, 48, 59), (0, config.SCREEN_HEIGHT - 55, config.SCREEN_WIDTH, 55))

    def panel(self, title: str) -> pygame.Rect:
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        rect = pygame.Rect(0, 0, 520, 390)
        rect.center = (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        pygame.draw.rect(self.screen, (51, 30, 53), rect, border_radius=5)
        pygame.draw.rect(self.screen, (255, 190, 207), rect, 3, border_radius=5)
        pygame.draw.line(self.screen, (255, 231, 151), (rect.left + 18, rect.top + 15), (rect.right - 18, rect.top + 15), 2)
        image = self.font_big.render(title, True, (255, 231, 151))
        self.screen.blit(image, image.get_rect(center=(rect.centerx, rect.top + 68)))
        return rect

    def draw_pause(self) -> None:
        rect = self.panel("PAUSED")
        for button in self.overlay_buttons(["Resume", "Restart", "Main Menu", "Quit"], rect):
            button.draw(self.screen, self.font_small, pygame.mouse.get_pos())

    def draw_game_over(self, title: str) -> None:
        rect = self.panel(title)
        stats = [
            f"Final Score: {self.score}",
            f"Highest Combo: {self.highest_combo}",
            f"Fruits Sliced: {self.fruits_sliced}",
            f"Bombs Hit: {self.bombs_hit}",
            f"Mode: {self.mode_settings.name.value}",
        ]
        for i, line in enumerate(stats):
            image = self.font_small.render(line, True, (245, 245, 235))
            self.screen.blit(image, image.get_rect(center=(rect.centerx, rect.top + 135 + i * 38)))
        for button in self.overlay_buttons(["Play Again", "Main Menu", "Quit"], rect, y_start=315):
            button.draw(self.screen, self.font_tiny, pygame.mouse.get_pos())

    def draw_name_entry(self) -> None:
        rect = self.panel("GAME OVER")
        lines = ["Enter your name, then press ENTER", self.player_name or "_"]
        for i, line in enumerate(lines):
            font = self.font_small if i == 0 else self.font_medium
            color = (245, 245, 235) if i == 0 else (255, 218, 82)
            image = font.render(line, True, color)
            self.screen.blit(image, image.get_rect(center=(rect.centerx, rect.top + 160 + i * 60)))

    def draw_leaderboard(self) -> None:
        self.menu.draw_background(self.screen)
        title = self.font_big.render("HALL OF BLADES", True, (255, 231, 151))
        self.screen.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, 72)))
        rows = self.leaderboard.scores
        if not rows:
            empty = self.font_medium.render("No scores yet", True, (245, 245, 235))
            self.screen.blit(empty, empty.get_rect(center=(config.SCREEN_WIDTH // 2, 250)))
        panel = pygame.Rect(0, 0, 850, 460)
        panel.center = (config.SCREEN_WIDTH // 2, 330)
        pygame.draw.rect(self.screen, (41, 25, 47), panel, border_radius=5)
        pygame.draw.rect(self.screen, (255, 187, 205), panel, 2, border_radius=5)
        headers = self.font_tiny.render("RANK        NAME                         SCORE               MODE                         DATE", True, (255, 213, 143))
        self.screen.blit(headers, (panel.left + 30, panel.top + 16))
        visible_rows = 11
        self.leaderboard_scroll = max(0, min(self.leaderboard_scroll, max(0, len(rows) - visible_rows)))
        for display_index, row in enumerate(rows[self.leaderboard_scroll : self.leaderboard_scroll + visible_rows]):
            rank = self.leaderboard_scroll + display_index + 1
            text = f"{rank:>3}         {str(row.get('name', 'PLAYER'))[:12]:<12}          {int(row.get('score', 0)):>7}        {str(row.get('mode', ''))[:18]:<18}  {str(row.get('date', ''))[:16]}"
            color = (255, 231, 151) if rank <= 3 else (248, 238, 242)
            image = self.font_tiny.render(text, True, color)
            self.screen.blit(image, (panel.left + 30, panel.top + 57 + display_index * 34))
        if rows:
            scroll_text = self.font_tiny.render(f"Showing {self.leaderboard_scroll + 1}-{min(len(rows), self.leaderboard_scroll + visible_rows)} of {len(rows)}", True, (255, 192, 209))
            self.screen.blit(scroll_text, scroll_text.get_rect(center=(config.SCREEN_WIDTH // 2, panel.bottom - 22)))
        for button in self.leaderboard_buttons():
            button.draw(self.screen, self.font_tiny, pygame.mouse.get_pos())
        notice = self.leaderboard_notice or "Mouse wheel scrolls. ESC or M returns to menu."
        hint = self.font_tiny.render(notice, True, (255, 222, 151))
        self.screen.blit(hint, hint.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 42)))

    def leaderboard_buttons(self) -> list[Button]:
        return [Button(pygame.Rect(config.SCREEN_WIDTH // 2 - 84, 590, 168, 42), "Export PDF", "export_pdf")]

    def overlay_buttons(self, labels: list[str], panel_rect: pygame.Rect, y_start: int = 142) -> list[Button]:
        buttons: list[Button] = []
        button_width = 112 if len(labels) >= 4 else 128
        gap = 12
        total_width = len(labels) * button_width + (len(labels) - 1) * gap
        start_x = panel_rect.centerx - total_width // 2
        for index, label in enumerate(labels):
            rect = pygame.Rect(start_x + index * (button_width + gap), panel_rect.top + y_start, button_width, 40)
            action = label.lower().replace(" ", "_")
            buttons.append(Button(rect, label, action))
        return buttons

    def apply_overlay_action(self, action: str | None) -> None:
        if action is None:
            return
        self.sound.play("button")
        if action in {"resume"}:
            self.state = AppState.PLAYING
        elif action in {"restart", "play_again"}:
            self.reset_game(self.mode_settings)
            self.state = AppState.PLAYING
        elif action == "main_menu":
            self.state = AppState.MENU
        elif action == "quit":
            self.running = False

    def handle_game_over_click(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        rect = pygame.Rect(0, 0, 520, 390)
        rect.center = (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        for button in self.overlay_buttons(["Play Again", "Main Menu", "Quit"], rect, y_start=315):
            self.apply_overlay_action(button.handle(event))

    def handle_leaderboard_click(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEWHEEL:
            self.leaderboard_scroll -= event.y * 3
            return
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        for button in self.leaderboard_buttons():
            if button.handle(event) == "export_pdf":
                try:
                    self.leaderboard.export_pdf()
                    self.leaderboard_notice = "PDF created: data/fruit_fury_leaderboard.pdf"
                    self.sound.play("button")
                except OSError as exc:
                    self.leaderboard_notice = f"Could not create PDF: {exc}"

    def handle_pause_click(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        rect = pygame.Rect(0, 0, 520, 390)
        rect.center = (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        for button in self.overlay_buttons(["Resume", "Restart", "Main Menu", "Quit"], rect):
            self.apply_overlay_action(button.handle(event))
