import pyttsx3
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class PCVoiceTTS:
    def __init__(self, voice_speed_var=None):
        self.pc_engine = None
        self.voice_speed_var = voice_speed_var  # Variável tkinter para velocidade da voz
        self.voice = None
        self.is_speaking = False

    def _ensure_pc_engine(self):
        """Garante que o engine pyttsx3 está inicializado."""
        if self.pc_engine is None:
            self.pc_engine = pyttsx3.init()
        return self.pc_engine

    def set_voice(self, voice):
        """Define a voz a ser usada."""
        self.voice = voice
        engine = self._ensure_pc_engine()
        engine.setProperty('voice', voice)

    def _get_current_speed(self):
        """Obtém a velocidade atual da voz."""
        try:
            if self.voice_speed_var:
                return float(self.voice_speed_var.get())
            return 1.5  # Valor padrão se não houver variável
        except (ValueError, AttributeError):
            return 1.5

    def speak_response(self, response_text, on_speech_start=None):
        """Reproduz o texto usando a voz do PC."""
        try:
            self.is_speaking = True
            if on_speech_start:
                on_speech_start()
            
            engine = self._ensure_pc_engine()
            engine.setProperty('rate', int(175 * self._get_current_speed()))
            engine.say(response_text)
            engine.runAndWait()
            
        except Exception as e:
            log.error("Erro ao reproduzir texto com voz do PC: %s", e)
        finally:
            self.is_speaking = False

    def stop_speaking(self):
        """Para a reprodução atual."""
        if self.pc_engine:
            self.pc_engine.stop()
        while self.is_speaking:
            pass

    def enqueue_speak(self, response_text, on_speech_start=None):
        """Adiciona texto à fila de fala."""
        if self.is_speaking:
            self.stop_speaking()
        self.speak_response(response_text, on_speech_start)

    def cleanup(self):
        """Limpa os recursos do TTS."""
        try:
            if self.is_speaking:
                self.stop_speaking()
            
            if self.pc_engine:
                self.pc_engine.stop()
                
        except Exception as e:
            log.error("Erro durante a limpeza do TTS: %s", e)
