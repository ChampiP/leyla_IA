import speech_recognition as sr


class WakeWordListener:
    def __init__(self, config, voice):
        self.config = config
        self.voice = voice
        self.recognizer = sr.Recognizer()

    def listen_for_wake(self):
        try:
            microphone = sr.Microphone()
        except AttributeError as exc:
            raise RuntimeError(
                "No se encontro PyAudio. Instala la dependencia para usar el microfono."
            ) from exc

        with microphone as source:
            self.recognizer.adjust_for_ambient_noise(
                source, duration=self.config.get("ambient_duration", 1)
            )
            audio = self.recognizer.listen(
                source, phrase_time_limit=self.config.get("listen_timeout", 6)
            )
        try:
            text = self.recognizer.recognize_google(
                audio, language=self.config.get("language", "es-ES")
            )
            return text.lower().strip()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            return ""
