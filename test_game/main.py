"""Entry point for Spike Troll."""

from __future__ import annotations

import sys

import pygame as pg

import config as c
from game import Game
from multiplayer import LanRoom, create_room_code, validate_room_code


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
    globe_button = pg.Rect(c.SCREEN_W - 52, 8, 40, 40)
    create_button = pg.Rect(125, 218, 170, 44)
    code_box = pg.Rect(320, 218, 350, 44)
    join_button = pg.Rect(320, 278, 150, 44)
    leave_button = pg.Rect(490, 278, 150, 44)

    def open_room(code: str) -> None:
        nonlocal room, room_code, room_status
        if room is not None:
            room.close()
            room = None
        try:
            room_code = validate_room_code(code)
            room = LanRoom(room_code)
            room_status = "Room opened. Share the code with your friend."
        except (ValueError, OSError) as exc:
            room_status = str(exc) if isinstance(exc, ValueError) else f"Could not open room: {exc}"

    running = True

    while running:
        dt = clock.tick(c.FPS) / 1000.0
        dt = min(dt, 1.0 / 30.0)
        now_ms = pg.time.get_ticks()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if globe_button.collidepoint(event.pos):
                    room_panel_open = not room_panel_open
                    if room_panel_open:
                        room_code_input = ""
                        pg.key.start_text_input()
                    else:
                        pg.key.stop_text_input()
                elif room_panel_open and create_button.collidepoint(event.pos):
                    room_code_input = create_room_code()
                    open_room(room_code_input)
                elif room_panel_open and join_button.collidepoint(event.pos):
                    open_room(room_code_input)
                elif room_panel_open and leave_button.collidepoint(event.pos):
                    if room is not None:
                        room.close()
                        room = None
                    room_code = ""
                    room_status = "You left the room."
                elif room_panel_open and code_box.collidepoint(event.pos):
                    pg.key.start_text_input()
            elif event.type == pg.KEYDOWN:
                if room_panel_open:
                    if event.key == pg.K_ESCAPE:
                        room_panel_open = False
                        pg.key.stop_text_input()
                    elif event.key == pg.K_RETURN:
                        open_room(room_code_input)
                    elif event.key == pg.K_BACKSPACE:
                        room_code_input = room_code_input[:-1]
                elif event.key == pg.K_ESCAPE:
                    running = False
                elif event.key in (pg.K_UP, pg.K_SPACE, pg.K_w):
                    game.request_jump(now_ms)
                elif event.key == pg.K_r and not game.won:
                    game.reset_level(keep_message=False)
            elif event.type == pg.TEXTINPUT and room_panel_open:
                room_code_input = "".join(
                    char for char in room_code_input + event.text if char in "0123456789"
                )[:6]

        keys = pg.key.get_pressed()
        if not room_panel_open:
            game.handle_input(keys)
            game.update(dt, now_ms)
        if room is not None:
            try:
                room.update(game.x, game.y, game.level_index)
            except OSError as exc:
                room_status = f"Room connection failed: {exc}"
                room.close()
                room = None
        game.draw(screen, font, big)

        if room is not None:
            for player in room.players.values():
                if player.level == game.level_index:
                    player_rect = pg.Rect(
                        int(player.x), int(player.y), c.PLAYER_W, c.PLAYER_H
                    )
                    pg.draw.rect(screen, (255, 130, 210), player_rect, border_radius=4)
                    friend_label = font.render("Friend", True, (255, 200, 230))
                    screen.blit(friend_label, (player_rect.x - 4, player_rect.y - 22))

        pg.draw.rect(screen, (48, 60, 82), globe_button, border_radius=8)
        center = globe_button.center
        pg.draw.circle(screen, c.TEXT, center, 12, 2)
        pg.draw.ellipse(
            screen, c.TEXT, (center[0] - 6, center[1] - 12, 12, 24), 1
        )
        pg.draw.line(
            screen, c.TEXT, (center[0] - 11, center[1]), (center[0] + 11, center[1]), 1
        )

        if room is not None:
            screen.blit(
                font.render(f"ROOM {room_code}", True, c.TEXT),
                (c.SCREEN_W - 190, 54),
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
                font.render("Same Wi-Fi only: create a code or enter a friend's.", True, c.HUD),
                (125, 170),
            )

            pg.draw.rect(screen, (55, 120, 92), create_button, border_radius=6)
            create_label = font.render("Create code", True, c.TEXT)
            screen.blit(create_label, create_label.get_rect(center=create_button.center))
            pg.draw.rect(screen, (18, 24, 36), code_box, border_radius=6)
            pg.draw.rect(screen, c.PLAYER, code_box, 2, border_radius=6)
            shown_code = room_code_input or "Type 6-digit code"
            code_color = c.TEXT if room_code_input else c.HUD
            screen.blit(font.render(shown_code, True, code_color), (code_box.x + 12, code_box.y + 12))

            pg.draw.rect(screen, (54, 93, 143), join_button, border_radius=6)
            join_label = font.render("Join room", True, c.TEXT)
            screen.blit(join_label, join_label.get_rect(center=join_button.center))
            pg.draw.rect(screen, (100, 62, 72), leave_button, border_radius=6)
            leave_label = font.render("Leave room", True, c.TEXT)
            screen.blit(leave_label, leave_label.get_rect(center=leave_button.center))
            if room is not None:
                room_status = f"Room code: {room_code} | Players: {len(room.players) + 1}"
            status = room_status or "Enter the same code on both computers."
            screen.blit(font.render(status, True, c.WARNING), (125, 337))

        pg.display.flip()

    if room is not None:
        room.close()
    pg.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
