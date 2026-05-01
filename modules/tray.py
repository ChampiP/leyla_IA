import threading
import time

import pystray
from PIL import Image, ImageDraw


class Tray:
    def __init__(self, on_toggle, on_quit):
        self.on_toggle = on_toggle
        self.on_quit = on_quit
        self._running = False
        self._icons = self._create_frames()
        self._icon = pystray.Icon("Leyla", self._icons[0], "Leyla")
        self._icon.menu = pystray.Menu(
            pystray.MenuItem("Activar/Desactivar", self._toggle),
            pystray.MenuItem("Salir", self._quit),
        )
        self._animation_thread = threading.Thread(target=self._animate, daemon=True)

    def start(self):
        self._running = True
        self._animation_thread.start()
        self._icon.run()

    def stop(self):
        self._running = False
        self._icon.stop()

    def _toggle(self, icon, item):
        self.on_toggle()

    def _quit(self, icon, item):
        self.on_quit()

    def _animate(self):
        index = 0
        while self._running:
            index = (index + 1) % len(self._icons)
            self._icon.icon = self._icons[index]
            time.sleep(0.4)

    def _create_frames(self):
        frames = []
        colors = ["#3a86ff", "#33c3a5", "#f4a261"]
        for color in colors:
            image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.ellipse((4, 4, 28, 28), fill=color)
            draw.ellipse((10, 10, 22, 22), outline=(255, 255, 255, 200), width=2)
            frames.append(image)
        return frames
