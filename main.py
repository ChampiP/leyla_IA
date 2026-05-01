import threading
import time

from modules.commands import CommandHandler
from modules.config import load_config
from modules.listener import WakeWordListener
from modules.tray import Tray
from modules.voice import Voice


def log_status(message):
    print(f"[Leyla] {message}", flush=True)


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
            log_status("Asistente activado.")
            voice.speak("Leyla activada.")
        else:
            log_status("Asistente desactivado.")
            voice.speak("Leyla desactivada.")

    def quit_app():
        running["value"] = False
        tray.stop()

    tray = Tray(toggle_active, quit_app)
    tray_thread = threading.Thread(target=tray.start, daemon=True)
    tray_thread.start()

    wake_word = config.get("wake_word", "leyla").lower()
    log_status(f"Lista. Di '{wake_word}' para activar.")
    voice.speak("Leyla lista.")

    while running["value"]:
        if not active["value"]:
            time.sleep(0.5)
            continue
        log_status("Escuchando palabra clave...")
        text = listener.listen_for_wake()
        if not text:
            continue
        log_status(f"Escuche: {text}")
        if wake_word in text:
            log_status("Palabra clave detectada. Esperando comando...")
            voice.beep_ready()
            voice.speak("Te escucho.")
            command_text = listener.listen_for_wake()
            if not command_text:
                log_status("No se detecto ningun comando.")
                continue
            log_status(f"Comando: {command_text}")
            handler.handle(command_text)


if __name__ == "__main__":
    main()
