import json
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from config.settings_manager import SettingsManager

load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Metadados para esta tarefa
description = "Este é um criador de novas tarefas"
trigger = "Quando o usuário pedir para fazer uma nova tarefa, rode isto."
example = "{'type': 'nova_tarefa', 'content': 'Detalhes do que a tarefa tem que fazer'}"

client = OpenAI()

# Função que lida com a tarefa
def execute(content, model=None):
    log.info(f"Iniciando execução da tarefa com conteúdo: {content}")
    
    try:
        # Obtém o modelo selecionado das configurações
        settings_manager = SettingsManager("junin_settings.json")
        selected_model = model or settings_manager.get_setting("selected_model", "gpt-4-mini")
        log.info(f"Modelo selecionado: {selected_model}")

        # Verifica se o conteúdo é um JSON string e tenta extrair
        try:
            if isinstance(content, str):
                content_dict = json.loads(content)
                if isinstance(content_dict, dict) and 'content' in content_dict:
                    content = content_dict['content']
                    log.info(f"Conteúdo extraído do JSON: {content}")
        except json.JSONDecodeError:
            log.info("Conteúdo não é um JSON válido, usando como está")

        # Parâmetros para o prompt do sistema e mensagem do usuário
        system_prompt = """Você é um assistente que gera códigos em Python com base na descrição dada.
        Retorne um JSON no formato como no exemplo:
        {'name': 'nome da função', 'code': 'código em python'}

        O código precisa ter obrigatoriamente uma 'description', um 'trigger' e um 'example'.
        O código precisa ter também obrigatoriamente uma função 'execute'
        Ao final verifique se fez os importes corretamente.
        O tipo do example é o próprio nome do arquivo conforme o exemplo:

    # Metadados para esta tarefa
    description = '''descrição da tarefa. Peça as variáveis que precisa no formato JSON'''
    trigger = '''explicação que o usuário precisa dar para executar esta tarefa'''
    example = '''{'type': 'nome_da_tarefa', 'content': 'A resposta para o usuário. Todas as variáveis necessárias devem estar em formato JSON'}'''


    # coloque aqui as funções necessárias
    def funcao_demonstracao(dados): 
        return 'Demonstração' + str(dados)

    # Função que lida com a tarefa
    def execute(content): # o conteúdo sempre vem no formato string, peça um JSON se necessário
        log.info(f'Tarefa: {content}', '\n')
        return str(funcao_demonstracao(content)) # sempre retorne uma string
        
        """
        log.info("Enviando requisição para o OpenAI")
        
        # Chamando o assistente para gerar o código
        response = client.chat.completions.create(
            model=selected_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ]
        )

        log.info("Resposta recebida do OpenAI")
        log.info(f"Conteúdo da resposta: {response.choices[0].message.content}")

        # Extraindo o conteúdo da resposta
        json_response = json.loads(response.choices[0].message.content)
        function_name = json_response['name']
        function_code = json_response['code']

        log.info(f"Nome da função: {function_name}")
        log.info(f"Código gerado: {function_code}")

        # Criando um arquivo Python com o nome da função e inserindo o código
        file_name = os.path.join(os.getcwd(), "tasks_folder", f"{function_name}.py")
        log.info(f"Criando arquivo em: {file_name}")
        
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(function_code)
            log.info("Arquivo criado com sucesso")

        tarefa_criada = f"Tarefa {function_name} criada com sucesso com o código da função {function_name}."
        log.info(f"{tarefa_criada}")
        return tarefa_criada

    except Exception as e:
        erro = f"Erro ao criar tarefa: {str(e)}"
        log.info(f"{erro}")
        return erro


def main():
    # Exemplo de uso
    evaluate_content = "Crie uma nova tarefa com nome 'calcular' que calcula a área de um círculo dado o raio."
    execute(evaluate_content)

if __name__ == "__main__":
    main()
