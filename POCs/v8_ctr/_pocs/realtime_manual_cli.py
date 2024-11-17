import logging
import asyncio
import os

from pynput import keyboard
from modules.open_ai.chat_realtime.client import RealtimeClient, InputHandler, AudioHandler
from llama_index.core.tools import FunctionTool

# Configuração do logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Adicione suas próprias ferramentas aqui!
# NOTA: FunctionTool analisa a docstring para obter a descrição, o nome da ferramenta é o nome da função
def get_phone_number(name: str) -> str:
    """Obtém meu número de telefone."""
    if name == "Jerry":
        return "1234567890"
    elif name == "Logan":
        return "0987654321"
    else:
        return "Desconhecido"

tools = [FunctionTool.from_defaults(fn=get_phone_number)]

async def main():
    # Inicializa os manipuladores
    audio_handler = AudioHandler()
    input_handler = InputHandler()
    input_handler.loop = asyncio.get_running_loop()
    
    # Inicializa o cliente realtime
    client = RealtimeClient(
        api_key=os.environ.get("OPENAI_API_KEY"),
        on_text_delta=lambda text: log.info(f"\nAssistente: {text}"),
        on_audio_delta=lambda audio: audio_handler.play_audio(audio),
        on_input_transcript=lambda transcript: log.info(f"\nVocê disse: {transcript}\nAssistente: "),
        on_output_transcript=lambda transcript: log.info(f"{transcript}"),
        tools=tools,
    )
    
    # Inicia o listener de teclado em uma thread separada
    listener = keyboard.Listener(on_press=input_handler.on_press)
    listener.start()
    
    try:
        # Conecta-se à API
        await client.connect()
        
        # Inicia o tratamento de mensagens em segundo plano
        message_handler = asyncio.create_task(client.handle_messages())
        
        log.info("Conectado à API OpenAI Realtime!")
        log.info("Comandos:")
        log.info("- Digite sua mensagem e pressione Enter para enviar texto")
        log.info("- Pressione 'r' para iniciar a gravação de áudio")
        log.info("- Pressione 'espaço' para parar a gravação")
        log.info("- Pressione 'q' para sair")
        log.info("")        
 
        while True:
            # Aguarda comandos do manipulador de entrada
            command, data = await input_handler.command_queue.get()
            
            if command == 'q':
                break
            elif command == 'r':
                # Inicia a gravação
                audio_handler.start_recording()
            elif command == 'space':
                log.info("[Preparando para parar a gravação]")
                if audio_handler.recording:
                    # Para a gravação e obtém os dados de áudio
                    audio_data = audio_handler.stop_recording()
                    log.info("[Gravação parada]")
                    if audio_data:
                        await client.send_audio(audio_data)
                        log.info("[Áudio enviado]")
            elif command == 'enter' and data:
                # Envia mensagem de texto
                await client.send_text(data)

            await asyncio.sleep(0.01) 
    except Exception as e:
        log.info(f"Erro: {e}")
    finally:
        # Limpa
        listener.stop()
        audio_handler.cleanup()
        await client.close()

if __name__ == "__main__":
    # Instale os pacotes necessários:
    # pip install pyaudio pynput pydub websockets

    log.info("Iniciando CLI da API Realtime...")
    asyncio.run(main())
