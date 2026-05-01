import json
import os


DEFAULT_CONFIG = {
    "wake_word": "leyla",
    "language": "es-ES",
    "voice": "es-ES-ElenaNeural",
    "listen_timeout": 6,
    "ambient_duration": 1,
    "confirm_dangerous": True,
    "apps": {
        "calculadora": "calc.exe",
        "explorador": "explorer.exe",
        "notepad": "notepad.exe",
        "powershell": "powershell.exe",
        "cmd": "cmd.exe",
    },
    "folders": {
        "descargas": "{USERPROFILE}\\Downloads",
        "documentos": "{USERPROFILE}\\Documents",
        "escritorio": "{USERPROFILE}\\Desktop",
    },
}


def load_config(config_path):
    if not os.path.exists(config_path):
        return DEFAULT_CONFIG
    with open(config_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    merged = DEFAULT_CONFIG.copy()
    merged.update(data)
    return merged


def resolve_path(path_template):
    return os.path.expandvars(path_template)
