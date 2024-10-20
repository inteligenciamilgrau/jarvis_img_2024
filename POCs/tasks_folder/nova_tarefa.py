import json
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

# Metadata for this task
description = "Este é um criador de novas tarefas"
trigger = "Quando o usuário pedir para fazer uma nova tarefa rode isto."
example = "{'type': 'nova_tarefa', 'content': 'Detalhes do que a tarefa tem que fazer'}"

client = OpenAI()

# Function that handles the task
def execute(content):
    # Parâmetros para o system prompt e user message
    system_prompt = """Você é um assistente que gera códigos em Python com base na descrição dada.
    Retorne um JSON no formato como no exemplo:
    {'name': 'function name', 'code': 'código em python'}

    O código precisa ter obrigatoriamente uma 'description', um 'trigger' e um 'example'.
    O código precisa ter também obrigatoriamente uma funçao 'execute'
    O tipo do example é o próprio nome do arquivo conforme o exemplo:

# Metadata for this task
description = '''descrição da tarefa. Peça as variaveis que precisa no formato JSON'''
trigger = '''explicação que o usuario precisa dar para executar esta tarefa'''
example = '''{'type': 'nome_da_tarefa', 'content': 'The response to the user. All variable needed must be in a JSON format'}'''

# coloque aqui as funções necessárias
def funcao_demonstracao(dados): 
    return 'Demonstracao' + str(dados)

# Function that handles the task
def execute(content): # o content vem sempre no formato string, peça um JSON se necessário
    print(f'Handling task: {content}')
    return str(funcao_demonstracao(content)) # sempre retorne uma string
    
    """
    user_message = content

    # Chamando o assistente para gerar o código
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    # Extraindo o conteúdo da resposta
    json_response = json.loads(response.choices[0].message.content)
    function_name = json_response['name']
    function_code = json_response['code']

    # Criando um arquivo Python com o nome da função e inserindo o código
    file_name = os.path.join(os.getcwd() + "\\tasks_folder\\", f"{function_name}.py")
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(function_code)

    tarefa_criada = f"Tarefa {function_name} criada com sucesso com o código da função {function_name}."
    print(tarefa_criada)
    return tarefa_criada


def main():
    # Exemplo de uso
    # Calcule a área de um círculo de raio 3
    evaluate_content = "Crie uma nova tarefa com nome 'calcular' que calcula a área de um círculo dado o raio."
    execute(evaluate_content)

if __name__ == "__main__":
    main()