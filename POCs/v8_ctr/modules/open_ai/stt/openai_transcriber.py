from .base_transcriber import BaseTranscriber
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class OpenAITranscriber(BaseTranscriber):
    """Implementação do transcritor usando a API OpenAI"""
    
    def transcribe(self, audio_file):
        """
        Transcreve áudio usando a API OpenAI.
        
        Args:
            audio_file: Objeto BytesIO contendo os dados de áudio
            
        Returns:
            str: Texto transcrito
        """
        try:
            if not self.client:
                raise ValueError("Cliente OpenAI não inicializado")
            
            audio_file.seek(0)
            self._log_transcription_details(audio_file, "whisper-1")
            
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            
            transcribed_text = response.text
            log.info("Texto transcrito: %s", transcribed_text)
            
            return transcribed_text
            
        except Exception as e:
            log.error("Erro na Transcrição: %s", e)
            return f"Erro na Transcrição: {e}"
