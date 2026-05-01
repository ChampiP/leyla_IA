import threading
import time
import warnings

import pythoncom
import winsound
import win32com.client

try:
    import pyttsx3
except ImportError:  # pragma: no cover
    pyttsx3 = None


class Voice:
    def __init__(self, voice_name):
        self.voice_name = voice_name
        self._lock = threading.Lock()
        self._last_tts = 0.0
        self._warned = False

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

            if self._speak_with_pyttsx3(text):
                return
            if self._speak_with_sapi(text):
                return

            if not self._warned:
                warnings.warn(
                    f"No se pudo reproducir voz local. Texto: {text}",
                    RuntimeWarning,
                )
                self._warned = True

    def _speak_with_pyttsx3(self, text):
        if pyttsx3 is None:
            return False
        try:
            engine = pyttsx3.init()
            self._configure_pyttsx3(engine)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            return True
        except Exception:
            return False

    def _configure_pyttsx3(self, engine):
        if not self.voice_name:
            return
        target = self.voice_name.lower()
        try:
            for available_voice in engine.getProperty("voices"):
                voice_id = getattr(available_voice, "id", "").lower()
                voice_name = getattr(available_voice, "name", "").lower()
                if target in voice_id or target in voice_name:
                    engine.setProperty("voice", available_voice.id)
                    return
        except Exception:
            return

    def _speak_with_sapi(self, text):
        pythoncom.CoInitialize()
        sapi_voice = None
        try:
            sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
            self._set_sapi_voice(sapi_voice)
            sapi_voice.Speak(text)
            return True
        except Exception:
            return False
        finally:
            sapi_voice = None
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
