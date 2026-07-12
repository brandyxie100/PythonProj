#!/usr/bin/env python3
"""Serve Pocket Zoo over the local network so others on the same WiFi can play."""

from __future__ import annotations

import http.server
import os
import socket
import socketserver
import sys
from pathlib import Path

PORT = 8080
ROOT = Path(__file__).resolve().parent


def get_lan_ip() -> str:
    """Return this machine's LAN IPv4 address, or localhost if detection fails."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            # Does not send traffic; used only to learn the outbound interface IP.
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def main() -> None:
    """Start a static file server bound to all interfaces."""
    os.chdir(ROOT)
    handler = http.server.SimpleHTTPRequestHandler
    handler.extensions_map.update({".html": "text/html; charset=utf-8"})

    with socketserver.TCPServer(("0.0.0.0", PORT), handler) as httpd:
        httpd.allow_reuse_address = True
        lan_ip = get_lan_ip()
        print("Pocket Zoo — LAN host")
        print(f"Serving: {ROOT}")
        print()
        print("On this computer:")
        print(f"  http://localhost:{PORT}")
        print()
        print("Share with others on the same WiFi:")
        print(f"  http://{lan_ip}:{PORT}")
        print()
        print("Press Ctrl+C to stop.")
        print("-" * 40)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            sys.exit(0)


if __name__ == "__main__":
    main()
