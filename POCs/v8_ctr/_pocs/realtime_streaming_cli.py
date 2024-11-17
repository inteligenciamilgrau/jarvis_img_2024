import logging
import asyncio
import os

from pynput import keyboard
from modules.open_ai.chat_realtime.client import RealtimeClient, AudioHandler, InputHandler, TurnDetectionMode
from llama_index.core.tools import FunctionTool

# Configuração do logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Adicione suas próprias ferramentas aqui!
# NOTA: FunctionTool analisa a docstring para obter a descrição, o nome da ferramenta é o nome da função
def pegue_o_numero_do_telefone_de(name: str) -> str:
    """Obtém meu número de telefone."""
    if name == "Diego":
        return "1234567890"
    elif name == "Logan":
        return "0987654321"
    else:
        return "Desconhecido"

tools = [FunctionTool.from_defaults(fn=pegue_o_numero_do_telefone_de)]

async def main():
    audio_handler = AudioHandler()
    input_handler = InputHandler()
    input_handler.loop = asyncio.get_running_loop()
    
    client = RealtimeClient(
        api_key=os.environ.get("OPENAI_API_KEY"),
        on_text_delta=lambda text: log.info(f"\nAssistente: {text}"),
        on_audio_delta=lambda audio: audio_handler.play_audio(audio),
        on_interrupt=lambda: audio_handler.stop_playback_immediately(),
        turn_detection_mode=TurnDetectionMode.SERVER_VAD,
        tools=tools,
    )

    # Inicia o listener de teclado em uma thread separada
    listener = keyboard.Listener(on_press=input_handler.on_press)
    listener.start()
    
    try:
        await client.connect()
        message_handler = asyncio.create_task(client.handle_messages())
        
        log.info("Conectado à API OpenAI Realtime!")
        log.info("A transmissão de áudio começará automaticamente.")
        log.info("Pressione 'q' para sair")
        log.info("")
        
        # Inicia a transmissão de áudio contínua
        streaming_task = asyncio.create_task(audio_handler.start_streaming(client))
        
        # Loop de entrada simples para o comando de saída
        while True:
            command, _ = await input_handler.command_queue.get()
            
            if command == 'q':
                break
            
    except Exception as e:
        log.info(f"Erro: {e}")
    finally:
        audio_handler.stop_streaming()
        audio_handler.cleanup()
        await client.close()

if __name__ == "__main__":
    log.info("Iniciando CLI da API Realtime com detecção de fala automática...")
    asyncio.run(main())
