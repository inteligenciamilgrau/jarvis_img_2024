description = '''Esta tarefa soma dois números fornecidos pelo usuário. As variáveis necessárias devem ser apresentadas em formato JSON.'''
trigger = '''Para executar esta tarefa, forneça uma entrada no formato JSON com os dois números a serem somados.'''
example = '''{'type': 'somar', 'content': '{"numero1": 5, "numero2": 10}'}''' 

def somar_numeros(dados): 
    numero1 = dados['numero1']
    numero2 = dados['numero2']
    return numero1 + numero2

def execute(content): 
    import json
    print(f'Handling task: {content}')
    dados = json.loads(content)  # faz o parse do JSON
    resultado = somar_numeros(dados)  # chama a função de soma
    return str(resultado)