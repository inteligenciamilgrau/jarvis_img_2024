import logging

# Metadados para esta tarefa
description = "Responde apenas quando alguém fala com Junin."
trigger = "Somente se alguém perguntar por Junin, o tipo é 'handle_normal'."
example = "{'type': 'handle_normal', 'content': {'question':'o texto original do usuário', 'answer':'A resposta para o usuário'}"

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Função que lida com a tarefa
def execute(content):
    #content = json.loads(content)
    logger.info(f"Tarefa normal:\nPergunta: {content['question']}\nResposta: {content['answer']}")
    return content['answer']
