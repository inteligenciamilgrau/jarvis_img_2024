import json
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

# Metadados para esta tarefa
description = "Este é um criador de novas tarefas"
trigger = "Quando o usuário pedir para fazer uma nova tarefa, rode isto."
example = "{'type': 'nova_tarefa', 'content': 'Detalhes do que a tarefa tem que fazer'}"

client = OpenAI()

# Função que lida com a tarefa
def execute(content, model="gpt-4o-mini"):
    # Parâmetros para o prompt do sistema e mensagem do usuário
    system_prompt = """Você é um assistente que gera códigos em Python com base na descrição dada.
    Retorne um JSON no formato como no exemplo:
    {'name': 'nome da função', 'code': 'código em python'}

    O código precisa ter obrigatoriamente uma 'description', um 'trigger' e um 'example'.
    O código precisa ter também obrigatoriamente uma função 'execute'
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
    print(f'Tarefa: {content}', '\n')
    return str(funcao_demonstracao(content)) # sempre retorne uma string
    
    """
    user_message = content

    # Chamando o assistente para gerar o código
    response = client.chat.completions.create(
        model=model,
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
