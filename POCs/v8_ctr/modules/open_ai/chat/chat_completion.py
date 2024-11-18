from openai import OpenAI
import json
import logging

# Configura o logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_openai_response(user_message, model, chat_history):
    """
    Obtém uma resposta da API OpenAI.
    
    Args:
        user_message: A mensagem do usuário
        model: O modelo a ser usado
        chat_history: O histórico do chat
        
    Returns:
        str: A resposta da API no formato JSON esperado pelo sistema de tarefas
    """
    client = OpenAI()
    try:
        # Adiciona a mensagem do usuário ao histórico
        chat_history.append({"role": "user", "content": user_message})
        
        # Faz a chamada à API
        response = client.chat.completions.create(
            model=model,
            messages=chat_history,
            temperature=0.4,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        # Extrai a resposta
        assistant_message = response.choices[0].message.content
        
        # Verifica se a mensagem contém palavras-chave relacionadas à criação de tarefas
        if any(keyword in user_message.lower() for keyword in ["nova tarefa", "criar tarefa", "adicionar tarefa"]):
            task_response = {
                "type": "task_new",  # Alterado para corresponder ao nome do arquivo sem .py
                "content": assistant_message
            }
        else:
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
        logger.error(f"Erro ao obter resposta da OpenAI: {e}")
        error_response = {
            "type": "handle_normal",
            "content": {
                "question": user_message,
                "answer": f"Desculpe, ocorreu um erro ao processar sua solicitação: {e}"
            }
        }
        return error_response

def get_openai_response_with_spellcheck(corrected_text, model, chat_history):
    """
    Obtém uma resposta da API OpenAI usando o texto já corrigido.
    
    Args:
        corrected_text: O texto já corrigido pelo SpellcheckTranscriber
        model: O modelo a ser usado
        chat_history: O histórico do chat
        
    Returns:
        str: A resposta da API no formato JSON esperado pelo sistema de tarefas
    """
    client = OpenAI()
    try:
        # Adiciona o texto corrigido ao histórico
        chat_history.append({"role": "user", "content": corrected_text})
        
        # Faz a chamada à API com o texto corrigido
        response = client.chat.completions.create(
            model=model,
            messages=chat_history,
            temperature=0.2,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        # Extrai a resposta
        assistant_message = response.choices[0].message.content
        
        # Verifica se a mensagem contém palavras-chave relacionadas à criação de tarefas
        if any(keyword in corrected_text.lower() for keyword in ["nova tarefa", "criar tarefa", "adicionar tarefa"]):
            task_response = {
                "type": "task_new",  # Alterado para corresponder ao nome do arquivo sem .py
                "content": assistant_message
            }
        else:
            task_response = {
                "type": "handle_normal",
                "content": {
                    "question": corrected_text,
                    "answer": assistant_message
                }
            }
        
        # Retorna a resposta formatada
        return task_response
    except Exception as e:
        logger.error(f"Erro ao obter resposta da OpenAI para texto corrigido: {e}")
        error_response = {
            "type": "handle_normal",
            "content": {
                "question": corrected_text,
                "answer": f"Desculpe, ocorreu um erro ao processar sua solicitação: {e}"
            }
        }
        return error_response
