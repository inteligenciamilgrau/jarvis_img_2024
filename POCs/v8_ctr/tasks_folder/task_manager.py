import importlib.util
import os
from typing import Dict, Any, Callable
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class TaskManager:
    def __init__(self, tasks_path='tasks_folder', prompt_file='prompts/system_prompt.txt', spelling_prompt_file='prompts/spelling_correction_word.txt'):
        """
        Inicializa o gerenciador de tarefas.
        
        Args:
            tasks_path (str): Caminho para a pasta contendo os arquivos de tarefas
            prompt_file (str): Caminho para o arquivo de prompt do sistema
            spelling_prompt_file (str): Caminho para o arquivo de prompt de correção ortográfica
        """
        current_dir = os.path.dirname(os.path.dirname(__file__))  # Ajustado para considerar a nova estrutura
        self.tasks_path = os.path.join(current_dir, tasks_path)
        self.prompt_file = os.path.join(current_dir, prompt_file)
        self.spelling_prompt_file = os.path.join(current_dir, spelling_prompt_file)
        
        self.task_handlers = self.load_task_handlers(self.tasks_path)
        
        # Carrega e armazena o prompt de correção ortográfica em memória
        self.spelling_correction_prompt = self.load_spelling_correction_prompt()

    def load_task_handlers(self, tasks_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Carrega dinamicamente os manipuladores de tarefas do diretório especificado.
        
        Args:
            tasks_path (str): Caminho para o diretório contendo os arquivos de tarefas
            
        Returns:
            Dict[str, Dict[str, Any]]: Dicionário contendo os manipuladores de tarefas e seus metadados
        """
        handlers = {}
        for filename in os.listdir(tasks_path):
            if filename.endswith('.py') and filename != 'task_manager.py':  # Ignora o task_manager.py
                task_name = filename[:-3]  # Remove a extensão '.py'
                module_path = os.path.join(tasks_path, filename)
                
                try:
                    spec = importlib.util.spec_from_file_location(task_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Carrega os metadados e a função de execução
                    execute_func = getattr(module, 'execute', None)
                    if execute_func is None:
                        log.info("Erro: A tarefa %s não possui a função 'execute'.", task_name)
                    else:
                        log.info("Tarefa carregada: %s com a função execute.", task_name)
                    
                    handlers[task_name] = {
                        'description': getattr(module, 'description', 'Nenhuma descrição fornecida.'),
                        'trigger': getattr(module, 'trigger', 'Nenhum gatilho fornecido.'),
                        'example': getattr(module, 'example', 'Nenhum exemplo fornecido.'),
                        'execute': execute_func
                    }
                except Exception as e:
                    log.info("Erro ao carregar a tarefa %s: %s", task_name, e)
                    
        return handlers
    
    def load_system_prompt(self) -> str:
        """
        Carrega o prompt básico do sistema a partir de um arquivo de texto externo.
        
        Returns:
            str: Conteúdo do arquivo de prompt do sistema
            
        Raises:
            FileNotFoundError: Se o arquivo de prompt não for encontrado
        """
        try:
            with open(self.prompt_file, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"O arquivo de prompt do sistema '{self.prompt_file}' não existe.")

    def load_spelling_correction_prompt(self) -> str:
        """
        Carrega o prompt de correção ortográfica a partir de um arquivo de texto externo.
        
        Returns:
            str: Conteúdo do arquivo de prompt de correção ortográfica
            
        Raises:
            FileNotFoundError: Se o arquivo de prompt não for encontrado
        """
        try:
            with open(self.spelling_prompt_file, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"O arquivo de prompt de correção ortográfica '{self.spelling_prompt_file}' não existe.")

    def get_spelling_correction_prompt(self) -> str:
        """
        Retorna o prompt de correção ortográfica carregado em memória.
        
        Returns:
            str: Prompt de correção ortográfica
        """
        return self.spelling_correction_prompt

    def build_system_prompt(self) -> str:
        """
        Constrói um prompt de sistema dinâmico com descrições, gatilhos e exemplos para cada tarefa.
        
        Returns:
            str: Prompt do sistema completo com informações sobre todas as tarefas
        """
        # Recarrega os manipuladores de tarefas para garantir que temos as informações mais recentes
        # Removido para evitar chamadas desnecessárias
        # self.task_handlers = self.load_task_handlers(self.tasks_path)

        # Carrega o prompt base do sistema
        prompt = self.load_system_prompt() + "\n\n"
        
        # Adiciona informações sobre cada tarefa disponível
        prompt += "As tarefas disponíveis são as seguintes:\n"
        for task_name, task_info in self.task_handlers.items():
            prompt += f"\nTarefa: {task_name}\n"
            prompt += f"Descrição: {task_info['description']}\n"
            prompt += f"Gatilho: {task_info['trigger']}\n"
            prompt += f"Exemplo: {task_info['example']}\n"
            
        return prompt

    def execute_task(self, task_type: str, content: Any) -> Any:
        """
        Executa a tarefa apropriada com base no tipo de tarefa.
        
        Args:
            task_type (str): Tipo da tarefa a ser executada
            content (Any): Conteúdo/parâmetros para a execução da tarefa
            
        Returns:
            Any: Resultado da execução da tarefa
            
        Raises:
            KeyError: Se o tipo de tarefa não for encontrado
        """
        if task_type in self.task_handlers:
            try:
                return self.task_handlers[task_type]['execute'](content)
            except Exception as e:
                return f"Erro ao executar a tarefa {task_type}: {e}"
        else:
            return f"Tipo de tarefa desconhecido: {task_type}"

    def get_available_tasks(self) -> Dict[str, Dict[str, str]]:
        """
        Retorna um dicionário com informações sobre todas as tarefas disponíveis.
        
        Returns:
            Dict[str, Dict[str, str]]: Dicionário com informações sobre as tarefas
        """
        return {
            task_name: {
                'description': info['description'],
                'trigger': info['trigger'],
                'example': info['example']
            }
            for task_name, info in self.task_handlers.items()
        }

    def reload_tasks(self):
        """
        Recarrega todos os manipuladores de tarefas.
        Útil quando novas tarefas são adicionadas em tempo de execução.
        """
        self.task_handlers = self.load_task_handlers(self.tasks_path)
