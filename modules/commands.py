import os
import subprocess
import time

import pyautogui
import webbrowser


class CommandHandler:
    def __init__(self, config, voice):
        self.config = config
        self.voice = voice
        self._processes = {}

    def handle(self, command):
        command = command.lower().strip()
        if not command:
            return

        if "abre el navegador" in command:
            webbrowser.open_new_tab("https://www.google.com")
            self.voice.speak("Abriendo el navegador.")
            return

        if "cerrar navegador" in command:
            self.voice.speak("No puedo cerrar el navegador de forma fiable.")
            return

        if command.startswith("escribir "):
            texto = command.replace("escribir", "", 1).strip()
            time.sleep(0.4)
            pyautogui.write(texto)
            self.voice.speak("Listo.")
            return

        if command.startswith("abrir "):
            target = command.replace("abrir", "", 1).strip()
            if self._open_app(target):
                return
            if self._open_folder(target):
                return
            self.voice.speak("No encontré esa aplicación o carpeta.")
            return

        if command.startswith("cerrar "):
            target = command.replace("cerrar", "", 1).strip()
            if self._close_app(target):
                return
            self.voice.speak("No encontré un proceso controlado con ese nombre.")
            return

        if "bloquear pantalla" in command:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=False)
            return

        if "minimizar todo" in command:
            pyautogui.hotkey("win", "d")
            return

        if "cambiar ventana" in command or "siguiente ventana" in command:
            pyautogui.hotkey("alt", "tab")
            return

        if "captura de pantalla" in command:
            self._screenshot()
            return

        if "fecha" in command or "hora" in command:
            now = time.strftime("%H:%M")
            self.voice.speak(f"Son las {now}.")
            return

        if "apagar" in command:
            self._shutdown("/s")
            return

        if "reiniciar" in command:
            self._shutdown("/r")
            return

        if "cerrar sesion" in command or "cerrar sesión" in command:
            subprocess.run(["shutdown", "/l"], check=False)
            return

        if "suspender" in command:
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=False)
            return

        self.voice.speak("No entendí el comando.")

    def _open_app(self, name):
        apps = self.config.get("apps", {})
        for key, value in apps.items():
            if key in name:
                self._processes[key] = subprocess.Popen([value])
                self.voice.speak(f"Abriendo {key}.")
                return True
        return False

    def _close_app(self, name):
        for key, proc in list(self._processes.items()):
            if key in name and proc.poll() is None:
                proc.terminate()
                self._processes.pop(key, None)
                self.voice.speak(f"Cerrando {key}.")
                return True
        return False

    def _open_folder(self, name):
        folders = self.config.get("folders", {})
        for key, value in folders.items():
            if key in name:
                path = os.path.expandvars(value)
                subprocess.Popen(["explorer.exe", path])
                self.voice.speak(f"Abriendo {key}.")
                return True
        return False

    def _shutdown(self, flag):
        if self.config.get("confirm_dangerous", True):
            self.voice.speak("¿Seguro que quieres hacerlo? Di confirmar.")
            return
        subprocess.run(["shutdown", flag, "/t", "60"], check=False)

    def _screenshot(self):
        os.makedirs("screenshots", exist_ok=True)
        filename = time.strftime("screenshots\\leyla_%Y%m%d_%H%M%S.png")
        image = pyautogui.screenshot()
        image.save(filename)
        self.voice.speak("Captura guardada.")
