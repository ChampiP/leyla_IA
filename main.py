import threading
import time
import unicodedata

from modules.commands import CommandHandler
from modules.config import load_config
from modules.listener import WakeWordListener
from modules.tray import Tray
from modules.voice import Voice


def log_status(message):
    print(f"[Leyla] {message}", flush=True)


def normalize_text(text):
    normalized = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def extract_wake_event(text, wake_words):
    words = normalize_text(text).split()
    for wake_word in wake_words:
        if wake_word in words:
            index = words.index(wake_word)
            inline_command = " ".join(words[index + 1 :]).strip()
            return True, wake_word, inline_command
    return False, "", ""


def main():
    config = load_config("config.json")
    assistant_name = config.get("assistant_name", "Leyla")
    voice = Voice(config.get("voice", "es-ES-ElenaNeural"))
    listener = WakeWordListener(config, voice)
    handler = CommandHandler(config, voice)

    running = {"value": True}
    active = {"value": True}

    def toggle_active():
        active["value"] = not active["value"]
        if active["value"]:
            log_status("Asistente activado.")
            voice.speak(f"{assistant_name} activada.")
        else:
            log_status("Asistente desactivado.")
            voice.speak(f"{assistant_name} desactivada.")

    def quit_app():
        running["value"] = False
        tray.stop()

    tray = Tray(toggle_active, quit_app)
    tray_thread = threading.Thread(target=tray.start, daemon=True)
    tray_thread.start()

    wake_words = [normalize_text(word) for word in config.get("wake_words", ["leila"])]
    wake_words_text = ", ".join(f"'{word}'" for word in wake_words)
    log_status(f"Lista. Di {wake_words_text} para activar.")
    voice.speak(f"{assistant_name} lista.")
    print(handler.help_text(), flush=True)

    while running["value"]:
        if not active["value"]:
            time.sleep(0.5)
            continue

        if handler.expects_followup():
            prompt = handler.pending_prompt()
            if prompt:
                log_status(prompt)
            followup_text = listener.listen_for_command()
            if not followup_text:
                continue
            log_status(f"Respuesta: {followup_text}")
            handler.handle_followup(followup_text)
            continue

        log_status("Escuchando palabra clave...")
        text = listener.listen_for_wake()
        if not text:
            continue
        log_status(f"Escuche: {text}")
        wake_detected, wake_word, inline_command = extract_wake_event(text, wake_words)
        if wake_detected:
            voice.beep_ready()
            if inline_command:
                log_status(
                    f"Palabra clave '{wake_word}' detectada con comando inline: {inline_command}"
                )
                command_text = inline_command
            else:
                log_status(f"Palabra clave '{wake_word}' detectada. Esperando comando...")
                voice.speak("Te escucho.")
                command_text = listener.listen_for_command()
                if not command_text:
                    log_status("No se detecto ningun comando. Reintentando una vez...")
                    voice.speak("Repitelo por favor.")
                    command_text = listener.listen_for_command()
                    if not command_text:
                        log_status("No se detecto ningun comando.")
                        voice.speak("No te escuche claramente.")
                        continue
            log_status(f"Comando: {command_text}")
            handler.handle(command_text)


if __name__ == "__main__":
    main()
