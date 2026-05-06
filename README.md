# Claude Usage Tray

A lightweight Linux system tray applet that shows your [Claude.ai](https://claude.ai) AI message usage (e.g. `12/100`) directly in the panel — no more checking the dashboard manually.

Built for **Linux Mint / Cinnamon** but should work on any GTK-based desktop with AppIndicator3 support (Ubuntu, Xfce, MATE, etc.).

---

## Features

- Shows current message usage as `used/limit` in the system tray
- Refreshes automatically every 60 seconds
- Right-click menu with:
  - Detailed usage for all limits (Messages, Claude Design, etc.)
  - Reset time display for each limit
  - Manual refresh
  - Open Claude.ai in browser
  - Set / update session key
  - Quit
- Session key saved locally in `~/.config/claude-tray/config.json`
- Survives desktop icon caching (Cinnamon-compatible)

---

## Requirements

- Linux Mint / Ubuntu or any GTK3 desktop
- Python 3.8+

Install dependencies:

```bash
sudo apt install python3-gi python3-requests gir1.2-appindicator3-0.1
pip3 install pillow --break-system-packages
```

---

## Installation

**1. Clone the repo**
```bash
git clone https://github.com/mibet01/claude-usage-tray.git
cd claude-usage-tray
```

**2. Copy the script**
```bash
mkdir -p ~/.local/bin
cp claude_tray.py ~/.local/bin/claude_tray.py
chmod +x ~/.local/bin/claude_tray.py
```

**3. Run it**
```bash
nohup python3 ~/.local/bin/claude_tray.py > ~/.config/claude-tray/tray.log 2>&1 &
```

**4. Set your session key**

Right-click the tray icon → **🔑 Set sessionKey…** → paste your key → OK.

### How to get your session key

1. Open your browser and go to [claude.ai](https://claude.ai) while logged in
2. Press `F12` to open DevTools
3. Go to **Application** tab → **Cookies** → click `https://claude.ai`
4. Find `sessionKey` and copy its value

> The key is stored only on your machine at `~/.config/claude-tray/config.json` and is only ever sent to `claude.ai`.

---

## Auto-start on Login

The repo includes a `claude-tray.desktop` file that tells Linux to launch the applet automatically when you log in.

**Install it with one command:**
```bash
mkdir -p ~/.config/autostart
cp claude-tray.desktop ~/.config/autostart/claude-tray.desktop
```

That's it. The applet will now start automatically on every login with a 5-second delay to let the desktop load first.

**To disable auto-start:**
```bash
rm ~/.config/autostart/claude-tray.desktop
```

**To check if it's enabled:**
```bash
ls ~/.config/autostart/
```

---

## Updating

```bash
cd claude-usage-tray
git pull
cp claude_tray.py ~/.local/bin/claude_tray.py
pkill -f claude_tray.py
nohup python3 ~/.local/bin/claude_tray.py > ~/.config/claude-tray/tray.log 2>&1 &
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Only shows `...` | Key not set — right-click → Set sessionKey… |
| Shows `expired` | Get a fresh sessionKey from browser DevTools |
| Shows `ERR` | Check `~/.config/claude-tray/tray.log` for details |
| Icon not visible | Make sure `gir1.2-appindicator3-0.1` is installed |
| Numbers not showing | Make sure `pillow` is installed: `pip3 install pillow --break-system-packages` |
| Doesn't start on login | Make sure `claude-tray.desktop` is in `~/.config/autostart/` |

---

## File locations

| File | Path |
|---|---|
| Script | `~/.local/bin/claude_tray.py` |
| Autostart | `~/.config/autostart/claude-tray.desktop` |
| Config / key | `~/.config/claude-tray/config.json` |
| Icon cache | `~/.config/claude-tray/icons/` |
| Log | `~/.config/claude-tray/tray.log` |

---

## License

MIT
