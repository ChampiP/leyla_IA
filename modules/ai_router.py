import os

from PIL import Image

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover
    genai = None
    types = None


class GeminiCommandRouter:
    def __init__(self, config):
        self.enabled = config.get("ai_enabled", True)
        self.api_key = config.get("gemini_api_key", "") or os.getenv("GEMINI_API_KEY", "")
        self.model = config.get("gemini_model", "gemini-2.5-flash")
        self._client = None

    def resolve_command(self, text, available_commands):
        if not self._ready():
            return None

        prompt = self._build_command_prompt(text, available_commands)
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    max_output_tokens=24,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
        except Exception:
            return None

        result = (response.text or "").strip()
        if not result:
            return None

        result = result.splitlines()[0].strip()
        if result == "NO_MATCH":
            return None
        return result

    def analyze_whatsapp_screen(self, image_path):
        if not self._ready():
            return None

        try:
            image = Image.open(image_path)
            response = self._client.models.generate_content(
                model=self.model,
                contents=[
                    image,
                    (
                        "Mira esta captura de pantalla. Si es una ventana de WhatsApp o "
                        "WhatsApp Web, dime en espanol y de forma breve quien escribio o "
                        "que chats parecen tener mensajes recientes o no leidos. Si no se "
                        "puede saber, responde exactamente NO_WHATSAPP_INFO."
                    ),
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                    max_output_tokens=80,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
        except Exception:
            return None

        result = (response.text or "").strip()
        if not result or result == "NO_WHATSAPP_INFO":
            return None
        return result

    def _ready(self):
        if not self.enabled or not self.api_key or genai is None or types is None:
            return False
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return True

    def _build_command_prompt(self, text, available_commands):
        command_list = "\n".join(f"- {command}" for command in available_commands)
        return (
            "Convierte la frase del usuario en un solo comando exacto de la lista.\n"
            "Responde solo con un comando exacto o NO_MATCH.\n"
            "No expliques nada.\n"
            "Lista de comandos:\n"
            f"{command_list}\n"
            f"Frase del usuario: {text}"
        )
