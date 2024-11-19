import json

# Metadata for this task
description = "Talking about something."
#trigger = "If it was a regular question, the type is 'normal'."
trigger = "When you read something without your name, the type is 'handle_pensamento'."
example = "{'type': 'handle_pensamento', 'content': {'pensamento':'Your thoughts about what was said'}"

# Function that handles the task
def execute(content):
    #content = json.loads(content)
    print(f"Tarefa pensamento: {content}", "\n")
    return "Pensamento: " + content['pensamento']
