"""Entry point for Spike Troll."""

from __future__ import annotations

import sys

import pygame as pg

import config as c
from game import Game
from multiplayer import LanRoom, create_room_code, validate_room_code

ROOM_BAR_H = 52


def main() -> int:
    """Run the troll platformer until quit."""
    pg.init()
    pg.display.set_caption(c.TITLE)
    screen = pg.display.set_mode((c.SCREEN_W, c.SCREEN_H))
    clock = pg.time.Clock()
    font = pg.font.SysFont("consolas", 18)
    big = pg.font.SysFont("consolas", 28, bold=True)

    game = Game()
    room: LanRoom | None = None
    room_code = ""
    room_code_input = ""
    room_status = ""
    room_panel_open = False
    is_host = False
    globe_button = pg.Rect(c.SCREEN_W - 52, 8, 40, 40)
    create_button = pg.Rect(125, 218, 170, 44)
    code_box = pg.Rect(320, 218, 350, 44)
    join_button = pg.Rect(320, 278, 150, 44)
    leave_button = pg.Rect(490, 278, 150, 44)

    def focus_code_box() -> None:
        pg.key.start_text_input()
        pg.key.set_text_input_rect(code_box)

    def player_count() -> int:
        if room is None:
            return 0
        return len(room.players) + 1

    def refresh_room_status() -> None:
        nonlocal room_status
        if room is None:
            return
        count = player_count()
        if count <= 1:
            room_status = "Waiting for other players…"
        else:
            room_status = f"Playing together ({count} players)"

    def open_room(code: str, *, host: bool) -> bool:
        """Enter a room. Returns True on success."""
        nonlocal room, room_code, room_status, room_code_input, is_host
        nonlocal room_panel_open
        cleaned = "".join(ch for ch in code if ch.isdigit())[:6]
        room_code_input = cleaned
        if room is not None:
            room.close()
            room = None
            room_code = ""
        try:
            room_code = validate_room_code(cleaned)
            room = LanRoom(room_code)
            room_code_input = room_code
            is_host = host
            refresh_room_status()
            # Stay in-game with the top lobby bar visible.
            room_panel_open = False
            pg.key.stop_text_input()
            return True
        except ValueError as exc:
            room_status = str(exc)
            is_host = False
            return False
        except OSError as exc:
            room_status = str(exc)
            is_host = False
            return False

    def create_room() -> None:
        nonlocal room_code_input
        room_code_input = create_room_code()
        open_room(room_code_input, host=True)

    def join_room() -> None:
        open_room(room_code_input, host=False)

    def leave_room() -> None:
        nonlocal room, room_code, room_status, is_host
        if room is not None:
            room.close()
            room = None
        room_code = ""
        is_host = False
        room_status = "You left the room."

    def append_code_digit(digit: str) -> None:
        nonlocal room_code_input
        if digit in "0123456789" and len(room_code_input) < 6:
            room_code_input += digit

    def draw_room_bar() -> None:
        """Top-of-screen lobby: code, player count, waiting/playing status."""
        assert room is not None
        count = player_count()
        refresh_room_status()

        bar = pg.Rect(0, 0, c.SCREEN_W, ROOM_BAR_H)
        pg.draw.rect(screen, (28, 36, 54), bar)
        pg.draw.line(screen, c.PLAYER, (0, ROOM_BAR_H - 1), (c.SCREEN_W, ROOM_BAR_H - 1), 2)

        role = "HOST" if is_host else "JOINED"
        code_surf = big.render(f"ROOM {room_code}", True, c.TEXT)
        screen.blit(code_surf, (16, 10))

        players_surf = font.render(f"Players: {count}", True, c.EXIT_C)
        screen.blit(players_surf, (240, 8))

        role_surf = font.render(role, True, c.WARNING)
        screen.blit(role_surf, (240, 28))

        status_surf = font.render(room_status, True, c.WARNING if count <= 1 else c.EXIT_C)
        screen.blit(status_surf, (360, 16))

        # Keep globe on the bar
        globe_button.y = 6

    running = True

    while running:
        dt = clock.tick(c.FPS) / 1000.0
        dt = min(dt, 1.0 / 30.0)
        now_ms = pg.time.get_ticks()

        # Globe sits on the room bar when in a room, else top-right corner.
        if room is None:
            globe_button.y = 8

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if globe_button.collidepoint(event.pos):
                    room_panel_open = not room_panel_open
                    if room_panel_open:
                        if room is not None:
                            room_code_input = room_code
                        focus_code_box()
                        if room is None:
                            room_status = (
                                room_status
                                or "Create a code, or type a friend's 6 digits."
                            )
                    else:
                        pg.key.stop_text_input()
                elif room_panel_open and create_button.collidepoint(event.pos):
                    create_room()
                elif room_panel_open and join_button.collidepoint(event.pos):
                    join_room()
                elif room_panel_open and leave_button.collidepoint(event.pos):
                    leave_room()
                elif room_panel_open and code_box.collidepoint(event.pos):
                    focus_code_box()
            elif event.type == pg.KEYDOWN:
                if room_panel_open:
                    if event.key == pg.K_ESCAPE:
                        room_panel_open = False
                        pg.key.stop_text_input()
                    elif event.key == pg.K_RETURN:
                        if len(room_code_input) == 6:
                            join_room()
                        else:
                            create_room()
                    elif event.key == pg.K_BACKSPACE:
                        room_code_input = room_code_input[:-1]
                    else:
                        digit = event.unicode if event.unicode in "0123456789" else ""
                        if not digit and pg.K_KP0 <= event.key <= pg.K_KP9:
                            digit = str(event.key - pg.K_KP0)
                        if not digit and pg.K_0 <= event.key <= pg.K_9:
                            digit = str(event.key - pg.K_0)
                        if digit:
                            append_code_digit(digit)
                elif event.key == pg.K_ESCAPE:
                    running = False
                elif event.key in (pg.K_UP, pg.K_SPACE, pg.K_w):
                    game.request_jump(now_ms)
                elif event.key == pg.K_r and not game.won:
                    game.reset_level(keep_message=False)
            elif event.type == pg.TEXTINPUT and room_panel_open:
                for char in event.text:
                    append_code_digit(char)

        keys = pg.key.get_pressed()
        if not room_panel_open:
            game.handle_input(keys)
            game.update(dt, now_ms)
        if room is not None:
            try:
                room.update(game.x, game.y, game.level_index)
                refresh_room_status()
            except OSError as exc:
                room_status = f"Room connection failed: {exc}"
                room.close()
                room = None
                room_code = ""
                is_host = False

        top_pad = ROOM_BAR_H if room is not None else 0
        game.draw(screen, font, big, top_pad=top_pad)

        if room is not None:
            for player in room.players.values():
                if player.level == game.level_index:
                    player_rect = pg.Rect(
                        int(player.x), int(player.y), c.PLAYER_W, c.PLAYER_H
                    )
                    pg.draw.rect(screen, (255, 130, 210), player_rect, border_radius=4)
                    friend_label = font.render("Friend", True, (255, 200, 230))
                    screen.blit(friend_label, (player_rect.x - 4, player_rect.y - 22))
            draw_room_bar()

        pg.draw.rect(screen, (48, 60, 82), globe_button, border_radius=8)
        center = globe_button.center
        pg.draw.circle(screen, c.TEXT, center, 12, 2)
        pg.draw.ellipse(
            screen, c.TEXT, (center[0] - 6, center[1] - 12, 12, 24), 1
        )
        pg.draw.line(
            screen, c.TEXT, (center[0] - 11, center[1]), (center[0] + 11, center[1]), 1
        )

        if room_panel_open:
            overlay = pg.Surface((c.SCREEN_W, c.SCREEN_H), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 175))
            screen.blit(overlay, (0, 0))
            panel = pg.Rect(90, 105, 620, 270)
            pg.draw.rect(screen, (36, 44, 62), panel, border_radius=12)
            pg.draw.rect(screen, c.HUD, panel, 2, border_radius=12)
            screen.blit(big.render("Play together", True, c.TEXT), (125, 128))
            screen.blit(
                font.render(
                    "Same Wi-Fi: Create code, or type 6 digits then Join.",
                    True,
                    c.HUD,
                ),
                (125, 170),
            )

            pg.draw.rect(screen, (55, 120, 92), create_button, border_radius=6)
            create_label = font.render("Create code", True, c.TEXT)
            screen.blit(create_label, create_label.get_rect(center=create_button.center))
            pg.draw.rect(screen, (18, 24, 36), code_box, border_radius=6)
            pg.draw.rect(screen, c.PLAYER, code_box, 2, border_radius=6)
            shown_code = room_code_input or "Type 6-digit code"
            code_color = c.TEXT if room_code_input else c.HUD
            screen.blit(
                font.render(shown_code, True, code_color),
                (code_box.x + 12, code_box.y + 12),
            )

            pg.draw.rect(screen, (54, 93, 143), join_button, border_radius=6)
            join_label = font.render("Join room", True, c.TEXT)
            screen.blit(join_label, join_label.get_rect(center=join_button.center))
            pg.draw.rect(screen, (100, 62, 72), leave_button, border_radius=6)
            leave_label = font.render("Leave room", True, c.TEXT)
            screen.blit(leave_label, leave_label.get_rect(center=leave_button.center))
            if room is not None:
                live = (
                    f"You are in ROOM {room_code}  ·  Players: {player_count()}  ·  "
                    f"{room_status}"
                )
                screen.blit(font.render(live, True, c.EXIT_C), (125, 337))
            elif room_status:
                screen.blit(font.render(room_status, True, c.WARNING), (125, 337))
            else:
                screen.blit(
                    font.render("Enter the same code on both computers.", True, c.WARNING),
                    (125, 337),
                )

        pg.display.flip()

    if room is not None:
        room.close()
    pg.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
