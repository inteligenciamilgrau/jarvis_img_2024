import pyaudio
import numpy as np
import io
import base64
from pydub import AudioSegment
import asyncio
import threading
import queue
import logging
from config.audio_config import AudioDeviceConfig

# Configuração do logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Configurações de áudio otimizadas para baixa latência e compatibilidade com GPT-4
CHUNK = 2048  # Aumentado para melhor buffer
CHANNELS = 1
RATE = 24000  # Ajustado para 24000Hz para compatibilidade com GPT-4
FORMAT = pyaudio.paFloat32
BUFFER_SIZE = 10  # Número de chunks no buffer

class AudioChunkProcessor:
    """Classe para processar chunks de áudio base64 de forma assíncrona"""
    def __init__(self, chunk_size=8192):  # Reduzido para 8KB chunks
        self.chunk_size = chunk_size
        
    def process_base64_chunks(self, base64_data):
        """Processa o áudio base64 em chunks, retornando um gerador"""
        try:
            # Decodifica todo o base64 primeiro
            decoded_data = base64.b64decode(base64_data + "=" * (-len(base64_data) % 4))
            
            # Converte para AudioSegment uma única vez
            audio = AudioSegment.from_mp3(io.BytesIO(decoded_data))
            audio = audio.set_channels(CHANNELS)
            
            # Obtém todos os samples de uma vez
            samples = np.array(audio.get_array_of_samples(), dtype=np.int16)
            float_samples = samples.astype(np.float32)
            
            # Normaliza todo o áudio de uma vez
            max_value = np.max(np.abs(float_samples))
            if max_value > 0:
                float_samples = float_samples / max_value
            
            # Divide em chunks menores para processamento
            for i in range(0, len(float_samples), self.chunk_size):
                chunk = float_samples[i:i + self.chunk_size]
                yield chunk
                
        except Exception as e:
            log.error("Erro ao processar áudio: %s", e)
            yield np.array([], dtype=np.float32)

    async def process_audio_chunk(self, chunk):
        """Processa um chunk de áudio de forma assíncrona"""
        try:
            return chunk  # O chunk já está processado no formato correto
        except Exception as e:
            log.error("Erro ao processar chunk de áudio: %s", e)
            return np.array([], dtype=np.float32)

