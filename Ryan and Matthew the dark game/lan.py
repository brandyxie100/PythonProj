"""Same-WiFi co-op rooms for Dungeon 67.

The host binds one UDP port derived from a 6-digit code. Joiners use an
ephemeral port and send to localhost plus the subnet broadcast, so two
windows on one PC and two PCs on one WiFi both reach the host.
"""

from __future__ import annotations

import json
import secrets
import socket
import time
from dataclasses import dataclass, field

BASE_PORT = 50123
SEND_INTERVAL = 0.1
PEER_TIMEOUT = 3.0
MAX_PLAYERS = 4  # host plus three joiners
_JOIN_LABELS = ("P2", "P3", "P4")


def create_room_code() -> str:
    """Create a shareable six-digit room code."""
    return f"{secrets.randbelow(1_000_000):06d}"


def validate_room_code(code: str) -> str:
    """Return a normalized code or raise ValueError for invalid input."""
    normalized = "".join(ch for ch in code.strip() if ch.isdigit())
    if len(normalized) != 6:
        raise ValueError("Enter a six-digit room code.")
    return normalized


def port_for_code(code: str) -> int:
    """Map a room code to a UDP port so rooms do not all share one port."""
    return BASE_PORT + (int(validate_room_code(code)) % 200)


@dataclass
class Peer:
    """A joiner the host has heard from."""

    player_id: str
    address: tuple[str, int]
    seen_at: float
    name: str
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0
    hp: int = 100
    slot: int = 0
    weapon_bonus: int = 0
    last_attack_seq: int = -1
    attack_pending: bool = False


