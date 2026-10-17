"""Entry point for JUMP — Geometry Dash–style auto-runner."""

from __future__ import annotations

import sys

import pygame

import config as c
from admin import AdminMenu
from game import Game
from editor import Editor
from chapters import ChapterBrowser
from level import build_secret_level
from menu import MainMenu
from path import Path, build_boss_level, build_master_level, build_path_level
from vault import Vault


def main() -> int:
    """Run menu ↔ gameplay until the player quits."""
    pygame.init()
    pygame.display.set_caption(c.TITLE)
    screen = pygame.display.set_mode((c.SCREEN_W, c.SCREEN_H))
    clock = pygame.time.Clock()

    menu = MainMenu()
    game: Game | None = None
    editor: Editor | None = None
    chapters: ChapterBrowser | None = None
    admin: AdminMenu | None = None
    vault: Vault | None = None
    path: Path | None = None
    scene = "menu"

    running = True
    while running:
        dt = clock.tick(c.FPS) / 1000.0
        dt = min(dt, 1.0 / 30.0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            if scene == "menu":
                menu.handle_event(event)
            elif game is not None:
                game.handle_event(event)
            elif editor is not None:
                editor.handle_event(event)
            elif chapters is not None:
                chapters.handle_event(event)
            elif admin is not None:
                admin.handle_event(event)
            elif vault is not None:
                vault.handle_event(event)
            elif path is not None:
                path.handle_event(event)

        if scene == "menu":
            menu.update(dt)
            if menu.choice == "play":
                game = Game()
                scene = "game"
                menu.reset()
            elif menu.choice == "editor":
                editor = Editor()
                scene = "editor"
                menu.reset()
            elif menu.choice == "chapters":
                chapters = ChapterBrowser()
                scene = "chapters"
                menu.reset()
            elif menu.choice == "admin":
                admin = AdminMenu()
                pygame.key.start_text_input()
                scene = "admin"
                menu.reset()
            elif menu.choice == "vault":
                vault = Vault(menu.vault_unlocked, menu.vault_key)
                scene = "vault"
                menu.reset()
            elif menu.choice == "quit":
                running = False
            menu.draw(screen)
        elif game is not None:
            game.update(dt)
            if game.state == "won" and game.is_first_level:
                menu.vault_key = True
            if game.state == "won" and game.path_level is not None and path is not None:
                if game.master_level:
                    menu.boss_unlocked = True
                    path.boss_unlocked = True
                elif not game.boss_level:
                    menu.path_completed.add(game.path_level)
                game = None
                scene = "path"
                continue
            if game.request_menu:
                scene = "menu"
                menu.reset()
                game = None
            else:
                game.draw(screen)
        elif editor is not None:
            editor.update(dt)
            if editor.request_play:
                if editor.request_secret:
                    game = Game(build_secret_level())
                else:
                    game = Game(
                        editor.level_data(),
                        double_jump_enabled=editor.double_jump_enabled,
                        infinite=editor.infinite_test_enabled,
                    )
                editor = None
                scene = "game"
            elif editor.request_menu:
                scene = "menu"
                menu.reset()
                editor = None
            else:
                editor.draw(screen)
        elif chapters is not None:
            chapters.update(dt)
            if chapters.level_data is not None:
                game = Game(
                    chapters.level_data,
                    double_jump_enabled=chapters.double_jump_enabled,
                    infinite=chapters.infinite_test_enabled,
                )
                chapters = None
                scene = "game"
            elif chapters.request_menu:
                scene = "menu"
                menu.reset()
                chapters = None
            else:
                chapters.draw(screen)
        elif admin is not None:
            admin.update(dt)
            if admin.action == "vault":
                menu.vault_unlocked = True
                menu.vault_key = True
                admin.action = None
                admin.message = "Vault and key unlocked for this session"
            elif admin.action == "path":
                menu.path_completed.update(range(10))
                admin.action = None
                admin.message = "All path levels unlocked for this session"
            elif admin.action == "boss":
                menu.boss_unlocked = True
                admin.action = None
                admin.message = "Boss level unlocked for this session"
            if admin.request_menu:
                pygame.key.stop_text_input()
                scene = "menu"
                menu.reset()
                admin = None
            else:
                admin.draw(screen)
        elif vault is not None:
            vault.update(dt)
            if vault.request_path:
                path = Path(menu.path_completed, menu.boss_unlocked)
                vault = None
                scene = "path"
            elif vault.request_menu:
                scene = "menu"
                menu.reset()
                vault = None
            else:
                vault.draw(screen)
        elif path is not None:
            path.update(dt)
            if path.level_to_play is not None:
                level_index = path.level_to_play
                path.level_to_play = None
                if level_index == 10:
                    game = Game(
                        build_master_level(), path_level=level_index, master_level=True
                    )
                elif level_index == 11:
                    game = Game(
                        build_boss_level(), path_level=level_index, boss_level=True
                    )
                else:
                    game = Game(path.level_data(level_index), path_level=level_index)
                scene = "game"
            elif path.request_vault:
                vault = Vault(menu.vault_unlocked, menu.vault_key)
                path = None
                scene = "vault"
            else:
                path.draw(screen)

        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