class AudioStreamManager:
    """Gerencia o stream de áudio para reprodução"""
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.lock = threading.Lock()
        self.buffer = queue.Queue(maxsize=BUFFER_SIZE)
        self.is_playing = False
        self.play_thread = None
        self.audio_config = AudioDeviceConfig()
        self.current_device = None

    def _get_output_device_index(self, device_name):
        """Obtém o índice do dispositivo de saída pelo nome"""
        devices = AudioDeviceConfig.list_audio_devices()
        for device in devices['output']:
            if device['name'] == device_name:
                return device['index']
        return None

    def update_output_device(self, device_name):
        """Atualiza o dispositivo de saída em tempo real"""
        log.info(f"AudioStreamManager: Atualizando dispositivo de saída para: {device_name}")
        with self.lock:
            # Obtém o índice do novo dispositivo
            new_device_index = self._get_output_device_index(device_name)
            if new_device_index is None:
                log.error(f"AudioStreamManager: Dispositivo não encontrado: {device_name}")
                return False

            # Se o dispositivo for o mesmo, não faz nada
            if new_device_index == self.current_device:
                return True

            # Fecha o stream atual se existir
            if self.stream is not None:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except Exception as e:
                    log.error(f"AudioStreamManager: Erro ao fechar stream atual: {e}")
                self.stream = None

            # Limpa o buffer antes de trocar o dispositivo
            while not self.buffer.empty():
                try:
                    self.buffer.get_nowait()
                except:
                    pass

            # Tenta abrir o novo stream
            try:
                self.stream = self.p.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True,
                    output_device_index=new_device_index,
                    frames_per_buffer=CHUNK,
                    start=True,
                    stream_callback=self._callback
                )
                self.current_device = new_device_index
                log.info(f"AudioStreamManager: Stream de áudio atualizado com sucesso para o dispositivo: {device_name}")
                return True
            except Exception as e:
                log.error(f"AudioStreamManager: Erro ao abrir stream com novo dispositivo: {e}")
                # Tenta reabrir com o dispositivo padrão
                try:
                    self.stream = self.p.open(
                        format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        output=True,
                        frames_per_buffer=CHUNK,
                        start=True,
                        stream_callback=self._callback
                    )
                    self.current_device = None
                    log.info("AudioStreamManager: Stream de áudio revertido para dispositivo padrão")
                    return False
                except Exception as e2:
                    log.error(f"AudioStreamManager: Erro ao abrir stream com dispositivo padrão: {e2}")
                    return False

    def ensure_stream(self):
        """Garante que o stream está pronto para uso."""
        with self.lock:
            try:
                stream_valid = False
                if self.stream is not None:
                    try:
                        stream_valid = self.stream.is_active()
                    except:
                        stream_valid = False

                if not stream_valid:
                    if self.stream is not None:
                        try:
                            self.stream.stop_stream()
                            self.stream.close()
                        except:
                            pass
                        self.stream = None

                    # Obtém o dispositivo de saída selecionado nas configurações
                    output_device = None
                    try:
                        with open('junin_settings.json', 'r', encoding='utf-8') as f:
                            import json
                            settings = json.load(f)
                            output_device_name = settings.get('output_device')
                            if output_device_name:
                                output_device = self._get_output_device_index(output_device_name)
                                self.current_device = output_device
                    except Exception as e:
                        log.error(f"AudioStreamManager: Erro ao ler configurações de dispositivo: {e}")

                    try:
                        self.stream = self.p.open(
                            format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            output=True,
                            output_device_index=output_device,
                            frames_per_buffer=CHUNK,
                            start=True,
                            stream_callback=self._callback
                        )
                        log.info(f"AudioStreamManager: Stream de áudio iniciado com dispositivo de saída: {output_device}")
                    except Exception as e:
                        log.error(f"AudioStreamManager: Erro ao abrir stream com dispositivo específico: {e}")
                        # Tenta novamente com o dispositivo padrão
                        self.stream = self.p.open(
                            format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            output=True,
                            frames_per_buffer=CHUNK,
                            start=True,
                            stream_callback=self._callback
                        )
                        self.current_device = None
                        log.info("AudioStreamManager: Stream de áudio iniciado com dispositivo padrão")
                return True
            except Exception as e:
                log.error("AudioStreamManager: Erro ao inicializar o stream de áudio: %s", e)
                self.stream = None
                return False

    def _callback(self, in_data, frame_count, time_info, status):
        """Callback para processar o próximo chunk de áudio"""
        try:
            if not self.buffer.empty():
                data = self.buffer.get_nowait()
                return (data, pyaudio.paContinue)
            else:
                return (np.zeros(frame_count, dtype=np.float32).tobytes(), pyaudio.paContinue)
        except:
            return (np.zeros(frame_count, dtype=np.float32).tobytes(), pyaudio.paContinue)

    def play_audio_chunks(self, float_samples, stop_flag=None, on_first_chunk=None):
        """Reproduz chunks de áudio."""
        if not float_samples.size:
            return

        if not self.ensure_stream():
            return

        # Limpa o buffer antes de começar
        while not self.buffer.empty():
            try:
                self.buffer.get_nowait()
            except:
                pass

        first_chunk = True
        for i in range(0, len(float_samples), CHUNK):
            if stop_flag and stop_flag.is_set():
                break
                
            if first_chunk and on_first_chunk:
                on_first_chunk()
                first_chunk = False
            
            chunk = float_samples[i:i + CHUNK]
            if len(chunk) < CHUNK:
                # Aplica fade out no último chunk para evitar cliques
                fade_length = min(len(chunk), CHUNK // 4)
                fade_out = np.linspace(1.0, 0.0, fade_length)
                chunk[-fade_length:] *= fade_out
                chunk = np.pad(chunk, (0, CHUNK - len(chunk)), 'constant')
            
            try:
                # Espera até que haja espaço no buffer
                self.buffer.put(chunk.tobytes(), timeout=1.0)
            except queue.Full:
                log.warning("AudioStreamManager: Buffer de áudio cheio, pulando chunk")
                continue
            except Exception as e:
                log.error("AudioStreamManager: Erro ao reproduzir chunk de áudio: %s", e)
                if not self.ensure_stream():
                    break

        # Adiciona um chunk silencioso no final para suavizar a transição
        silence = np.zeros(CHUNK, dtype=np.float32)
        try:
            self.buffer.put(silence.tobytes(), timeout=1.0)
        except:
            pass

    def cleanup(self):
        """Limpa os recursos de áudio."""
        with self.lock:
            if self.stream is not None:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except:
                    pass
                self.stream = None
        
        # Limpa o buffer
        while not self.buffer.empty():
            try:
                self.buffer.get_nowait()
            except:
                pass

        if self.p:
            self.p.terminate()
