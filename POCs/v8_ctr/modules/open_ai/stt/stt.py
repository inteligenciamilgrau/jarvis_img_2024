from .openai_transcriber import OpenAITranscriber
from .local_transcriber import LocalTranscriber
from .spellcheck_transcriber import SpellcheckTranscriber
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class SpeechToText:
    """
    Classe principal que gerencia diferentes implementações de transcrição.
    Atua como uma fábrica para criar a implementação apropriada com base nas opções.
    """
    def __init__(self, client, logger, task_manager, vars=None):
        """
        Inicializa o gerenciador de transcrição.
        
        Args:
            client: Cliente OpenAI inicializado
            logger: Logger configurado
            task_manager: Instância do TaskManager para acessar prompts
            vars: Variáveis da UI (opcional)
        """
        self.client = client
        self.logger = logger
        self.task_manager = task_manager
        self.vars = vars

    def transcribe_audio(self, audio_file, use_local=False, use_spellcheck=False):
        """
        Transcreve áudio para texto usando a implementação apropriada.
        
        Args:
            audio_file: Objeto BytesIO contendo os dados de áudio
            use_local: Booleano indicando se deve usar o modelo Whisper local
            use_spellcheck: Booleano indicando se deve usar correção ortográfica
            
        Returns:
            str: Texto transcrito
        """
        log.info("=== Iniciando transcribe_audio ===")
        log.info("Parâmetros: use_local=%s, use_spellcheck=%s", use_local, use_spellcheck)
        
        try:
            # Primeiro faz a transcrição normal
            if use_local:
                transcriber = LocalTranscriber(self.client, self.logger, self.vars)
            else:
                transcriber = OpenAITranscriber(self.client, self.logger, self.vars)
            
            # Executa a transcrição inicial
            transcribed_text = transcriber.transcribe(audio_file)
            
            # Se necessário, aplica a correção ortográfica
            if use_spellcheck:
                log.info("Aplicando correção ortográfica ao texto transcrito")
                spellchecker = SpellcheckTranscriber(self.client, self.logger, self.task_manager, self.vars)
                corrected_text = spellchecker.transcribe(transcribed_text)
                return corrected_text
            
            return transcribed_text
            
        except Exception as e:
            log.error("Erro na Transcrição: %s", e)
            return f"Erro na Transcrição: {e}"
