# Metadata for this task
description = "Esta é uma nova tarefa."
trigger = "Quando o usuário pedir para fazer uma nova tarefa rode isto."
example = "{'type': 'nova_tarefa', 'content': 'O nome da tarefa pedida'}"

# Function that handles the task
def execute(content):
    print(f"Rodando a nova tarefa: {content}")
    return content
