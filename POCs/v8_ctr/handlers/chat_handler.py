import json
import logging
from openai import OpenAI
from modules.open_ai.chat.chat_completion import get_openai_response, get_openai_response_with_spellcheck
from modules.ollama.chat.chat_completion_ollama import get_ollama_response

class ChatHandler:
    def __init__(self, task_manager):
        # Configura o logging
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        self.client = OpenAI()
        self.ollama_client = OpenAI(api_key="nada", base_url="http://localhost:11434/v1/")
        self.task_manager = task_manager
        self.chat_history = []
        # Obtém o prompt do sistema uma única vez durante a inicialização
        self.system_prompt = self.task_manager.build_system_prompt()
        self.initialize_chat_history()

    def initialize_chat_history(self):
        """Inicializa o histórico do chat com o prompt do sistema.""" 
        # Usa o prompt do sistema já carregado ao invés de chamar build_system_prompt novamente
        self.chat_history = [{"role": "system", "content": self.system_prompt}]

    def get_response(self, user_message, use_ollama=False, model=None, is_corrected_text=False):
        """
        Obtém a resposta da API OpenAI ou Ollama.
        
        Args:
            user_message: Mensagem de entrada do usuário
            use_ollama: Booleano indicando se deve usar Ollama
            model: O modelo a ser utilizado
            is_corrected_text: Booleano indicando se o texto já foi corrigido
        """
        try:
            if use_ollama:
                response = get_ollama_response(user_message, self.chat_history)
            else:
                # Registra o modelo sendo usado
                self.logger.info(f"Modelo na Resposta: {model}")
                
                # Usa o método apropriado baseado no tipo de texto
                if is_corrected_text:
                    response = get_openai_response_with_spellcheck(user_message, model, self.chat_history)
                else:
                    response = get_openai_response(user_message, model, self.chat_history)

            # Executa a tarefa apropriada com base no tipo de resposta
            if isinstance(response, dict) and 'type' in response:
                task_type = response['type']
                task_content = response['content']
                # Executa a tarefa e obtém a resposta processada
                response_text = self.task_manager.execute_task(task_type, task_content)
            else:
                response_text = str(response)
            
            # Atualiza o histórico do chat apenas com o texto da resposta processada
            self.chat_history.append({"role": "user", "content": user_message})
            
            # Verifica se response_text é um dicionário e extrai apenas a resposta
            if isinstance(response_text, dict) and 'answer' in response_text:
                response_text = response_text['answer']
            
            self.chat_history.append({"role": "assistant", "content": response_text})
            
            return response_text
        except Exception as e:
            error_msg = f"Desculpe, não consegui obter uma resposta. Erro: {e}"
            return error_msg

    def get_chat_history(self):
        """Obtém o histórico atual do chat.""" 
        return self.chat_history

    def clear_chat_history(self):
        """Limpa o histórico do chat e reinicializa com o prompt do sistema.""" 
        self.initialize_chat_history()
