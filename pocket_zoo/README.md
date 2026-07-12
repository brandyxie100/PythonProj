# Pocket Zoo — Underwater World

A browser merge game. Host it on your local WiFi so friends on the same network can play in their own browsers.

## Run locally (just you)

Open `index.html` in a browser, or:

```bash
python serve.py
```

Then visit `http://localhost:8080`.

## Host for others on the same WiFi

1. Make sure your computer and guests are on the **same WiFi** (not guest/isolated networks).
2. From this folder, start the server:

   ```bash
   cd pocket_zoo
   python serve.py
   ```

3. The script prints a URL like `http://192.168.1.42:8080`.
4. Share that URL. Guests open it in Safari or Chrome on their phone or laptop.

Each player gets their **own** game — coins and creatures are not shared. Refreshing the page starts a new session.

## Troubleshooting

| Problem | What to try |
|--------|-------------|
| Guests cannot connect | Confirm same WiFi; avoid guest networks that block device-to-device traffic. |
| Wrong IP shown | On macOS, check **System Settings → Network** for your WiFi IP. |
| Port in use | Stop other apps on port 8080, or change `PORT` in `serve.py`. |
| Firewall blocks access | Allow incoming connections for Python on your host machine. |

## Files

- `index.html` — game
- `deep_sea_game_bg.png` — background image
- `serve.py` — LAN static file server (Python 3, no extra packages)
