import json
import logging
from openai import OpenAI
from .task_manager import TaskManager

class ChatHandler:
    def __init__(self):
        # Configura o logging
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        self.client = OpenAI()
        self.ollama_client = OpenAI(api_key="nada", base_url="http://localhost:11434/v1/")
        self.task_manager = TaskManager()
        self.chat_history = []
        self.initialize_chat_history()

    def initialize_chat_history(self):
        """Inicializa o histórico do chat com o prompt do sistema.""" 
        system_prompt = self.task_manager.build_system_prompt()
        self.chat_history = [{"role": "system", "content": system_prompt}]

    def get_response(self, user_message, use_ollama=False, model="gpt-4-1106-preview"):
        """
        Obtém a resposta da API OpenAI ou Ollama.
        
        Args:
            user_message: Mensagem de entrada do usuário
            use_ollama: Booleano indicando se deve usar Ollama
            model: O modelo a ser utilizado
        """
        try:
            if use_ollama:
                return self._get_ollama_response(user_message)
            else:
                # Registra o modelo sendo usado
                self.logger.info(f"Modelo: {model}")
                return self._get_openai_response(user_message, model)
        except Exception as e:
            return f"Desculpe, não consegui obter uma resposta. Erro: {e}"

    def _get_openai_response(self, user_message, model):
        """Obtém a resposta da API OpenAI.""" 
        try:
            # Atualiza o prompt do sistema
            system_prompt = self.task_manager.build_system_prompt()
            self.chat_history[0] = {"role": "system", "content": system_prompt}
            
            # Adiciona a mensagem do usuário ao histórico
            self.chat_history.append({"role": "user", "content": user_message})

            # Obtém a resposta da API
            response = self.client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=self.chat_history
            )

            # Analisa a resposta JSON
            json_response = json.loads(response.choices[0].message.content)
            response_type = json_response.get('type')
            response_content = json_response.get('content')

            # Executa a tarefa e obtém a resposta
            task_response = self.task_manager.execute_task(response_type, response_content)
            
            # Adiciona a resposta do assistente ao histórico
            self.chat_history.append({"role": "assistant", "content": task_response})

            return task_response

        except Exception as e:
            error_msg = f"Erro ao obter resposta do OpenAI: {e}"
            self.logger.error(error_msg)
            return error_msg

    def _get_ollama_response(self, user_message):
        """Obtém a resposta da API Ollama.""" 
        try:
            response = self.ollama_client.chat.completions.create(
                model="llama2",
                messages=[{"role": "user", "content": user_message}],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"Erro ao obter resposta do Ollama: {e}"
            self.logger.error(error_msg)
            return error_msg

    def get_chat_history(self):
        """Obtém o histórico atual do chat.""" 
        return self.chat_history

    def clear_chat_history(self):
        """Limpa o histórico do chat e reinicializa com o prompt do sistema.""" 
        self.initialize_chat_history()