@dataclass
class LanSession:
    """Host or joiner socket for one room code."""

    code: str
    host: bool
    player_id: str = field(default_factory=lambda: secrets.token_hex(8))
    peers: dict[str, Peer] = field(default_factory=dict)
    snapshot: dict | None = None
    rejected: bool = False
    lobby_count: int = 1
    _last_pose: float = 0.0
    _last_snap: float = 0.0
    _pose_seq: int = 0

    def __post_init__(self) -> None:
        """Open the UDP socket. Only the host binds the room port."""
        self.code = validate_room_code(self.code)
        self.port = port_for_code(self.code)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if self.host and hasattr(socket, "SO_REUSEPORT"):
                try:
                    self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except OSError:
                    pass
            # Host owns the room port. Joiners bind an ephemeral port so two
            # game windows on one machine do not split incoming packets.
            if self.host:
                self._socket.bind(("", self.port))
            else:
                self._socket.bind(("", 0))
            self._socket.setblocking(False)
        except OSError as exc:
            self._socket.close()
            raise OSError(
                f"Could not open room on port {self.port}. "
                f"Close other Dungeon 67 windows and try again. ({exc})"
            ) from exc

    def close(self) -> None:
        """Release the UDP socket."""
        try:
            self._socket.close()
        except OSError:
            pass

    def poll(self) -> None:
        """Read every pending datagram and drop silent peers."""
        now = time.monotonic()
        while True:
            try:
                packet, address = self._socket.recvfrom(8192)
            except BlockingIOError:
                break
            except OSError:
                break
            self._receive(packet, address, now)
        if self.host:
            self.peers = {
                player_id: peer
                for player_id, peer in self.peers.items()
                if now - peer.seen_at < PEER_TIMEOUT
            }

    def send_hello(self) -> None:
        """Joiner announces itself so the host can record its address."""
        if self.host:
            return
        self._send_discovery({"type": "hello", "room": self.code, "id": self.player_id})

    def send_pose(
        self,
        *,
        x: float,
        y: float,
        angle: float,
        hp: int,
        attack: bool,
        slot: int,
        weapon_bonus: int = 0,
        force: bool = False,
    ) -> None:
        """Joiner reports where they are. `attack` is a one-shot swing."""
        if self.host:
            return
        now = time.monotonic()
        if attack:
            self._pose_seq += 1
        elif not force and now - self._last_pose < SEND_INTERVAL:
            return
        self._last_pose = now
        self._send_discovery(
            {
                "type": "pose",
                "room": self.code,
                "id": self.player_id,
                "x": round(x, 3),
                "y": round(y, 3),
                "angle": round(angle, 4),
                "hp": int(hp),
                "attack": bool(attack),
                "seq": self._pose_seq,
                "slot": int(slot),
                "weapon": int(weapon_bonus),
            }
        )

    def snapshot_due(self) -> bool:
        """True when the host should publish a new world snapshot."""
        if not self.host:
            return False
        return time.monotonic() - self._last_snap >= SEND_INTERVAL

    def send_snapshot(self, payload: dict, *, force: bool = False) -> None:
        """Unicast the host world state to every joined peer."""
        if not self.host:
            return
        now = time.monotonic()
        if not force and now - self._last_snap < SEND_INTERVAL:
            return
        self._last_snap = now
        message = {
            "type": "snap",
            "room": self.code,
            "id": self.player_id,
            **payload,
        }
        raw = _encode(message)
        for peer in self.peers.values():
            try:
                self._socket.sendto(raw, peer.address)
            except OSError:
                continue

    def take_attacks(self) -> list[Peer]:
        """Return peers who swung since the last call, then clear the flags."""
        ready = [peer for peer in self.peers.values() if peer.attack_pending]
        for peer in ready:
            peer.attack_pending = False
        return ready

    def _send_discovery(self, message: dict) -> None:
        """Send to the host via localhost (same PC) and subnet broadcast."""
        raw = _encode(message)
        for target in ("127.0.0.1", "255.255.255.255"):
            try:
                self._socket.sendto(raw, (target, self.port))
            except OSError:
                continue

    def _receive(self, packet: bytes, address: tuple[str, int], now: float) -> None:
        try:
            message = json.loads(packet.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
            return
        if not isinstance(message, dict) or message.get("room") != self.code:
            return
        kind = message.get("type")
        player_id = message.get("id")
        if player_id == self.player_id:
            return
        if self.host and kind in ("hello", "pose"):
            self._host_peer(message, address, now)
            return
        if not self.host and kind == "snap":
            self.snapshot = message
            players = message.get("players")
            if isinstance(players, list):
                self.lobby_count = min(MAX_PLAYERS, len(players))
            return
        if not self.host and kind == "ack":
            count = message.get("count")
            if type(count) is int:
                self.lobby_count = count
            return
        if not self.host and kind == "full":
            self.rejected = True

    def _host_peer(self, message: dict, address: tuple[str, int], now: float) -> None:
        player_id = message.get("id")
        if not isinstance(player_id, str) or len(player_id) != 16:
            return
        peer = self.peers.get(player_id)
        if peer is None:
            # Cap is host + 3 joiners. A 5th player is told the room is full.
            if len(self.peers) >= MAX_PLAYERS - 1:
                self._send_to(address, {"type": "full", "room": self.code, "id": self.player_id})
                return
            used = {item.name for item in self.peers.values()}
            label = next(name for name in _JOIN_LABELS if name not in used)
            peer = Peer(player_id=player_id, address=address, seen_at=now, name=label)
            self.peers[player_id] = peer
        peer.address = address
        peer.seen_at = now
        if message.get("type") == "hello":
            self._send_to(
                address,
                {
                    "type": "ack",
                    "room": self.code,
                    "id": self.player_id,
                    "count": 1 + len(self.peers),
                },
            )
        if message.get("type") != "pose":
            return
        x, y, angle = message.get("x"), message.get("y"), message.get("angle")
        hp = message.get("hp")
        slot = message.get("slot", 0)
        weapon = message.get("weapon", 0)
        seq = message.get("seq", 0)
        if (
            type(x) not in (int, float)
            or type(y) not in (int, float)
            or type(angle) not in (int, float)
            or type(hp) not in (int, float)
        ):
            return
        peer.x = float(x)
        peer.y = float(y)
        peer.angle = float(angle)
        peer.hp = int(hp)
        peer.slot = int(slot) if type(slot) is int else 0
        peer.weapon_bonus = int(weapon) if type(weapon) is int else 0
        # Same swing can arrive twice (localhost + broadcast). Apply it once.
        if message.get("attack") and type(seq) is int and seq != peer.last_attack_seq:
            peer.last_attack_seq = seq
            peer.attack_pending = True

    def _send_to(self, address: tuple[str, int], message: dict) -> None:
        try:
            self._socket.sendto(_encode(message), address)
        except OSError:
            pass


def _encode(message: dict) -> bytes:
    return json.dumps(message, separators=(",", ":")).encode("utf-8")
