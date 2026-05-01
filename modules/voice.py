import asyncio
import os
import tempfile
import threading
import time
import uuid
import warnings

import edge_tts
import winsound
import win32com.client


class Voice:
    def __init__(self, voice_name):
        self.voice_name = voice_name
        self._lock = threading.Lock()
        self._last_tts = 0.0
        self._sapi_voice = None
        self._prefer_local = False

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
                if self._prefer_local:
                    self._speak_with_sapi(text)
                else:
                    asyncio.run(self._speak_async(text))
            except Exception as exc:
                self._prefer_local = True
                warnings.warn(
                    f"edge_tts no disponible ({exc}). Usando voz local de Windows.",
                    RuntimeWarning,
                )
                try:
                    self._speak_with_sapi(text)
                except Exception as local_exc:
                    warnings.warn(
                        f"No se pudo reproducir voz local ({local_exc}). Texto: {text}",
                        RuntimeWarning,
                    )

    async def _speak_async(self, text):
        tmp_dir = tempfile.gettempdir()
        filename = os.path.join(tmp_dir, f"leyla_{uuid.uuid4().hex}.mp3")
        try:
            communicate = edge_tts.Communicate(text, self.voice_name)
            await communicate.save(filename)
            winsound.PlaySound(filename, winsound.SND_FILENAME)
        finally:
            if os.path.exists(filename):
                os.remove(filename)

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
