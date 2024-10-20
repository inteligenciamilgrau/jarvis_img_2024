description = '''Esta tarefa calcula a área de um círculo dado o raio. Você precisa fornecer o raio no formato JSON.'''
trigger = '''Para executar esta tarefa, forneça o raio como um número decimal no formato JSON.'''
example = '''{'type': 'calcular', 'content': '{"raio": 5}'}'''  

import math

def calcular_area(raio): 
    return math.pi * (raio ** 2)

# Function that handles the task
def execute(content): # o content vem sempre no formato string
    import json
    dados = json.loads(content)
    raio = dados['raio']
    area = calcular_area(raio)
    return str(area)  # sempre retorne uma string