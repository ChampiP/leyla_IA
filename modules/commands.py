import io
import os
import subprocess
import tempfile
import time
import unicodedata
import webbrowser
from urllib.parse import quote_plus

import pyautogui
import win32clipboard
from PIL import Image

from modules.ai_router import GeminiCommandRouter


def _strip_accents(text):
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


class CommandHandler:
    def __init__(self, config, voice):
        self.config = config
        self.voice = voice
        self._processes = {}
        self._ai_router = GeminiCommandRouter(config)
        self._pending_action = None

    def expects_followup(self):
        return self._pending_action is not None

    def pending_prompt(self):
        if not self._pending_action:
            return ""
        if self._pending_action["type"] == "screenshot_edit_choice":
            return "Quieres editar la captura? Responde si o no."
        if self._pending_action["type"] == "screenshot_finish":
            return "Edita la captura. Cuando termines, di listo."
        return ""

    def handle_followup(self, command):
        normalized = self._normalize_command(command)
        if not normalized or not self._pending_action:
            return False

        action_type = self._pending_action["type"]
        if action_type == "screenshot_edit_choice":
            if self._is_yes(normalized):
                self._pending_action = {"type": "screenshot_finish"}
                self.voice.speak("Edita la captura. Cuando termines, di listo.")
                return True
            if self._is_no(normalized):
                self._finalize_lightshot_capture()
                self._pending_action = None
                return True
            self.voice.speak("Responde si o no.")
            return True

        if action_type == "screenshot_finish":
            if normalized in {"listo", "ya", "termine", "terminado", "acabe"}:
                self._finalize_lightshot_capture()
                self._pending_action = None
                return True
            self.voice.speak("Cuando termines, di listo.")
            return True

        return False

    def handle(self, command):
        original_command = command.strip()
        command = self._normalize_command(original_command)
        if not command:
            return False

        if self._handle_known_command(command):
            return True

        ai_command = self._ai_router.resolve_command(
            original_command,
            self._command_catalog(),
        )
        if ai_command:
            normalized_ai_command = self._normalize_command(ai_command)
            if normalized_ai_command:
                self.voice.speak(f"Entendi: {ai_command}")
                if self._handle_known_command(normalized_ai_command):
                    return True

        self.voice.speak("No entendi el comando.")
        return False

    def _handle_known_command(self, command):
        if command in {
            "ayuda",
            "comandos",
            "que puedes hacer",
            "que puedes hacer sistema",
            "que puedes hacer leyla",
            "que puedes hacer leila",
        }:
            self.voice.speak("Puedo abrir apps, buscar, controlar ventanas, musica, capturas y whatsapp.")
            print(self.help_text(), flush=True)
            return True

        if command in {"abre el navegador", "abrir navegador"}:
            webbrowser.open_new_tab("https://www.google.com")
            self.voice.speak("Abriendo el navegador.")
            return True

        if command.startswith("buscar en google "):
            return self._search_in_browser(command.replace("buscar en google", "", 1), "google")

        if command.startswith("buscar en youtube "):
            return self._search_in_browser(command.replace("buscar en youtube", "", 1), "youtube")

        if command.startswith("buscar en spotify "):
            return self._search_in_browser(command.replace("buscar en spotify", "", 1), "spotify")

        if command.startswith("buscar "):
            return self._search_in_browser(command.replace("buscar", "", 1), "google")

        if command.startswith("reproducir en youtube "):
            return self._play_on_youtube(command.replace("reproducir en youtube", "", 1))

        if command.startswith("reproducir youtube "):
            return self._play_on_youtube(command.replace("reproducir youtube", "", 1))

        if command.startswith("pon en youtube "):
            return self._play_on_youtube(command.replace("pon en youtube", "", 1))

        if command.startswith("reproducir musica "):
            query = command.replace("reproducir musica", "", 1).strip()
            if query:
                return self._play_on_youtube(query)

        if command.startswith("pon musica "):
            query = command.replace("pon musica", "", 1).strip()
            if query:
                return self._play_on_youtube(query)

        if command in {"reproducir musica", "reanudar musica"}:
            pyautogui.press("playpause")
            self.voice.speak("Reproduciendo musica.")
            return True

        if command in {"pausar musica", "detener musica"}:
            pyautogui.press("playpause")
            self.voice.speak("Pausando musica.")
            return True

        if command in {"siguiente cancion", "siguiente pista"}:
            pyautogui.press("nexttrack")
            self.voice.speak("Siguiente cancion.")
            return True

        if command in {"cancion anterior", "pista anterior"}:
            pyautogui.press("prevtrack")
            self.voice.speak("Cancion anterior.")
            return True

        if command in {"subir volumen", "aumentar volumen"}:
            for _ in range(5):
                pyautogui.press("volumeup")
            self.voice.speak("Subiendo volumen.")
            return True

        if command in {"bajar volumen", "disminuir volumen"}:
            for _ in range(5):
                pyautogui.press("volumedown")
            self.voice.speak("Bajando volumen.")
            return True

        if command in {"silenciar", "mute"}:
            pyautogui.press("volumemute")
            self.voice.speak("Silenciando.")
            return True

        if command in {"nueva pestana", "abrir nueva pestana"}:
            pyautogui.hotkey("ctrl", "t")
            return True

        if command in {"cerrar pestana", "cerrar tab"}:
            pyautogui.hotkey("ctrl", "w")
            return True

        if command in {"recargar pagina", "actualizar pagina"}:
            pyautogui.press("f5")
            return True

        if command in {"atras", "volver atras"}:
            pyautogui.hotkey("alt", "left")
            return True

        if command in {"adelante", "ir adelante"}:
            pyautogui.hotkey("alt", "right")
            return True

        if command in {"cerrar ventana", "cerrar esta ventana"}:
            pyautogui.hotkey("alt", "f4")
            return True

        if command in {"copiar"}:
            pyautogui.hotkey("ctrl", "c")
            return True

        if command in {"pegar"}:
            pyautogui.hotkey("ctrl", "v")
            return True

        if command in {"cortar"}:
            pyautogui.hotkey("ctrl", "x")
            return True

        if command in {"guardar"}:
            pyautogui.hotkey("ctrl", "s")
            return True

        if command in {"seleccionar todo"}:
            pyautogui.hotkey("ctrl", "a")
            return True

        if command in {"presiona enter", "enter"}:
            pyautogui.press("enter")
            return True

        if command in {"cerrar navegador"}:
            self.voice.speak("No puedo cerrar el navegador de forma fiable.")
            return True

        if command.startswith("escribir "):
            text_to_write = command.replace("escribir", "", 1).strip()
            if not text_to_write:
                self.voice.speak("Dime el texto que quieres escribir.")
                return True
            time.sleep(0.4)
            pyautogui.write(text_to_write)
            self.voice.speak("Listo.")
            return True

        if command in {
            "captura de pantalla",
            "tomar captura",
            "sacar captura",
            "haz una captura",
        }:
            return self._capture_screen()

        if command in {"abrir whatsapp", "whatsapp"}:
            return self._open_whatsapp()

        if command in {
            "ver whatsapp",
            "revisar whatsapp",
            "quien me escribio en whatsapp",
            "quien escribio en whatsapp",
            "quien me escribio",
        }:
            return self._review_whatsapp()

        if command.startswith("abrir "):
            target = command.replace("abrir", "", 1).strip()
            if self._open_website(target):
                return True
            if self._open_app(target):
                return True
            if self._open_folder(target):
                return True
            self.voice.speak("No encontre esa aplicacion, web o carpeta.")
            return True

        if command.startswith("cerrar "):
            target = command.replace("cerrar", "", 1).strip()
            if self._close_app(target):
                return True
            self.voice.speak("No encontre un proceso controlado con ese nombre.")
            return True

        if "bloquear pantalla" in command:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=False)
            return True

        if "minimizar todo" in command or command in {"mostrar escritorio"}:
            pyautogui.hotkey("win", "d")
            return True

        if "cambiar ventana" in command or "siguiente ventana" in command:
            pyautogui.hotkey("alt", "tab")
            return True

        if command in {"fecha", "hora", "que hora es"}:
            now = time.strftime("%H:%M")
            self.voice.speak(f"Son las {now}.")
            return True

        if "apagar" in command:
            self._shutdown("/s")
            return True

        if "reiniciar" in command:
            self._shutdown("/r")
            return True

        if "cerrar sesion" in command:
            subprocess.run(["shutdown", "/l"], check=False)
            return True

        if "suspender" in command:
            subprocess.run(
                ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
                check=False,
            )
            return True

        return False

    def help_text(self):
        sections = [
            "[Leyla] Comandos disponibles:",
            "- abrir calculadora / spotify / chrome / explorador / notepad / powershell / cmd / whatsapp",
            "- abrir descargas / documentos / escritorio / imagenes / musica / videos",
            "- abrir youtube / gmail / whatsapp / google / spotify web",
            "- buscar gatos en google",
            "- buscar lofi en youtube",
            "- reproducir musica bad bunny",
            "- reproducir en youtube lofi hip hop",
            "- pausar musica / siguiente cancion / cancion anterior",
            "- subir volumen / bajar volumen / silenciar",
            "- captura de pantalla",
            "- revisar whatsapp / quien me escribio en whatsapp",
            "- escribir hola mundo",
            "- nueva pestana / cerrar pestana / recargar pagina / atras / adelante",
            "- copiar / pegar / cortar / guardar / seleccionar todo / presiona enter",
            "- cerrar ventana / minimizar todo / cambiar ventana / bloquear pantalla",
            "- hora / fecha / que hora es",
            "- ayuda",
        ]
        return "\n".join(sections)

    def _open_app(self, name):
        apps = self.config.get("apps", {})
        for key, value in apps.items():
            if key in name:
                if key == "spotify":
                    return self._open_spotify()
                if key == "whatsapp":
                    return self._open_whatsapp()
                self._processes[key] = subprocess.Popen([value])
                self.voice.speak(f"Abriendo {key}.")
                return True
        return False

    def _open_website(self, name):
        websites = self.config.get("websites", {})
        for key, value in websites.items():
            if key in name:
                webbrowser.open_new_tab(value)
                self.voice.speak(f"Abriendo {key}.")
                return True
        return False

    def _open_spotify(self):
        try:
            os.startfile("spotify:")
            self.voice.speak("Abriendo Spotify.")
            return True
        except OSError:
            try:
                self._processes["spotify"] = subprocess.Popen(["spotify"])
                self.voice.speak("Abriendo Spotify.")
                return True
            except OSError:
                webbrowser.open_new_tab("https://open.spotify.com")
                self.voice.speak("Abriendo Spotify web.")
                return True

    def _open_whatsapp(self):
        try:
            os.startfile("whatsapp:")
            self.voice.speak("Abriendo WhatsApp.")
            return True
        except OSError:
            webbrowser.open_new_tab("https://web.whatsapp.com")
            self.voice.speak("Abriendo WhatsApp web.")
            return True

    def _review_whatsapp(self):
        self._open_whatsapp()
        self.voice.speak("Estoy revisando WhatsApp.")
        time.sleep(5)

        temp_file = os.path.join(tempfile.gettempdir(), "leyla_whatsapp.png")
        pyautogui.screenshot().save(temp_file)
        summary = self._ai_router.analyze_whatsapp_screen(temp_file)
        try:
            os.remove(temp_file)
        except OSError:
            pass

        if summary:
            self.voice.speak(summary)
        else:
            self.voice.speak(
                "No pude identificar los mensajes. Asegurate de tener WhatsApp abierto y visible."
            )
        return True

    def _play_on_youtube(self, query):
        query = query.strip()
        if not query:
            self.voice.speak("Dime que quieres reproducir.")
            return True
        lucky_query = quote_plus(f"site:youtube.com/watch {query}")
        url = f"https://www.google.com/search?btnI=I&q={lucky_query}"
        webbrowser.open_new_tab(url)
        self.voice.speak(f"Reproduciendo {query} en YouTube.")
        return True

    def _search_in_browser(self, query, engine):
        query = query.strip()
        if not query:
            self.voice.speak("Dime que quieres buscar.")
            return True

        if engine == "youtube":
            url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        elif engine == "spotify":
            url = f"https://open.spotify.com/search/{quote_plus(query)}"
        else:
            url = f"https://www.google.com/search?q={quote_plus(query)}"

        webbrowser.open_new_tab(url)
        self.voice.speak(f"Buscando {query}.")
        return True

    def _capture_screen(self):
        if self._is_lightshot_available():
            pyautogui.hotkey("alt", "a")
            self._pending_action = {"type": "screenshot_edit_choice"}
            self.voice.speak("Quieres editar la captura? Responde si o no.")
            return True

        self._default_capture_to_clipboard()
        return True

    def _is_lightshot_available(self):
        configured_path = self.config.get("lightshot_path", "")
        common_paths = [
            configured_path,
            os.path.expandvars(r"%ProgramFiles%\Skillbrains\lightshot\Lightshot.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Skillbrains\lightshot\Lightshot.exe"),
            os.path.expandvars(r"%LocalAppData%\Skillbrains\lightshot\Lightshot.exe"),
        ]
        return any(path and os.path.exists(path) for path in common_paths)

    def _finalize_lightshot_capture(self):
        pyautogui.hotkey("ctrl", "c")
        time.sleep(0.2)
        pyautogui.press("esc")
        self.voice.speak("Captura copiada al portapapeles.")

    def _default_capture_to_clipboard(self):
        image = pyautogui.screenshot()
        self._copy_image_to_clipboard(image)
        self.voice.speak("Captura copiada al portapapeles.")

    def _copy_image_to_clipboard(self, image):
        output = io.BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()

        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        finally:
            win32clipboard.CloseClipboard()

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
            self.voice.speak("Seguro que quieres hacerlo. Di confirmar.")
            return
        subprocess.run(["shutdown", flag, "/t", "60"], check=False)

    def _normalize_command(self, text):
        normalized = _strip_accents(text.lower().strip())
        for wake_word in ("leila", "leyla", "sistema"):
            normalized = normalized.replace(wake_word, " ")
        filler_words = {
            "mmm",
            "eh",
            "em",
            "este",
            "pues",
            "oye",
            "porfa",
            "porfavor",
        }
        words = [word for word in normalized.split() if word not in filler_words]
        return " ".join(words).strip()

    def _is_yes(self, text):
        return text in {"si", "sí", "claro", "editar", "yes"}

    def _is_no(self, text):
        return text in {"no", "nop", "negativo"}

    def _command_catalog(self):
        commands = [
            "abre el navegador",
            "buscar en google perros husky",
            "buscar en youtube musica lofi",
            "buscar en spotify bad bunny",
            "reproducir musica despacito",
            "reproducir en youtube lofi hip hop",
            "pausar musica",
            "siguiente cancion",
            "cancion anterior",
            "subir volumen",
            "bajar volumen",
            "silenciar",
            "escribir hola mundo",
            "nueva pestana",
            "cerrar pestana",
            "recargar pagina",
            "atras",
            "adelante",
            "copiar",
            "pegar",
            "guardar",
            "cerrar ventana",
            "bloquear pantalla",
            "minimizar todo",
            "cambiar ventana",
            "captura de pantalla",
            "revisar whatsapp",
            "quien me escribio en whatsapp",
            "fecha",
            "hora",
            "que hora es",
            "apagar",
            "reiniciar",
            "cerrar sesion",
            "suspender",
            "ayuda",
        ]
        commands.extend(f"abrir {name}" for name in self.config.get("apps", {}))
        commands.extend(f"cerrar {name}" for name in self.config.get("apps", {}))
        commands.extend(f"abrir {name}" for name in self.config.get("folders", {}))
        commands.extend(f"abrir {name}" for name in self.config.get("websites", {}))
        return commands
