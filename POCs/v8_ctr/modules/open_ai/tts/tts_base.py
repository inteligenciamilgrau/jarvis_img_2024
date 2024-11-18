import queue
import threading
from concurrent.futures import ThreadPoolExecutor
import time
from openai import OpenAI
from .audio_processor import AudioChunkProcessor, AudioStreamManager
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Singleton do AudioStreamManager para garantir uma única instância
_audio_stream_instance = None

def get_audio_stream_manager():
    global _audio_stream_instance
    if _audio_stream_instance is None:
        _audio_stream_instance = AudioStreamManager()
        log.info("Nova instância do AudioStreamManager criada")
    return _audio_stream_instance

class BaseTTS:
    """Classe base para funcionalidade TTS compartilhada"""
    def __init__(self, voice_speed_var=None, accent_var=None, emotion_var=None, intonation_var=None):
        self.client_openai = OpenAI()
        self.audio_stream = get_audio_stream_manager()  # Usa o singleton
        self.queue = queue.Queue()
        self.audio_buffer = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        self.is_speaking = False
        self.stop_current = False
        self.speech_started_callback = None
        self.first_chunk_played = False
        
        self.voice = "onyx"
        self.model = "tts-1"
        self.voice_speed_var = voice_speed_var
        self.accent_var = accent_var
        self.emotion_var = emotion_var
        self.intonation_var = intonation_var
        
        self._shutdown = False
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        
        # Métricas de tempo
        self.recording_start_time = None
        self.api_start_time = None
        self.processing_start_time = None
        self.first_chunk_time = None
        self.total_chunks_processed = 0
        self.sentence_metrics = []

    def start_recording_timer(self):
        """Inicia o timer de gravação"""
        self.recording_start_time = time.time()
        log.info("=== Início da gravação ===")

    def stop_recording_timer(self):
        """Para o timer de gravação e retorna o tempo decorrido"""
        if self.recording_start_time:
            recording_time = time.time() - self.recording_start_time
            log.info("Tempo de gravação: %.2f segundos", recording_time)
            return recording_time
        return 0

    def set_voice(self, voice):
        """Define a voz a ser usada."""
        self.voice = voice

    def set_model(self, model):
        """Define o modelo a ser usado."""
        self.model = model

    def _get_current_speed(self):
        """Obtém a velocidade atual da voz."""
        try:
            if self.voice_speed_var:
                return float(self.voice_speed_var.get())
            return 1.5
        except (ValueError, AttributeError):
            return 1.5

    def _get_current_accent(self):
        """Obtém o sotaque atual."""
        try:
            if self.accent_var:
                return self.accent_var.get()
            return "Default (Sem sotaque)"
        except AttributeError:
            return "Default (Sem sotaque)"

    def _get_current_emotion(self):
        """Obtém a emoção atual."""
        try:
            if self.emotion_var:
                return self.emotion_var.get()
            return "Bem calmo"
        except AttributeError:
            return "Bem calmo"

    def _get_current_intonation(self):
        """Obtém a entonação atual."""
        try:
            if self.intonation_var:
                return self.intonation_var.get()
            return "Default (Sem entonação)"
        except AttributeError:
            return "Default (Sem entonação)"

    def stop_speaking(self):
        """Para a reprodução atual."""
        self.stop_current = True
        while self.is_speaking:
            pass

    def enqueue_speak(self, response_text, on_speech_start=None):
        """Adiciona texto à fila de fala."""
        if self._shutdown:
            return
            
        if self.is_speaking:
            self.stop_speaking()
        self.queue.put((response_text, on_speech_start))

    def _process_queue(self):
        """Processa a fila de textos para fala."""
        while not self._shutdown:
            try:
                try:
                    item = self.queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                if item is None:
                    self.queue.task_done()
                    break

                try:
                    response_text, on_speech_start = item
                    self.speak_response(response_text, on_speech_start)
                finally:
                    self.queue.task_done()
                
            except Exception as e:
                log.error("Erro no processamento da fila de fala: %s", e)

    def cleanup(self):
        """Limpa os recursos do TTS."""
        try:
            self._shutdown = True
            
            if self.is_speaking:
                self.stop_speaking()
            
            self.queue.put(None)
            if self.worker_thread.is_alive():
                self.worker_thread.join(timeout=1)
            
            self.executor.shutdown(wait=True, cancel_futures=True)
                
        except Exception as e:
            log.error("Erro durante a limpeza do TTS: %s", e)

    def speak_response(self, response_text, on_speech_start=None):
        """
        Método abstrato para ser implementado pelas classes filhas.
        Processa e reproduz o texto como áudio.
        """
        raise NotImplementedError("Método speak_response deve ser implementado pela classe filha")
