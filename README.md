# Claude Usage Tray

A system tray applet for Linux (Gnome, Cinnamon, etc.) that displays your remaining Claude.ai messages. Similar to the [Cursor Usage Tray](https://github.com/miha/cursor-usage-tray).

![Claude Usage Tray](https://github.com/miha/claude-usage-tray/raw/main/screenshot.png) *(Placeholder)*

## Features

- Displays remaining messages in the tray icon.
- Shows total limit and percentage used in the menu.
- Displays reset time for your current window.
- Easy session key configuration.
- Auto-refresh every 2 minutes.

## Requirements

- Python 3
- `python3-gi`, `gir1.2-appindicator3-0.1` (usually pre-installed on Mint/Ubuntu)
- `requests`
- `pillow` (for dynamic icon generation)

Install dependencies:

```bash
pip3 install requests pillow --break-system-packages
```

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/miha/claude-usage-tray.git
   cd claude-usage-tray
   ```

2. Make the script executable:
   ```bash
   chmod +x claude_tray.py
   ```

3. (Optional) Install the `.desktop` file to your applications menu:
   ```bash
   cp claude-tray.desktop ~/.local/share/applications/
   ```

## Configuration

1. Open Claude.ai in your browser and log in.
2. Open DevTools (F12) -> **Application** -> **Cookies** -> `https://claude.ai`.
3. Copy the value of the `sessionKey` cookie.
4. Click on the Claude Tray icon -> **Set sessionKey...** and paste your key.

## Credits

Inspired by the [Cursor Usage Tray](https://github.com/miha/cursor-usage-tray).
API exploration inspired by various community tools like `claude-usage-bar`.
