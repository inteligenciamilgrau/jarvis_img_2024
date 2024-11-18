import numpy as np
from .base_transcriber import BaseTranscriber
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class LocalTranscriber(BaseTranscriber):
    """Implementação do transcritor usando Whisper localmente"""
    
    def transcribe(self, audio_file):
        """
        Transcreve áudio usando o modelo Whisper local.
        
        Args:
            audio_file: Objeto BytesIO contendo os dados de áudio
            
        Returns:
            str: Texto transcrito
        """
        try:
            import whisper
            self._log_transcription_details(audio_file, "whisper-base-local")
            
            local_model = whisper.load_model("base")
            audio_file.seek(0)
            audio_data = np.frombuffer(audio_file.read(), np.int16).astype(np.float32) / 32768.0
            result = local_model.transcribe(audio_data)
            return result.get("text", "")
            
        except Exception as e:
            log.error("Erro na Transcrição Local: %s", e)
            return f"Erro na Transcrição Local: {e}"
