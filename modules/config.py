import json
import os

from dotenv import load_dotenv


DEFAULT_CONFIG = {
    "assistant_name": "Leyla",
    "wake_words": ["leyla", "leila", "sistema"],
    "language": "es-ES",
    "voice": "es-ES-ElenaNeural",
    "ai_enabled": True,
    "gemini_model": "gemini-2.5-flash",
    "listen_start_timeout": 3,
    "listen_timeout": 6,
    "command_start_timeout": 5,
    "command_timeout": 8,
    "ambient_duration": 1,
    "confirm_dangerous": True,
    "apps": {
        "calculadora": "calc.exe",
        "explorador": "explorer.exe",
        "notepad": "notepad.exe",
        "powershell": "powershell.exe",
        "cmd": "cmd.exe",
        "spotify": "spotify",
        "chrome": "chrome.exe",
        "whatsapp": "whatsapp",
    },
    "folders": {
        "descargas": "{USERPROFILE}\\Downloads",
        "documentos": "{USERPROFILE}\\Documents",
        "escritorio": "{USERPROFILE}\\Desktop",
        "imagenes": "{USERPROFILE}\\Pictures",
        "musica": "{USERPROFILE}\\Music",
        "videos": "{USERPROFILE}\\Videos",
    },
    "websites": {
        "youtube": "https://www.youtube.com",
        "gmail": "https://mail.google.com",
        "whatsapp": "https://web.whatsapp.com",
        "google": "https://www.google.com",
        "spotify web": "https://open.spotify.com",
    },
}


def load_config(config_path):
    load_dotenv()

    data = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)

    merged = DEFAULT_CONFIG.copy()
    merged.update(data)

    if "wake_word" in merged and "wake_words" not in data:
        merged["wake_words"] = [merged["wake_word"]]

    merged["wake_words"] = [word.lower().strip() for word in merged.get("wake_words", []) if word]

    for nested_key in ("apps", "folders", "websites"):
        nested = DEFAULT_CONFIG.get(nested_key, {}).copy()
        nested.update(data.get(nested_key, {}))
        merged[nested_key] = nested

    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_api_key:
        merged["gemini_api_key"] = gemini_api_key

    return merged


def resolve_path(path_template):
    return os.path.expandvars(path_template)
