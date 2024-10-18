# Metadata for this task
description = "Respond normally to user queries."
trigger = "If it was a regular question, the type is 'normal'."
example = "{'type': 'handle_normal', 'content': 'The response to the user'}"

# Function that handles the task
def execute(content):
    print(f"Handling normal task: {content}")
    return content
