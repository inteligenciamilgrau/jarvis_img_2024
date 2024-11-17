from .base_transcriber import BaseTranscriber
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class SpellcheckTranscriber(BaseTranscriber):
    """
    Implementação do transcritor com correção ortográfica usando GPT-4.
    """
    
    def __init__(self, client, logger, task_manager, vars=None):
        """
        Inicializa o SpellcheckTranscriber.
        
        Args:
            client: Cliente OpenAI
            logger: Logger para registrar informações
            task_manager: Instância do TaskManager para acessar o prompt de correção
            vars: Variáveis de configuração (opcional)
        """
        super().__init__(client, logger, vars)
        log.info("Inicializando SpellcheckTranscriber")
        self.task_manager = task_manager
        self.correct_terms = self.task_manager.get_spelling_correction_prompt().strip().split('\n')
        # Remove espaços em branco e vírgulas extras
        self.correct_terms = [term.strip().strip(',') for term in self.correct_terms if term.strip()]

    def transcribe(self, text):
        """
        Aplica correção ortográfica ao texto fornecido.
        
        Args:
            text: Texto a ser corrigido
            
        Returns:
            str: Texto corrigido
        """
        try:
            log.info("Iniciando correção ortográfica")
            log.info("Texto original: %s", text)

            # Prepara o prompt do sistema
            system_message = (
                "Corrija o texto usando a lista de termos fornecida como referência. "
                "Retorne apenas o texto corrigido, sem explicações.\n\n"
                f"Termos corretos: {', '.join(self.correct_terms)}"
            )

            # Aplica correção com GPT-4
            selected_model = self.vars['chatgpt_model'].get() if self.vars else "gpt-4"
            log.info("Aplicando correção com modelo %s", selected_model)

            completion = self.client.chat.completions.create(
                model=selected_model,
                temperature=0,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": text}
                ]
            )
            
            corrected_text = completion.choices[0].message.content.strip()
            log.info("Texto corrigido: %s", corrected_text)
            
            return corrected_text
            
        except Exception as e:
            log.error("Erro durante correção ortográfica: %s", e)
            return text  # Retorna o texto original em caso de erro
