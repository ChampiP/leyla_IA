import threading
import time
import warnings

import winsound
import win32com.client


class Voice:
    def __init__(self, voice_name):
        self.voice_name = voice_name
        self._lock = threading.Lock()
        self._last_tts = 0.0
        self._sapi_voice = None

    def beep_ready(self):
        winsound.MessageBeep(winsound.MB_OK)

    def speak(self, text):
        if not text:
            return
        with self._lock:
            now = time.time()
            if now - self._last_tts < 0.1:
                time.sleep(0.1)
            self._last_tts = time.time()
            try:
                self._speak_with_sapi(text)
            except Exception as exc:
                warnings.warn(
                    f"No se pudo reproducir voz local ({exc}). Texto: {text}",
                    RuntimeWarning,
                )

    def _speak_with_sapi(self, text):
        if self._sapi_voice is None:
            self._sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
            self._set_sapi_voice()
        self._sapi_voice.Speak(text)

    def _set_sapi_voice(self):
        if not self.voice_name:
            return

        target = self.voice_name.lower()
        for sapi_voice in self._sapi_voice.GetVoices():
            description = sapi_voice.GetDescription().lower()
            voice_id = sapi_voice.Id.lower()
            if target in description or target in voice_id:
                self._sapi_voice.Voice = sapi_voice
                return
