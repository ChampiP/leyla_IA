import speech_recognition as sr


class WakeWordListener:
    def __init__(self, config, voice):
        self.config = config
        self.voice = voice
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.7
        self._ambient_adjusted = False

    def listen_for_wake(self):
        return self._listen(
            start_timeout=self.config.get("listen_start_timeout", 3),
            phrase_time_limit=self.config.get("listen_timeout", 6),
            adjust_noise=not self._ambient_adjusted,
        )

    def listen_for_command(self):
        return self._listen(
            start_timeout=self.config.get("command_start_timeout", 5),
            phrase_time_limit=self.config.get("command_timeout", 8),
            adjust_noise=False,
        )

    def _listen(self, start_timeout, phrase_time_limit, adjust_noise):
        try:
            microphone = sr.Microphone()
        except AttributeError as exc:
            raise RuntimeError(
                "No se encontro PyAudio. Instala la dependencia para usar el microfono."
            ) from exc

        with microphone as source:
            if adjust_noise:
                self.recognizer.adjust_for_ambient_noise(
                    source, duration=self.config.get("ambient_duration", 1)
                )
                self._ambient_adjusted = True
            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=start_timeout,
                    phrase_time_limit=phrase_time_limit,
                )
            except sr.WaitTimeoutError:
                return ""
        try:
            text = self.recognizer.recognize_google(
                audio, language=self.config.get("language", "es-ES")
            )
            return text.lower().strip()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            return ""
