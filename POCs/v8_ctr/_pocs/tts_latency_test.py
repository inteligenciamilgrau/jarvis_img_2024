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

def test_format_latency(format, text="Olá, isso é um teste de latência para formato de áudio."):
    """
    # Testa a latência de um formato específico
    # Retorna uma tupla com:
    # 1. Tempo total (requisição + processamento)
    # 2. Tamanho do arquivo em bytes
    """
    start_time = time.time()
    
    # Faz a requisição para a API
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=text,
        response_format=format
    )
    
    # Captura o conteúdo da resposta
    if format == "mp3":
        audio_content = response.content
    else:
        audio_content = response.read()
        
    # Calcula o tempo total
    total_time = time.time() - start_time
    
    # Retorna tempo e tamanho
    return total_time, len(audio_content)

def main():
    """Testa a latência dos diferentes formatos"""
    log.info("Iniciando testes de latência...")
    
    # Lista de formatos para testar
    formats = ["mp3", "opus", "aac", "flac"]
    
    # Executa 5 testes para cada formato para ter uma média
    num_tests = 5
    results = {}
    
    for fmt in formats:
        log.info(f"\nTestando formato: {fmt}")
        times = []
        sizes = []
        
        for i in range(num_tests):
            try:
                time_taken, size = test_format_latency(fmt)
                times.append(time_taken)
                sizes.append(size)
                log.info(f"  Teste {i+1}: {time_taken:.3f}s - Tamanho: {size/1024:.2f}KB")
            except Exception as e:
                log.info(f"  Erro no teste {i+1}: {e}")
                continue
        
        if times:
            avg_time = sum(times) / len(times)
            avg_size = sum(sizes) / len(sizes)
            results[fmt] = {
                "avg_time": avg_time,
                "avg_size": avg_size
            }
    
    # Mostra resultados finais
    log.info("\nResultados Finais:")
    log.info("-" * 50)
    log.info(f"{'Formato':<10} {'Tempo Médio':<15} {'Tamanho Médio'}")
    log.info("-" * 50)
    
    for fmt, data in results.items():
        log.info(f"{fmt:<10} {data['avg_time']:.3f}s {data['avg_size']/1024:.2f}KB")

if __name__ == "__main__":
    main()
