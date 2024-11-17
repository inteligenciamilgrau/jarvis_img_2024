import logging
import time
from openai import OpenAI
import io
from pydub import AudioSegment

# Configuração do logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Inicializa o cliente OpenAI
client = OpenAI()

def test_standard_tts_format(format, text="Olá, isso é um teste de latência para formato de áudio."):
    """
    Testa a latência do TTS padrão para um formato específico
    Retorna uma tupla com:
    1. Tempo total (requisição + processamento)
    2. Tamanho do arquivo em bytes
    """
    start_time = time.time()
    
    try:
        # Faz a requisição para a API
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
            response_format=format
        )
        
        # Captura o conteúdo da resposta
        audio_content = response.content
            
        # Calcula o tempo total
        total_time = time.time() - start_time
        
        # Retorna tempo e tamanho
        return total_time, len(audio_content)
    except Exception as e:
        log.info(f"Erro no teste standard TTS - formato {format}: {e}")
        return None, None

def test_chat_completions_tts_format(format, text="Olá, isso é um teste de latência para formato de áudio."):
    """
    Testa a latência do Chat Completions TTS para um formato específico
    Retorna uma tupla com:
    1. Tempo total (requisição + processamento)
    2. Tamanho do arquivo em bytes
    """
    start_time = time.time()
    
    try:
        # Faz a requisição para a API
        completion = client.chat.completions.create(
            model="gpt-4o-audio-preview",
            modalities=["text","audio"],
            audio={"voice": "nova", "format": format},
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente prestativo que pode gerar áudio a partir de texto. Fale em português do Brasil com sotaque baiano, de forma clara e amigável, como se estivesse conversando com uma criança. Leia apenas o texto exatamente como está, sem adicionar, modificar ou interpretar nada além do que foi passado.",
                },
                {
                    "role": "user",
                    "content": text,
                }
            ],
        )
        
        # Decodifica o áudio base64 para bytes
        import base64
        audio_content = base64.b64decode(completion.choices[0].message.audio.data)
            
        # Calcula o tempo total
        total_time = time.time() - start_time
        
        # Retorna tempo e tamanho
        return total_time, len(audio_content)
    except Exception as e:
        log.info(f"Erro no teste Chat Completions TTS - formato {format}: {e}")
        return None, None

def main():
    """Testa a latência dos diferentes formatos para ambos os métodos TTS"""
    log.info("Iniciando testes de latência...")
    
    # Lista de formatos suportados
    formats = ["mp3", "opus", "flac", "wav", "pcm16"]
    
    # Executa 3 testes para cada formato para ter uma média
    num_tests = 3
    standard_results = {}
    chat_results = {}
    
    # Testes para TTS padrão
    log.info("\n=== Testes TTS Padrão ===")
    for fmt in formats:
        log.info(f"\nTestando formato: {fmt}")
        times = []
        sizes = []
        
        for i in range(num_tests):
            time_taken, size = test_standard_tts_format(fmt)
            if time_taken is not None:
                times.append(time_taken)
                sizes.append(size)
                log.info(f"  Teste {i+1}: {time_taken:.3f}s - Tamanho: {size/1024:.2f}KB")
        
        if times:
            avg_time = sum(times) / len(times)
            avg_size = sum(sizes) / len(sizes)
            standard_results[fmt] = {
                "avg_time": avg_time,
                "avg_size": avg_size
            }
    
    # Testes para Chat Completions TTS
    log.info("\n=== Testes Chat Completions TTS ===")
    for fmt in formats:
        log.info(f"\nTestando formato: {fmt}")
        times = []
        sizes = []
        
        for i in range(num_tests):
            time_taken, size = test_chat_completions_tts_format(fmt)
            if time_taken is not None:
                times.append(time_taken)
                sizes.append(size)
                log.info(f"  Teste {i+1}: {time_taken:.3f}s - Tamanho: {size/1024:.2f}KB")
        
        if times:
            avg_time = sum(times) / len(times)
            avg_size = sum(sizes) / len(sizes)
            chat_results[fmt] = {
                "avg_time": avg_time,
                "avg_size": avg_size
            }
    
    # Mostra resultados finais
    log.info("\n=== Resultados Finais TTS Padrão ===")
    log.info("-" * 50)
    log.info(f"{'Formato':<10} {'Tempo Médio':<15} {'Tamanho Médio'}")
    log.info("-" * 50)
    
    for fmt, data in standard_results.items():
        log.info(f"{fmt:<10} {data['avg_time']:.3f}s {data['avg_size']/1024:.2f}KB")
    
    log.info("\n=== Resultados Finais Chat Completions TTS ===")
    log.info("-" * 50)
    log.info(f"{'Formato':<10} {'Tempo Médio':<15} {'Tamanho Médio'}")
    log.info("-" * 50)
    
    for fmt, data in chat_results.items():
        log.info(f"{fmt:<10} {data['avg_time']:.3f}s {data['avg_size']/1024:.2f}KB")

if __name__ == "__main__":
    main()
