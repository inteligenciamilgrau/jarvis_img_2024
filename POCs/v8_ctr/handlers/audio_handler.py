import pyaudio
import wave
import numpy as np
import io
import threading
import time
from collections import deque
import logging
from config.audio_config import AudioConfig, AudioDeviceConfig  # Atualizado para incluir AudioDeviceConfig

# Configurações de logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class AudioHandler:
    def __init__(self, on_recording_complete=None):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.is_recording_vad = False
        self.stop_event = threading.Event()
        self.threshold = 200
        self.please_interrupt = False
        self.fechando = False
        self.on_recording_complete = on_recording_complete
        self.last_recorded_file = None
        self.vad_thread = None
        self.stream_lock = threading.Lock()
        
        # Inicializa o gerenciador de dispositivos
        self.device_config = AudioDeviceConfig()
        
        # Define os dispositivos padrão
        self.input_device_index = self.device_config._get_default_input_device()
        self.output_device_index = self.device_config._get_default_output_device()
        
        # Armazena os nomes dos dispositivos atuais
        self.current_input_device = None
        self.current_output_device = None
        
        # Inicializa o stream de saída
        self._initialize_output_stream()

    def _initialize_output_stream(self):
        """Inicializa o stream de saída com tratamento de erros."""
        try:
            with self.stream_lock:
                if self.stream is not None:
                    try:
                        self.stream.stop_stream()
                        self.stream.close()
                    except Exception as e:
                        log.error("Erro ao fechar stream existente: %s", e)

                # Obtém informações do dispositivo
                device_info = self.p.get_device_info_by_index(self.output_device_index) if self.output_device_index is not None else None
                device_name = device_info['name'] if device_info else "dispositivo padrão"
                
                log.info("Inicializando stream de saída com dispositivo: %s (índice: %s)", 
                        device_name, 
                        self.output_device_index if self.output_device_index is not None else "padrão")

                self.stream = self.p.open(
                    format=AudioConfig.FORMAT,
                    channels=AudioConfig.CHANNELS,
                    rate=AudioConfig.RATE,
                    output=True,
                    output_device_index=self.output_device_index,
                    frames_per_buffer=AudioConfig.CHUNK
                )
                log.info("Stream de saída inicializado com sucesso usando %s", device_name)
                self.current_output_device = device_name
        except Exception as e:
            log.error("Erro ao inicializar stream de saída: %s. Tentando dispositivo padrão...", e)
            try:
                # Tenta usar o dispositivo padrão
                self.output_device_index = None
                self.stream = self.p.open(
                    format=AudioConfig.FORMAT,
                    channels=AudioConfig.CHANNELS,
                    rate=AudioConfig.RATE,
                    output=True,
                    frames_per_buffer=AudioConfig.CHUNK
                )
                log.info("Stream de saída inicializado com dispositivo padrão")
                self.current_output_device = "dispositivo padrão"
            except Exception as e2:
                log.error("Erro ao inicializar stream de saída com dispositivo padrão: %s", e2)
                self.stream = None

    def set_input_device(self, device_index):
        """Define o dispositivo de entrada e atualiza o estado."""
        try:
            # Verifica se o dispositivo existe e suporta entrada
            device_info = self.p.get_device_info_by_index(device_index)
            if device_info['maxInputChannels'] > 0:
                # Verifica se o dispositivo realmente mudou
                if device_index == self.input_device_index:
                    log.info("Dispositivo de entrada já está selecionado: %s", device_info['name'])
                    return True

                log.info("Alterando dispositivo de entrada para: %s (índice: %d)", device_info['name'], device_index)
                self.input_device_index = device_index
                self.current_input_device = device_info['name']
                return True
            else:
                log.error("O dispositivo %s não suporta entrada", device_info['name'])
                return False
        except Exception as e:
            log.error("Erro ao definir dispositivo de entrada: %s", e)
            return False

    def set_output_device(self, device_index):
        """Define o dispositivo de saída e reinicializa o stream."""
        try:
            # Verifica se o dispositivo existe e suporta saída
            device_info = self.p.get_device_info_by_index(device_index)
            if device_info['maxOutputChannels'] > 0:
                # Verifica se o dispositivo realmente mudou
                if device_index == self.output_device_index:
                    log.info("Dispositivo de saída já está selecionado: %s", device_info['name'])
                    return True

                log.info("Alterando dispositivo de saída para: %s (índice: %d)", device_info['name'], device_index)
                self.output_device_index = device_index
                self._initialize_output_stream()
                return True
            else:
                log.error("O dispositivo %s não suporta saída", device_info['name'])
                return False
        except Exception as e:
            log.error("Erro ao definir dispositivo de saída: %s", e)
            return False

    def calibrate_noise_threshold(self):
        """Calibra o ruído ambiente e define o limite."""        
        log.info("Calibrando o som ambiente. Por favor, permaneça em silêncio durante a calibração...")

        try:
            # Abre um stream temporário para calibração
            stream = self.p.open(
                format=AudioConfig.FORMAT,
                channels=AudioConfig.CHANNELS,
                rate=AudioConfig.RATE,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=AudioConfig.CHUNK
            )

            volume_history = deque(maxlen=AudioConfig.MOVING_AVERAGE_WINDOW)

            for _ in range(AudioConfig.MOVING_AVERAGE_WINDOW):
                data = np.frombuffer(stream.read(AudioConfig.CHUNK), dtype=np.int16)
                volume = np.linalg.norm(data)
                if volume < AudioConfig.NOISE_FLOOR:
                    volume = 0
                volume_history.append(volume)
            
            stream.stop_stream()
            stream.close()
            
            average_volume = np.mean(volume_history)
            self.threshold = average_volume * AudioConfig.VOLUME_MULTIPLIER
            log.info("Calibração concluída. Limite de som ambiente: %.2f", self.threshold)
            return self.threshold

        except Exception as e:
            log.error("Erro durante a calibração: %s", e)
            return 200  # valor padrão

    def start_recording(self):
        """Inicia a gravação de áudio com seleção robusta de dispositivo."""        
        self.frames = []
        
        try:
            # Valida o índice do dispositivo
            device_info = self.p.get_device_info_by_index(self.input_device_index)
            
            # Garante que o dispositivo suporta entrada
            if device_info['maxInputChannels'] == 0:
                raise ValueError(f"O dispositivo {device_info['name']} não suporta entrada")
            
            log.info("Usando o dispositivo de entrada: %s (Índice: %d)", device_info['name'], self.input_device_index)
            
            # Abre o fluxo de áudio
            self.audio_stream = self.p.open(
                format=AudioConfig.FORMAT,
                channels=AudioConfig.CHANNELS,
                rate=AudioConfig.RATE,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=AudioConfig.CHUNK
            )
            
            # Inicia a thread de gravação
            self.recording_thread = threading.Thread(target=self.record)
            self.recording_thread.start()
        
        except Exception as e:
            log.error("Erro ao iniciar a gravação: %s", e)
            
            # Tenta os dispositivos padrão do sistema
            try:
                default_input_device = self.device_config._get_default_input_device()
                
                if default_input_device is not None:
                    log.warning("Tentando usar o dispositivo de entrada padrão do sistema")
                    self.input_device_index = default_input_device
                    
                    # Tenta novamente com o dispositivo padrão
                    self.audio_stream = self.p.open(
                        format=AudioConfig.FORMAT,
                        channels=AudioConfig.CHANNELS,
                        rate=AudioConfig.RATE,
                        input=True,
                        input_device_index=self.input_device_index,
                        frames_per_buffer=AudioConfig.CHUNK
                    )
                    
                    # Inicia a thread de gravação
                    self.recording_thread = threading.Thread(target=self.record)
                    self.recording_thread.start()
                else:
                    log.error("Nenhum dispositivo de entrada válido encontrado")
                    raise
            
            except Exception as fallback_error:
                log.critical("Falha ao iniciar a gravação: %s", fallback_error)
                raise

    def record(self):
        """Grava dados de áudio."""        
        self.please_interrupt = True
        self.is_recording = True  # Certifique-se de que a gravação está ativada
        log.info("Iniciando gravação...")
        while self.is_recording:
            data = self.audio_stream.read(AudioConfig.CHUNK)
            self.frames.append(data)

        self.audio_stream.stop_stream()
        self.audio_stream.close()
        self.please_interrupt = False
        log.info("Gravação finalizada.")

        if self.frames and self.on_recording_complete:
            audio_data = b''.join(self.frames)
            audio_file = io.BytesIO()
            with wave.open(audio_file, 'wb') as wf:
                wf.setnchannels(AudioConfig.CHANNELS)
                wf.setsampwidth(self.p.get_sample_size(AudioConfig.FORMAT))
                wf.setframerate(AudioConfig.RATE)
                wf.writeframes(audio_data)
            audio_file.name = "output.wav"
            self.last_recorded_file = audio_file  # Atualiza o último arquivo gravado
            self.on_recording_complete(audio_file)

    def vad_recording(self):
        """Gravação de detecção de atividade de voz."""        
        try:
            stream = self.p.open(
                format=AudioConfig.FORMAT,
                channels=AudioConfig.CHANNELS,
                rate=AudioConfig.RATE,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=AudioConfig.CHUNK
            )

            last_detection_time = None
            continuous_detection_start_time = None
            is_vad_active = False

            log.info("Iniciando gravação VAD...")
            while self.is_recording_vad and not self.stop_event.is_set():
                if self.fechando:
                    break

                data = np.frombuffer(stream.read(AudioConfig.CHUNK), dtype=np.int16)
                volume = np.linalg.norm(data)

                if volume < AudioConfig.NOISE_FLOOR:
                    volume = 0
                
                log.debug("Volume detectado: %.2f, Limite: %.2f", volume, self.threshold)

                if volume > self.threshold:
                    if continuous_detection_start_time is None:
                        continuous_detection_start_time = time.time()
                    else:
                        elapsed_detection_time = time.time() - continuous_detection_start_time
                        if elapsed_detection_time >= AudioConfig.DETECTION_TIME:
                            if not is_vad_active:
                                log.info("Som detectado! Gravando...")
                                
                                if self.please_interrupt:
                                    self.interromper = True
                                self.is_recording = True
                                
                                self.start_recording()
                                is_vad_active = True
                            last_detection_time = time.time()
                else:
                    continuous_detection_start_time = None
                
                if last_detection_time:
                    elapsed_time = time.time() - last_detection_time
                    if elapsed_time > AudioConfig.RECORD_TIME_AFTER_DETECTION and is_vad_active:
                        log.info("Som finalizado. Aguardando...")
                        self.is_recording = False
                        is_vad_active = False

        except Exception as e:
            log.error("Erro durante gravação VAD: %s", e)
        finally:
            stream.stop_stream()
            stream.close()
            self.is_recording_vad = False
            self.is_recording = False
            log.info("Gravação VAD finalizada.")

    def stop_recording(self):
        """Para a gravação de áudio."""        
        self.is_recording = False
        self.stop_event.set()
        if self.is_recording_vad:
            self.is_recording_vad = False
            if hasattr(self, 'audio_stream'):
                try:
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                except Exception as e:
                    log.error("Erro ao fechar o stream de áudio: %s", e)

    def cleanup(self):
        """Limpa os recursos."""        
        self.fechando = True
        self.stop_event.set()
        self.is_recording_vad = False
        self.is_recording = False
        
        with self.stream_lock:
            if self.stream:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except Exception as e:
                    log.error("Erro ao fechar stream de saída: %s", e)
        
        try:
            self.p.terminate()
        except Exception as e:
            log.error("Erro ao terminar PyAudio: %s", e)

    def get_last_recorded_file(self):
        """Retorna o último arquivo de áudio gravado."""        
        return self.last_recorded_file
