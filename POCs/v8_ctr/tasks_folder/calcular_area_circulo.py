import math

# Metadados para esta tarefa
description = '''Esta tarefa calcula a área de um círculo dado o raio como entrada. A fórmula utilizada é A = π * r², onde A é a área e r é o raio.''' 
trigger = '''Para calcular a área do círculo, forneça o raio em formato JSON como {'raio': <valor_do_raio>}''' 
example = '''{'type': 'task_new', 'content': 'A resposta para o usuário: O valor da área é <resultado>'}''' 

# Função que calcula a área do círculo
def calcular_area(raio):
    return math.pi * (raio ** 2)

# Função que lida com a tarefa
def execute(content):  # o conteúdo sempre vem no formato string, peça um JSON se necessário
    import json
    dados = json.loads(content)
    raio = dados['raio']
    area = calcular_area(raio)
    return f'A área do círculo é: {area}'