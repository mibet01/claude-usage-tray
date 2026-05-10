#!/usr/bin/env python3
"""
Claude Usage Tray Applet for Linux
Uses absolute icon paths to force Cinnamon/Gnome to reload the image.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3, GLib
import threading
import requests
import json
import os
import subprocess
from datetime import datetime

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("ERROR: Pillow not found. Run: pip3 install pillow --break-system-packages")

# Configuration
REFRESH_INTERVAL = 60 # 1 minute
API_BASE_URL = "https://claude.ai/api"
ICON_DIR = os.path.expanduser("~/.config/claude-tray/icons/")
CONFIG_DIR = os.path.expanduser("~/.config/claude-tray/")
os.makedirs(ICON_DIR, exist_ok=True)

_icon_counter = 0

def make_icon(text, color="#ffffff"):
    """Create a PNG with text and return its absolute path."""
    global _icon_counter
    _icon_counter += 1
    # Rotate through 20 filenames to bust the cache
    path = os.path.join(ICON_DIR, f"claude_{_icon_counter % 20}.png")

    W, H = 88, 24
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background pill
    draw.rounded_rectangle([0, 0, W-1, H-1], radius=4, fill=(30, 30, 30, 210))

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 13)
        except Exception:
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (W - tw) // 2
    y = (H - th) // 2 - 1

    # Shadow
    draw.text((x+1, y+1), text, font=font, fill=(0, 0, 0, 200))
    # Text
    draw.text((x, y), text, font=font, fill=color)

    img.save(path, "PNG")
    return path


class ClaudeTray:
    def __init__(self):
        if not HAS_PIL:
            raise RuntimeError("Pillow is required. Run: pip3 install pillow --break-system-packages")

        self.session_key = ""
        self.org_uuid = ""
        self.config_path = os.path.join(CONFIG_DIR, "config.json")
        
        # Start with a placeholder icon
        init_icon = make_icon("...", "#aaaaaa")

        self.indicator = AppIndicator3.Indicator.new_with_path(
            "claude-usage",
            os.path.splitext(os.path.basename(init_icon))[0],
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
            ICON_DIR
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        # Build menu
        self.menu = Gtk.Menu()

        self.dynamic_items = []
        
        init_item = Gtk.MenuItem(label="Fetching usage…")
        init_item.set_sensitive(False)
        self.menu.append(init_item)
        self.dynamic_items.append(init_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        refresh_item = Gtk.MenuItem(label="🔄  Refresh now")
        refresh_item.connect("activate", self.on_refresh)
        self.menu.append(refresh_item)

        open_item = Gtk.MenuItem(label="🌐  Open Claude.ai")
        open_item.connect("activate", self.on_open_claude)
        self.menu.append(open_item)

        set_token_item = Gtk.MenuItem(label="🔑  Set sessionKey…")
        set_token_item.connect("activate", self.on_set_token)
        self.menu.append(set_token_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label="✕  Quit")
        quit_item.connect("activate", self.on_quit)
        self.menu.append(quit_item)

        self.menu.show_all()
        self.indicator.set_menu(self.menu)

        self.load_config()
        self.fetch_data()
        GLib.timeout_add_seconds(REFRESH_INTERVAL, self.schedule_fetch)

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path) as f:
                    data = json.load(f)
                    self.session_key = data.get("session_key", "")
                    self.org_uuid = data.get("org_uuid", "")
            except Exception:
                pass

    def save_config(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump({
                "session_key": self.session_key,
                "org_uuid": self.org_uuid
            }, f)

    def schedule_fetch(self):
        self.fetch_data()
        return True

    def fetch_data(self):
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self):
        if not self.session_key:
            GLib.idle_add(self._update_ui, None, "no token")
            return

        try:
            headers = {
                "Cookie": f"sessionKey={self.session_key}",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            # 1. Fetch Organization UUID if not present
            if not self.org_uuid:
                resp = requests.get(f"{API_BASE_URL}/organizations", headers=headers, timeout=10)
                resp.raise_for_status()
                orgs = resp.json()
                if orgs:
                    self.org_uuid = orgs[0]["uuid"]
                    self.save_config()
                else:
                    GLib.idle_add(self._update_ui, None, "no org")
                    return

            # 2. Fetch Usage Stats
            resp = requests.get(
                f"{API_BASE_URL}/organizations/{self.org_uuid}/usage_limit_stats",
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 401:
                GLib.idle_add(self._update_ui, None, "expired")
                return
                
            resp.raise_for_status()
            data = resp.json()
            
            GLib.idle_add(self._update_ui, data, None)

        except Exception as e:
            print(f"Fetch error: {e}")
            GLib.idle_add(self._update_ui, None, str(e))

    def _update_ui(self, data, error):
        # clean dynamic items
        for item in self.dynamic_items:
            self.menu.remove(item)
        self.dynamic_items.clear()

        if error:
            icon_path = make_icon(error[:9], color="#ff6b6b")
            item = Gtk.MenuItem(label=f"Error: {error}")
            item.set_sensitive(False)
            self.menu.insert(item, 0)
            self.dynamic_items.append(item)
        elif data:
            main_usage = None
            items_to_add = []
            
            if isinstance(data, list):
                # add all limits to menu
                for item in data:
                    l_type = item.get("limit_type", "unknown")
                    if l_type == "messages" and not main_usage:
                        main_usage = item
                        
                    u = item.get("usage", 0)
                    l = item.get("limit", 0)
                    r = item.get("reset_at")
                    
                    if l > 0:
                        pct = int(u / l * 100)
                    else:
                        pct = 0
                        
                    label = f"✨ {l_type.capitalize()}: {u}/{l} used ({pct}%)"
                    if r:
                        try:
                            dt = datetime.fromisoformat(r.replace("Z", "+00:00"))
                            label += f" ↻ {dt.strftime('%H:%M')}"
                        except:
                            pass
                    
                    m_item = Gtk.MenuItem(label=label)
                    m_item.set_sensitive(False)
                    items_to_add.append(m_item)
                    
                if not main_usage and data:
                    main_usage = data[0]
            elif isinstance(data, dict):
                main_usage = data
                u = data.get("usage", 0)
                l = data.get("limit", 0)
                m_item = Gtk.MenuItem(label=f"✨ Usage: {u}/{l}")
                m_item.set_sensitive(False)
                items_to_add.append(m_item)

            if main_usage:
                used = main_usage.get("usage", 0)
                limit = main_usage.get("limit", 0)
                
                text = f"{used}/{limit}"
                pct = int(used / limit * 100) if limit else 0
                
                color = "#d97757" # Terracotta by default
                if pct > 80: color = "#ffeb3b" # Yellow
                if pct > 95: color = "#ff6b6b" # Red
                
                icon_path = make_icon(text, color=color)
            else:
                icon_path = make_icon("???", color="#aaaaaa")
                m_item = Gtk.MenuItem(label="No usage data found")
                m_item.set_sensitive(False)
                items_to_add.append(m_item)
                
            # insert items
            for i, item in enumerate(items_to_add):
                self.menu.insert(item, i)
                self.dynamic_items.append(item)
                
            self.menu.show_all()
        else:
            icon_path = make_icon("???", color="#aaaaaa")
            item = Gtk.MenuItem(label="No usage data found")
            item.set_sensitive(False)
            self.menu.insert(item, 0)
            self.dynamic_items.append(item)
            self.menu.show_all()

        # Update icon
        icon_name = os.path.splitext(os.path.basename(icon_path))[0]
        self.indicator.set_icon_full(icon_name, "Claude usage")

    def on_refresh(self, _):
        self.fetch_data()

    def on_open_claude(self, _):
        subprocess.Popen(["xdg-open", "https://claude.ai"])

    def on_set_token(self, _):
        dialog = Gtk.Dialog(title="Set Claude sessionKey", flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OK,     Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        box.set_spacing(8)
        box.set_margin_start(12); box.set_margin_end(12)
        box.set_margin_top(12);   box.set_margin_bottom(12)
        box.add(Gtk.Label(label=(
            "Paste your Claude 'sessionKey' cookie.\n"
            "DevTools → Application → Cookies → claude.ai"
        )))
        entry = Gtk.Entry()
        entry.set_width_chars(60)
        entry.set_visibility(False)
        entry.set_text(self.session_key)
        box.add(entry)
        dialog.show_all()

        if dialog.run() == Gtk.ResponseType.OK:
            self.session_key = entry.get_text().strip()
            self.org_uuid = "" # Reset org uuid to re-fetch it
            self.save_config()
            self.fetch_data()
        dialog.destroy()

    def on_quit(self, _):
        Gtk.main_quit()


def main():
    app = ClaudeTray()
    Gtk.main()

if __name__ == "__main__":
    main()
