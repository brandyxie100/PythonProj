"""Room-code multiplayer for players on the same local network."""

from __future__ import annotations

import json
import secrets
import socket
import time
from dataclasses import dataclass

import config as c

PORT = 50123
SEND_INTERVAL = 0.1
PEER_TIMEOUT = 3.0


def create_room_code() -> str:
    """Create a shareable six-digit room code."""
    return f"{secrets.randbelow(1_000_000):06d}"


def validate_room_code(code: str) -> str:
    """Return a normalized code or raise ValueError for invalid input."""
    normalized = code.strip()
    if len(normalized) != 6 or not normalized.isascii() or not normalized.isdigit():
        raise ValueError("Enter a six-digit room code.")
    return normalized


@dataclass
class Player:
    x: float
    y: float
    level: int
    seen_at: float


class LanRoom:
    """Exchange player positions with clients using the same room code."""

    def __init__(self, code: str) -> None:
        self.code = validate_room_code(code)
        self.player_id = secrets.token_hex(8)
        self.players: dict[str, Player] = {}
        self._last_sent = 0.0
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if hasattr(socket, "SO_REUSEPORT"):
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            self._socket.bind(("", PORT))
            self._socket.setblocking(False)
        except OSError:
            self._socket.close()
            raise

    def update(self, x: float, y: float, level: int) -> None:
        """Broadcast own position, receive peers, and expire disconnected peers."""
        now = time.monotonic()
        if now - self._last_sent >= SEND_INTERVAL:
            message = json.dumps(
                {
                    "room": self.code,
                    "id": self.player_id,
                    "x": x,
                    "y": y,
                    "level": level,
                },
                separators=(",", ":"),
            ).encode("ascii")
            self._socket.sendto(message, ("255.255.255.255", PORT))
            self._last_sent = now

        while True:
            try:
                packet, _address = self._socket.recvfrom(512)
            except BlockingIOError:
                break
            self._receive(packet, now)

        self.players = {
            player_id: player
            for player_id, player in self.players.items()
            if now - player.seen_at < PEER_TIMEOUT
        }

    def _receive(self, packet: bytes, now: float) -> None:
        try:
            message = json.loads(packet.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
            return
        if not isinstance(message, dict) or message.get("room") != self.code:
            return
        player_id = message.get("id")
        x, y, level = message.get("x"), message.get("y"), message.get("level")
        if (
            not isinstance(player_id, str)
            or len(player_id) != 16
            or player_id == self.player_id
            or type(x) not in (int, float)
            or type(y) not in (int, float)
            or type(level) is not int
            or not 0 <= x <= c.SCREEN_W - c.PLAYER_W
            or not 0 <= y <= c.SCREEN_H
            or not 0 <= level < c.MAX_LEVEL
        ):
            return
        self.players[player_id] = Player(float(x), float(y), level, now)

    def close(self) -> None:
        self._socket.close()
