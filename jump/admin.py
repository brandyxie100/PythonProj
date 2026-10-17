"""Password-gated session admin menu."""

from __future__ import annotations

import hashlib
import hmac

import pygame

import config as c

# SHA-256 digest only; the password is not stored in plaintext.
_ADMIN_PASSWORD_SHA256 = "b2e45f5c14bc8f74c1478a3a4b8c3a58d46907d49342b09a1e73e971012b44d3"


class AdminMenu:
    """Masked password prompt followed by temporary game unlock actions."""

    def __init__(self) -> None:
        self.password = ""
        self.authenticated = False
        self.request_menu = False
        self.action: str | None = None
        self.message = "Enter admin password, then press Enter"
        self._title = pygame.font.SysFont("Arial", 46, bold=True)
        self._body = pygame.font.SysFont("Arial", 22, bold=True)
        self._small = pygame.font.SysFont("Arial", 17)
        self.action_rects = {
            "vault": pygame.Rect(c.SCREEN_W // 2 - 180, 190, 360, 52),
            "path": pygame.Rect(c.SCREEN_W // 2 - 180, 260, 360, 52),
            "boss": pygame.Rect(c.SCREEN_W // 2 - 180, 330, 360, 52),
            "back": pygame.Rect(c.SCREEN_W // 2 - 180, 410, 360, 48),
        }

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.request_menu = True
                return
            if not self.authenticated:
                if event.key == pygame.K_BACKSPACE:
                    self.password = self.password[:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._authenticate()
                return

        if event.type == pygame.TEXTINPUT and not self.authenticated:
            allowed = "0123456789#"
            self.password = (self.password + "".join(ch for ch in event.text if ch in allowed))[:64]
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.authenticated:
            for action, rect in self.action_rects.items():
                if rect.collidepoint(event.pos):
                    if action == "back":
                        self.request_menu = True
                    else:
                        self.action = action
                    return

    def _authenticate(self) -> None:
        digest = hashlib.sha256(self.password.encode("utf-8")).hexdigest()
        self.authenticated = hmac.compare_digest(digest, _ADMIN_PASSWORD_SHA256)
        self.password = ""
        self.message = "Admin access granted" if self.authenticated else "Incorrect password"

    def update(self, dt: float) -> None:
        pass

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill((9, 13, 30))
        title = self._title.render("ADMIN MENU", True, c.GROUND_LINE)
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 76)))

        if not self.authenticated:
            prompt = self._body.render("PASSWORD", True, c.UI)
            surf.blit(prompt, prompt.get_rect(center=(c.SCREEN_W // 2, 190)))
            input_rect = pygame.Rect(c.SCREEN_W // 2 - 190, 222, 380, 56)
            pygame.draw.rect(surf, (22, 30, 54), input_rect, border_radius=8)
            pygame.draw.rect(surf, c.UI_DIM, input_rect, width=2, border_radius=8)
            masked = "•" * len(self.password)
            value = self._body.render(masked or "Type password", True, c.UI)
            surf.blit(value, value.get_rect(center=input_rect.center))
        else:
            labels = {
                "vault": "UNLOCK VAULT + KEY",
                "path": "UNLOCK ALL 10 PATH LEVELS",
                "boss": "UNLOCK BOSS LEVEL",
                "back": "BACK TO MENU",
            }
            for action, rect in self.action_rects.items():
                color = c.MENU_BTN_HOVER if action != "back" else c.MENU_BTN
                pygame.draw.rect(surf, color, rect, border_radius=8)
                pygame.draw.rect(surf, c.UI, rect, width=2, border_radius=8)
                label = self._body.render(labels[action], True, c.UI)
                surf.blit(label, label.get_rect(center=rect.center))

        message = self._small.render(self.message, True, c.UI_DIM)
        surf.blit(message, message.get_rect(center=(c.SCREEN_W // 2, 482)))
        hint = self._small.render("Esc to return", True, c.UI_DIM)
        surf.blit(hint, hint.get_rect(center=(c.SCREEN_W // 2, 516)))
