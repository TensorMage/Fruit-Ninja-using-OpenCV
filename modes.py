from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

class ModeName(str, Enum):
    CLASSIC = "Classic"
    TIME_RUSH = "Time Rush"
    BOMB_RUSH = "Bomb Rush"
    COMBO_MASTER = "Combo Master"
    BOSS_MODE = "Boss Mode"

@dataclass(frozen=True, slots=True)
class ModeSettings:
    name: ModeName
    lives: int
    duration: float | None
    spawn_multiplier: float
    bomb_probability: float
    speed_multiplier: float
    combo_multiplier_bonus: int = 0
    boss: bool = False

MODES = {
    ModeName.CLASSIC: ModeSettings(ModeName.CLASSIC, 3, None, 1.0, 0.12, 1.0),
    ModeName.TIME_RUSH: ModeSettings(ModeName.TIME_RUSH, 3, 60.0, 1.45, 0.10, 1.08),
    ModeName.BOMB_RUSH: ModeSettings(ModeName.BOMB_RUSH, 3, None, 1.20, 0.31, 1.16),
    ModeName.COMBO_MASTER: ModeSettings(ModeName.COMBO_MASTER, 3, None, 1.12, 0.10, 1.05, 1),
    ModeName.BOSS_MODE: ModeSettings(ModeName.BOSS_MODE, 3, None, 0.82, 0.16, 1.0, boss=True),
}
