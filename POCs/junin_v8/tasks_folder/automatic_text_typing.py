description = '''Esta tarefa recebe um texto como entrada e utiliza Python para digitar esse texto automaticamente.'''
trigger = '''Por favor, forneça o texto que você deseja digitar automaticamente em formato JSON.'''
example = '''{'type': 'automatic_text_typing', 'content': 'O texto que você deseja digitar.'}'''  

def funcao_digitacao(texto): 
    import pyautogui
    pyautogui.typewrite(texto)
    pyautogui.press('enter')
    return 'Texto digitado com sucesso!'

# Function that handles the task
def execute(content): # o content vem sempre no formato string, peça um JSON se necessário
    print(f'Tarefa: {content}\n')
    return str(funcao_digitacao(content)) # sempre retorne uma string