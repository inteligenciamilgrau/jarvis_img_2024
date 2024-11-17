from openai import OpenAI

def get_ollama_response(user_message, chat_history):
    """
    Obtém a resposta da API Ollama.
    
    Args:
        user_message: A mensagem do usuário
        chat_history: O histórico do chat
        
    Returns:
        str: A resposta da API no formato JSON esperado pelo sistema de tarefas
    """
    client = OpenAI(api_key="nada", base_url="http://localhost:11434/v1/")
    try:
        response = client.chat.completions.create(
            model="llama2",
            messages=[{"role": "user", "content": user_message}],
            stream=False
        )
        
        # Extrai a resposta
        assistant_message = response.choices[0].message.content
        
        # Formata a resposta no formato esperado pelo sistema de tarefas
        task_response = {
            "type": "handle_normal",
            "content": {
                "question": user_message,
                "answer": assistant_message
            }
        }
        
        # Retorna a resposta formatada
        return task_response
    except Exception as e:
        error_response = {
            "type": "handle_normal",
            "content": {
                "question": user_message,
                "answer": f"Erro ao obter resposta do Ollama: {e}"
            }
        }
        return error_response
