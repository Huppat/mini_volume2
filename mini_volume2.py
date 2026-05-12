#!/usr/bin/env python3
"""
Mini-Volume2 - Tray App für Cinnamon Desktop
- Mausrad in Taskleiste (unterste 50px) steuert Lautstärke
- wpctl prioritätär, ALSA als Fallback
- System Tray Icon mit pystray
"""

from pynput import mouse
import pystray
from pystray import Icon as TrayIcon, Menu, MenuItem
from PIL import Image
import io
import subprocess
import re
import os

# Konfiguration
VOLUME_STEP = 5  # Prozent
TASKBAR_HEIGHT = 50  # Pixel Höhe der Taskleiste


def create_icon_image():
    """Basis Icon erstellen (Lautstärke-Symbol)"""
    # Erstelle ein 32x32 PNG Bild
    image = Image.new('RGB', (32, 32), color=(50, 50, 50))
    # Einfaches Lautsprecher-Symbol zeichnen (Grauer Kreis mit Linie)
    draw = image.load()
    # Hintergrund
    for x in range(32):
        for y in range(32):
            # Kreis
            if (x - 16) ** 2 + (y - 16) ** 2 <= 14 ** 2:
                draw[x, y] = (100, 100, 100)
    # Lautsprecher-Symbol (einfache Darstellung)
    for y in range(8, 24):
        for x in range(18, 26):
            if (x - 22) ** 2 + (y - 16) ** 2 <= 5 ** 2:
                draw[x, y] = (200, 200, 200)
    return image


def get_current_volume():
    """Aktuelle Lautstärke ermitteln"""
    try:
        result = subprocess.run(
            ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            match = re.search(r'Volume:\s*([\d.]+)', result.stdout)
            if match:
                vol = float(match.group(1)) * 100
                return round(vol)
    except FileNotFoundError:
        pass
    return 100


def adjust_volume(delta):
    """Lautstärke anpassen"""
    current = get_current_volume()
    new_volume = max(0, min(100, current + delta))

    try:
        vol_decimal = new_volume / 100.0
        subprocess.run(
            ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{vol_decimal}"],
            check=True, timeout=3
        )
    except subprocess.CalledProcessError:
        try:
            subprocess.run(
                ["amixer", "sset", "Master", f"{new_volume}%"],
                check=True, timeout=3
            )
        except subprocess.CalledProcessError:
            pass
    except FileNotFoundError:
        pass


def on_scroll(x, y, dx, dy):
    """Mausrad-Event handler - nur wenn Maus in Taskleiste (unterste 50px)"""
    try:
        screen_height = os.environ.get('SCREEN_HEIGHT', 2160)
        try:
            screen_height = int(screen_height)
        except ValueError:
            screen_height = 2160

        taskbar_bottom = screen_height - TASKBAR_HEIGHT

        if y < taskbar_bottom:
            return True  # Maus nicht in Taskleiste

        # dy < 0 = Mausrad nach oben (Lauter), dy > 0 = Mausrad nach unten (Leiser)
        if dy > 0:
            adjust_volume(VOLUME_STEP)
        elif dy < 0:
            adjust_volume(-VOLUME_STEP)
        return True
    except Exception:
        return True


def on_draw_icon(icon, drawing_area):
    """Icon zeichnen (für GTK Integration)"""
    return True


def update_menu(icon):
    """Menü aktualisieren"""
    def do_nothing(icon):
        pass
    return Menu(
        MenuItem("Beenden", lambda icon: icon.stop()),
    )


def on_activate(icon):
    """Doppelklick auf Icon - Menü aktualisieren"""
    icon.menu = update_menu(icon)


def on_stop(icon):
    """App beenden"""
    pass


def main():
    # Icon erstellen
    image = create_icon_image()

    # Menü erstellen
    menu = update_menu(None)

    # Tray-Icon starten
    icon = TrayIcon(
        "mini-volume2",
        image,
        "Mini Volume",
        menu
    )

    # Maus-Listener im Hintergrund starten
    mouse.Listener(on_scroll=on_scroll).start()

    # Tray-Icon starten (blockiert)
    icon.run()


if __name__ == "__main__":
    main()
