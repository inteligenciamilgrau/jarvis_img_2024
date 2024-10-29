# Metadata for this task
description = "Respond only when someone talk to Junin."
trigger = "Only if someone ask for Junin, the type is 'handle_normal'."
example = "{'type': 'handle_normal', 'content': {'question':'the original text of the user', 'answer':'The response to the user'}"

# Function that handles the task
def execute(content):
    #content = json.loads(content)
    print(f"Tarefa normal:\nPergunta: {content['question']}\nResposta: {content['answer']}", "\n")
    return content['answer']
