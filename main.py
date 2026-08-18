from __future__ import annotations
import sys
import pygame
from game.game import FruitFury

def main() -> int:
    try:
        pygame.init()
        game=FruitFury()
        game.run()
    except Exception as exc:
        print(f"Fruit Fury could not start:{exc}")
        return 1
    finally:
        pygame.quit()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
