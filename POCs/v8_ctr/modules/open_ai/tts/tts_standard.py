import time
import io
from pydub import AudioSegment
import numpy as np
from .tts_base import BaseTTS
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class StandardTTS(BaseTTS):
    """Implementação do TTS padrão usando o modelo tts-1"""
    
    def speak_response(self, response_text, on_speech_start=None):
        """Processa e reproduz o texto como áudio usando TTS padrão."""
        if self._shutdown:
            return
            
        try:
            log.info("\n=== Iniciando speak_response (TTS-1) ===")
            log.info("Texto recebido: %s", response_text)
            log.info("Modelo atual: %s", self.model)
            
            self.is_speaking = True
            self.stop_current = False
            self.first_chunk_played = False
            self.speech_started_callback = on_speech_start
            self.sentence_metrics = []  # Limpa métricas anteriores

            if not self.audio_stream.ensure_stream():
                return

            log.info("\n=== Processando com TTS-1 ===")
            self._process_sentences(response_text)

            log.info("=== Finalizando speak_response ===\n")

        except Exception as e:
            log.error("Erro durante a conversão de texto em fala: %s", e)
            import traceback
            traceback.print_exc()
        finally:
            self.is_speaking = False
            self.stop_current = False
            self.first_chunk_played = False
            self.speech_started_callback = None

    def _process_sentences(self, response_text):
        """Processa o texto dividindo em sentenças e gerando áudio para cada uma."""
        process_start_time = time.time()
        sentences = [s.strip() for s in response_text.split('.') if s.strip()]
        if not sentences:
            return

        log.info("Número de sentenças: %d", len(sentences))
        
        # Processa primeira sentença
        first_audio = self._generate_audio_for_sentence(sentences[0], 0)
        
        # Submete sentenças restantes para processamento paralelo
        futures = []
        for i, sentence in enumerate(sentences[1:], 1):
            if not self._shutdown:
                future = self.executor.submit(self._generate_audio_for_sentence, sentence, i)
                futures.append((future, i))
        
        # Reproduz primeira sentença
        if not self._shutdown:
            self.audio_stream.play_audio_chunks(
                first_audio,
                stop_flag=self.stop_current,
                on_first_chunk=self.speech_started_callback
            )
        
        # Processa sentenças restantes
        self._process_remaining_sentences(futures)
        
        self._print_statistics(len(sentences), process_start_time)

    def _generate_audio_for_sentence(self, sentence, sentence_index=0):
        """Gera áudio para uma única sentença."""
        if self._shutdown:
            return np.array([], dtype=np.float32)
            
        try:
            sentence_start_time = time.time()
            log.info("\n=== Processando sentença %d (TTS-1) ===", sentence_index + 1)
            log.info("Texto: %s", sentence)
            
            api_call_start = time.time()
            response = self.client_openai.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=sentence.strip() + ".",
                response_format="aac",  # Alterado de mp3 para aac
                speed=self._get_current_speed()
            )
            api_call_time = time.time() - api_call_start
            
            processing_start = time.time()
            audio_segment = AudioSegment.from_file(io.BytesIO(response.content), format="aac")  # Alterado para ler formato aac
            audio_segment = audio_segment.set_frame_rate(24000).set_channels(1)
            
            samples = np.array(audio_segment.get_array_of_samples(), dtype=np.int16)
            float_samples = samples.astype(np.float32)
            max_value = np.max(np.abs(float_samples))
            if max_value > 0:
                float_samples = float_samples / max_value
            
            processing_time = time.time() - processing_start
            total_time = time.time() - sentence_start_time
            
            # Armazena métricas da sentença
            self.sentence_metrics.append({
                'index': sentence_index + 1,
                'text_length': len(sentence),
                'api_time': api_call_time,
                'processing_time': processing_time,
                'total_time': total_time
            })
            
            log.info("Tempo de API: %.2f segundos", api_call_time)
            log.info("Tempo de processamento: %.2f segundos", processing_time)
            log.info("Tempo total: %.2f segundos", total_time)
            
            return float_samples
                
        except Exception as e:
            log.error("Erro ao gerar áudio para a sentença: %s", e)
            return np.array([], dtype=np.float32)

    def _process_remaining_sentences(self, futures):
        """Processa as sentenças restantes após a primeira."""
        for future, idx in futures:
            if self._shutdown:
                break
            try:
                audio_data = future.result(timeout=10)
                if len(audio_data) > 0 and not self.stop_current and not self._shutdown:
                    self.audio_stream.play_audio_chunks(
                        audio_data,
                        stop_flag=self.stop_current,
                        on_first_chunk=None
                    )
            except Exception as e:
                log.error("Erro ao processar a sentença %d: %s", idx, e)

    def _print_statistics(self, num_sentences, process_start_time):
        """Imprime estatísticas do processamento."""
        total_process_time = time.time() - process_start_time
        
        log.info("\n=== Estatísticas Finais (TTS-1) ===")
        log.info("Total de sentenças processadas: %d", num_sentences)
        log.info("Tempo total de processamento: %.2f segundos", total_process_time)
        
        if self.sentence_metrics:
            # Calcula e exibe médias
            avg_api_time = sum(m['api_time'] for m in self.sentence_metrics) / len(self.sentence_metrics)
            avg_processing_time = sum(m['processing_time'] for m in self.sentence_metrics) / len(self.sentence_metrics)
            avg_total_time = sum(m['total_time'] for m in self.sentence_metrics) / len(self.sentence_metrics)
            
            log.info("\nMétricas médias por sentença:")
            log.info("Tempo médio de API: %.2f segundos", avg_api_time)
            log.info("Tempo médio de processamento: %.2f segundos", avg_processing_time)
            log.info("Tempo médio total: %.2f segundos", avg_total_time)
            
            log.info("\nDetalhes por sentença:")
            for metric in self.sentence_metrics:
                log.info("\nSentença %d:", metric['index'])
                log.info("Comprimento do texto: %d caracteres", metric['text_length'])
                log.info("Tempo de API: %.2f segundos", metric['api_time'])
                log.info("Tempo de processamento: %.2f segundos", metric['processing_time'])
                log.info("Tempo total: %.2f segundos", metric['total_time'])
