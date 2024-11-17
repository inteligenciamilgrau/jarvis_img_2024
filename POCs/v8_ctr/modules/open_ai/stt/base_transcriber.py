import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class BaseTranscriber:
    """Classe base para funcionalidade de transcrição compartilhada"""
    def __init__(self, client, logger, vars=None):
        """
        Inicializa o transcritor base.
        
        Args:
            client: Cliente OpenAI inicializado
            logger: Logger configurado
            vars: Variáveis da UI (opcional)
        """
        self.client = client
        self.logger = logger
        self.vars = vars

    def transcribe(self, input_data):
        """
        Método abstrato para transcrição/correção.
        
        Args:
            input_data: Pode ser um objeto BytesIO contendo dados de áudio
                       ou uma string contendo texto para correção
            
        Returns:
            str: Texto transcrito/corrigido
        """
        raise NotImplementedError("Método transcribe deve ser implementado pela classe filha")

    def _log_transcription_details(self, audio_file, model=""):
        """
        Registra detalhes da solicitação de transcrição de áudio.
        
        Args:
            audio_file: Objeto BytesIO contendo os dados de áudio
            model: Nome do modelo sendo usado
        """
        log.info("Detalhes da Solicitação de Transcrição:")
        log.info("Modelo: %s", model)
        log.info("Tamanho do Arquivo: %d bytes", len(audio_file.getvalue()))

    def _log_correction_details(self, text, model=""):
        """
        Registra detalhes da solicitação de correção de texto.
        
        Args:
            text: Texto a ser corrigido
            model: Nome do modelo sendo usado
        """
        log.info("Detalhes da Solicitação de Correção:")
        log.info("Modelo: %s", model)
        log.info("Texto Original: %s", text)
