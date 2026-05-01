import threading
import time

from modules.commands import CommandHandler
from modules.config import load_config
from modules.listener import WakeWordListener
from modules.tray import Tray
from modules.voice import Voice


def main():
    config = load_config("config.json")
    voice = Voice(config.get("voice", "es-ES-ElenaNeural"))
    listener = WakeWordListener(config, voice)
    handler = CommandHandler(config, voice)

    running = {"value": True}
    active = {"value": True}

    def toggle_active():
        active["value"] = not active["value"]
        if active["value"]:
            voice.speak("Leyla activada.")
        else:
            voice.speak("Leyla desactivada.")

    def quit_app():
        running["value"] = False
        tray.stop()

    tray = Tray(toggle_active, quit_app)
    tray_thread = threading.Thread(target=tray.start, daemon=True)
    tray_thread.start()

    wake_word = config.get("wake_word", "leyla").lower()
    voice.speak("Leyla lista.")

    while running["value"]:
        if not active["value"]:
            time.sleep(0.5)
            continue
        text = listener.listen_for_wake()
        if not text:
            continue
        if wake_word in text:
            voice.beep_ready()
            voice.speak("Te escucho.")
            command_text = listener.listen_for_wake()
            if not command_text:
                continue
            handler.handle(command_text)


if __name__ == "__main__":
    main()
