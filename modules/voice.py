import threading
import time
import warnings

import pythoncom
import winsound
import win32com.client


class Voice:
    def __init__(self, voice_name):
        self.voice_name = voice_name
        self._lock = threading.Lock()
        self._last_tts = 0.0

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
        pythoncom.CoInitialize()
        try:
            sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
            self._set_sapi_voice(sapi_voice)
            sapi_voice.Speak(text)
        finally:
            pythoncom.CoUninitialize()

    def _set_sapi_voice(self, sapi_voice):
        if not self.voice_name:
            return

        target = self.voice_name.lower()
        for available_voice in sapi_voice.GetVoices():
            description = available_voice.GetDescription().lower()
            voice_id = available_voice.Id.lower()
            if target in description or target in voice_id:
                sapi_voice.Voice = available_voice
                return
