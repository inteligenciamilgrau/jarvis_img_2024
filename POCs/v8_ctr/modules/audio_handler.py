import pyaudio
import wave
import numpy as np
import io
import threading
import time
from collections import deque
from config.theme import AudioConfig
import logging

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
        self.last_recorded_file = None  # Novo atributo para armazenar o último arquivo gravado
        
        # Configura o logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Define os dispositivos padrão
        self.input_device_index = self._get_default_input_device()
        self.output_device_index = self._get_default_output_device()

    def _get_default_input_device(self):
        """Obtém o índice do dispositivo de entrada padrão."""
        try:
            default_device = self.p.get_default_input_device_info()
            self.logger.info(f"Dispositivo de entrada padrão: {default_device['name']}")
            return default_device['index']
        except Exception as e:
            self.logger.error(f"Não foi possível obter o dispositivo de entrada padrão: {e}")
            return None

    def _get_default_output_device(self):
        """Obtém o índice do dispositivo de saída padrão."""
        try:
            default_device = self.p.get_default_output_device_info()
            self.logger.info(f"Dispositivo de saída padrão: {default_device['name']}")
            return default_device['index']
        except Exception as e:
            self.logger.error(f"Não foi possível obter o dispositivo de saída padrão: {e}")
            return None

    @staticmethod
    def _clean_device_name(name):
        """Limpa e padroniza os nomes dos dispositivos para evitar duplicatas."""
        # Sufixos e padrões comuns para remover
        patterns_to_remove = [
            " (AMD High Definition Audio Device)",
        ]
        
        # Remove todos os padrões especificados
        for pattern in patterns_to_remove:
            name = name.replace(pattern, "")
        
        # Remove quaisquer números entre parênteses no final
        import re
        name = re.sub(r'\s*\(\d+[\-\)]\s*', '', name)
        name = re.sub(r'\s*\(\d+\)\s*$', '', name)
        
        # Remove vários espaços
        name = ' '.join(name.split())
        
        return name.strip()

    @classmethod
    def list_audio_devices(cls):
        """Lista todos os dispositivos de entrada e saída de áudio disponíveis com filtragem de duplicatas."""
        p = pyaudio.PyAudio()
        devices = {
            'input': [],
            'output': []
        }
        
        # Rastrear dispositivos por seus nomes limpos para evitar duplicatas
        seen_devices = {}
        
        for i in range(p.get_device_count()):
            try:
                device_info = p.get_device_info_by_index(i)
                clean_name = cls._clean_device_name(device_info['name'])
                
                # Cria uma entrada de dispositivo com nome limpo e índice original
                device_entry = {
                    'index': device_info['index'],
                    'name': clean_name,
                    'channels': {
                        'input': device_info['maxInputChannels'],
                        'output': device_info['maxOutputChannels']
                    }
                }
                
                # Lidar com dispositivos de entrada
                if device_info['maxInputChannels'] > 0:
                    if clean_name not in seen_devices.get('input', set()):
                        devices['input'].append(device_entry)
                        if 'input' not in seen_devices:
                            seen_devices['input'] = set()
                        seen_devices['input'].add(clean_name)
                
                # Lidar com dispositivos de saída
                if device_info['maxOutputChannels'] > 0:
                    if clean_name not in seen_devices.get('output', set()):
                        devices['output'].append(device_entry)
                        if 'output' not in seen_devices:
                            seen_devices['output'] = set()
                        seen_devices['output'].add(clean_name)
                
            except Exception as e:
                logging.error(f"Erro ao processar o dispositivo {i}: {e}")
                continue
        
        p.terminate()
        return devices

    def set_input_device(self, device_index):
        """Define o dispositivo de áudio de entrada."""
        try:
            # Verifica se o dispositivo existe e suporta entrada
            device_info = self.p.get_device_info_by_index(int(device_index))
            if device_info['maxInputChannels'] > 0:
                self.input_device_index = int(device_index)
                self.logger.info(f"Dispositivo de entrada definido como: {device_info['name']} (índice: {device_index})")
            else:
                raise ValueError(f"O dispositivo {device_index} não suporta entrada")
        except Exception as e:
            self.logger.error(f"Erro ao definir o dispositivo de entrada: {e}")
            # Reverte para o dispositivo padrão
            self.input_device_index = self._get_default_input_device()

    def set_output_device(self, device_index):
        """Define o dispositivo de áudio de saída."""
        try:
            # Verifica se o dispositivo existe e suporta saída
            device_info = self.p.get_device_info_by_index(int(device_index))
            if device_info['maxOutputChannels'] > 0:
                self.output_device_index = int(device_index)
                self.logger.info(f"Dispositivo de saída definido como: {device_info['name']} (índice: {device_index})")
                
                # Fecha o fluxo existente, se houver
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()
                
                # Cria um novo fluxo com o dispositivo selecionado
                self.stream = self.p.open(
                    format=AudioConfig.FORMAT,
                    channels=AudioConfig.CHANNELS,
                    rate=AudioConfig.RATE,
                    output=True,
                    output_device_index=self.output_device_index,
                    frames_per_buffer=AudioConfig.CHUNK
                )
            else:
                raise ValueError(f"O dispositivo {device_index} não suporta saída")
        except Exception as e:
            self.logger.error(f"Erro ao definir o dispositivo de saída: {e}")
            # Reverte para o dispositivo padrão
            self.output_device_index = self._get_default_output_device()

    def calibrate_noise_threshold(self):
        """Calibra o ruído ambiente e define o limite."""
        print("Calibrando o som ambiente. Por favor, permaneça em silêncio durante a calibração...")

        # Usa o dispositivo de entrada padrão se nenhum dispositivo for selecionado
        input_device = self.input_device_index or self._get_default_input_device()

        stream = self.p.open(
            format=AudioConfig.FORMAT,
            channels=AudioConfig.CHANNELS,
            rate=AudioConfig.RATE,
            input=True,
            input_device_index=input_device,
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
        print(f"Calibração concluída. Limite de som ambiente: {self.threshold:.2f}")
        return self.threshold

    def start_recording(self):
        """Inicia a gravação de áudio com seleção robusta de dispositivo."""
        self.frames = []
        
        try:
            # Se nenhum dispositivo de entrada estiver definido, use o padrão do sistema
            if self.input_device_index is None:
                self.input_device_index = self._get_default_input_device()
            
            # Valida o índice do dispositivo
            device_info = self.p.get_device_info_by_index(self.input_device_index)
            
            # Garante que o dispositivo suporta entrada
            if device_info['maxInputChannels'] == 0:
                raise ValueError(f"O dispositivo {device_info['name']} não suporta entrada")
            
            self.logger.info(f"Usando o dispositivo de entrada: {device_info['name']} (Índice: {self.input_device_index})")
            
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
            self.logger.error(f"Erro ao iniciar a gravação: {e}")
            
            # Tenta os dispositivos padrão do sistema
            try:
                default_input_device = self._get_default_input_device()
                
                if default_input_device is not None:
                    self.logger.warning("Tentando usar o dispositivo de entrada padrão do sistema")
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
                    self.logger.error("Nenhum dispositivo de entrada válido encontrado")
                    raise
            
            except Exception as fallback_error:
                self.logger.critical(f"Falha ao iniciar a gravação: {fallback_error}")
                raise

    def record(self):
        """Grava dados de áudio."""
        self.please_interrupt = True
        while self.is_recording:
            data = self.audio_stream.read(AudioConfig.CHUNK)
            self.frames.append(data)

        self.audio_stream.stop_stream()
        self.audio_stream.close()
        self.please_interrupt = False

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
        # Usa o dispositivo de entrada padrão se nenhum dispositivo for selecionado
        input_device = self.input_device_index or self._get_default_input_device()

        stream = self.p.open(
            format=AudioConfig.FORMAT,
            channels=AudioConfig.CHANNELS,
            rate=AudioConfig.RATE,
            input=True,
            input_device_index=input_device,
            frames_per_buffer=AudioConfig.CHUNK
        )

        last_detection_time = None
        continuous_detection_start_time = None
        is_vad_active = False

        while self.is_recording_vad and not self.stop_event.is_set():
            if self.fechando:
                break

            data = np.frombuffer(stream.read(AudioConfig.CHUNK), dtype=np.int16)
            volume = np.linalg.norm(data)

            if volume < AudioConfig.NOISE_FLOOR:
                volume = 0
            
            if volume > self.threshold:
                if continuous_detection_start_time is None:
                    continuous_detection_start_time = time.time()
                else:
                    elapsed_detection_time = time.time() - continuous_detection_start_time
                    if elapsed_detection_time >= AudioConfig.DETECTION_TIME:
                        if not is_vad_active:
                            print("Som detectado! Gravando...")
                            
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
                    print("Som finalizado. Aguardando...")
                    self.is_recording = False
                    is_vad_active = False

        stream.stop_stream()
        stream.close()

    def stop_recording(self):
        """Para a gravação de áudio."""
        self.is_recording = False
        self.stop_event.set()

    def cleanup(self):
        """Limpa os recursos."""
        self.fechando = True
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

    def get_last_recorded_file(self):
        """Retorna o último arquivo de áudio gravado."""
        return self.last_recorded_file
