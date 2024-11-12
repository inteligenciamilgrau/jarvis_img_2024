import queue
import threading
import concurrent.futures
from openai import OpenAI
import pyaudio
import numpy as np
import io
from pydub import AudioSegment

# Configurações de áudio otimizadas para baixa latência
CHUNK = 2048
CHANNELS = 1
RATE = 24000
FORMAT = pyaudio.paFloat32

class TextToSpeech:
    def __init__(self, voice_speed_var=None):
        self.client_openai = OpenAI()
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.queue = queue.Queue()
        self.audio_buffer = queue.Queue()
        self.lock = threading.Lock()
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        self.is_speaking = False
        self.stop_current = False
        self.speech_started_callback = None
        self.first_chunk_played = False
        self.voice = "nova"
        self.voice_speed_var = voice_speed_var  # Variável tkinter para velocidade da voz

    def _ensure_stream(self):
        """Garante que o stream está pronto para uso."""
        try:
            if self.stream is None or not self.stream.is_active():
                if self.stream is not None:
                    try:
                        self.stream.close()
                    except:
                        pass
                self.stream = self.p.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True,
                    frames_per_buffer=CHUNK,
                    start=True
                )
            return True
        except Exception as e:
            print(f"Erro ao inicializar o stream de áudio: {e}")
            return False

    def set_voice(self, voice):
        """Define a voz a ser usada."""
        self.voice = voice

    def _get_current_speed(self):
        """Obtém a velocidade atual da voz."""
        try:
            if self.voice_speed_var:
                return float(self.voice_speed_var.get())
            return 1.5  # Valor padrão se não houver variável
        except (ValueError, AttributeError):
            return 1.5

    def _generate_audio_for_sentence(self, sentence):
        """Gera áudio para uma sentença."""
        try:
            response = self.client_openai.audio.speech.create(
                model="tts-1",
                voice=self.voice,
                input=sentence.strip() + ".",
                response_format="mp3",
                speed=self._get_current_speed()  # Usa a velocidade da variável tkinter
            )
            
            # Processa o áudio em memória
            audio_segment = AudioSegment.from_mp3(io.BytesIO(response.content))
            audio_segment = audio_segment.set_frame_rate(RATE).set_channels(CHANNELS)
            
            # Obtém os dados como um array numpy
            samples = np.array(audio_segment.get_array_of_samples(), dtype=np.int16)
            float_samples = samples.astype(np.float32)
            max_value = np.max(np.abs(float_samples))
            if max_value > 0:
                float_samples = float_samples / max_value
            
            return float_samples
        except Exception as e:
            print(f"Erro ao gerar áudio para a sentença: {e}")
            return np.array([], dtype=np.float32)

    def _play_audio_chunks(self, float_samples):
        """Reproduz chunks de áudio."""
        if not self._ensure_stream():
            return

        for i in range(0, len(float_samples), CHUNK):
            if self.stop_current:
                break
                
            # Notifica quando o primeiro chunk começar a tocar
            if not self.first_chunk_played and self.speech_started_callback:
                self.speech_started_callback()
                self.first_chunk_played = True
            
            chunk = float_samples[i:i + CHUNK]
            if len(chunk) < CHUNK:
                chunk = np.pad(chunk, (0, CHUNK - len(chunk)), 'constant')
            
            try:
                self.stream.write(chunk.tobytes())
            except Exception as e:
                print(f"Erro ao reproduzir chunk de áudio: {e}")
                if not self._ensure_stream():
                    break

    def speak_response(self, response_text, on_speech_start=None):
        try:
            self.is_speaking = True
            self.stop_current = False
            self.first_chunk_played = False
            self.speech_started_callback = on_speech_start

            if not self._ensure_stream():
                return

            # Divide o texto em sentenças
            sentences = [s.strip() for s in response_text.split('.') if s.strip()]
            
            if not sentences:
                return

            # Processa a primeira sentença imediatamente
            first_audio = self._generate_audio_for_sentence(sentences[0])
            
            # Inicia o processamento paralelo das sentenças restantes
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                # Submete todas as sentenças restantes para processamento
                future_to_sentence = {
                    executor.submit(self._generate_audio_for_sentence, sentence): i 
                    for i, sentence in enumerate(sentences[1:], 1)
                }
                
                # Reproduz a primeira sentença
                self._play_audio_chunks(first_audio)
                
                # Processa as sentenças restantes na ordem
                for i in range(1, len(sentences)):
                    for future in concurrent.futures.as_completed(future_to_sentence):
                        if future_to_sentence[future] == i:
                            try:
                                audio_data = future.result()
                                if len(audio_data) > 0 and not self.stop_current:
                                    self._play_audio_chunks(audio_data)
                            except Exception as e:
                                print(f"Erro ao processar a sentença {i}: {e}")
                            break

            if self.stream and self.stream.is_active():
                self.stream.stop_stream()

        except Exception as e:
            print("Erro durante a conversão de texto em fala:", e)
            import traceback
            traceback.print_exc()
        finally:
            self.is_speaking = False
            self.stop_current = False
            self.first_chunk_played = False
            self.speech_started_callback = None

    def stop_speaking(self):
        """Para a reprodução atual."""
        self.stop_current = True
        while self.is_speaking:
            pass

    def enqueue_speak(self, response_text, on_speech_start=None):
        """Adiciona texto à fila de fala."""
        if self.is_speaking:
            self.stop_speaking()
        self.queue.put((response_text, on_speech_start))

    def _process_queue(self):
        """Processa a fila de textos para fala."""
        while True:
            try:
                item = self.queue.get()
                if item is None:
                    break
                
                response_text, on_speech_start = item
                self.speak_response(response_text, on_speech_start)
                
            except Exception as e:
                print(f"Erro no processamento da fila de fala: {e}")
            finally:
                self.queue.task_done()

    def cleanup(self):
        """Limpa os recursos do TTS."""
        try:
            if self.is_speaking:
                self.stop_speaking()
            
            self.queue.put(None)
            if self.worker_thread.is_alive():
                self.worker_thread.join(timeout=1)
            
            if self.stream:
                try:
                    if self.stream.is_active():
                        self.stream.stop_stream()
                    self.stream.close()
                except:
                    pass
                self.stream = None
            
            if self.p:
                self.p.terminate()
                
        except Exception as e:
            print(f"Erro durante a limpeza do TTS: {e}")
