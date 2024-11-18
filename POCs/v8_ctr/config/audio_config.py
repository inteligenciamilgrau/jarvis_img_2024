import tkinter as tk
import pyaudio
import logging
from ui.theme import DarkTheme
from ui.components import ModernFrame, ModernOptionMenu

class AudioConfig:
    CHUNK = 1024
    FORMAT = 8  # pyaudio.paInt32
    CHANNELS = 1
    RATE = 24000  # Ajustado para 24000Hz para compatibilidade com GPT-4
    MOVING_AVERAGE_WINDOW = 50
    VOLUME_MULTIPLIER = 3
    NOISE_FLOOR = 100
    RECORD_TIME_AFTER_DETECTION = 2.0
    DETECTION_TIME = 0.2


class AudioDeviceManager:
    def __init__(self, root, variables, callbacks):
        self.root = root
        self.vars = variables
        self.callbacks = callbacks
        
    def setup_audio_device_selection(self):
        """Configura a seção de seleção do dispositivo de áudio.""" 
        audio_devices_frame = ModernFrame(self.root)
        audio_devices_frame.pack(pady=5, padx=10, fill='x')

        # Seleção do Dispositivo de Entrada
        input_device_label = tk.Label(
            audio_devices_frame, 
            text="Dispositivo de Entrada:", 
            bg=DarkTheme.BG_SECONDARY, 
            fg=DarkTheme.TEXT_PRIMARY
        )
        input_device_label.pack(side='left', padx=5)

        input_devices = AudioDeviceConfig.list_audio_devices()['input']
        input_device_names = [device['name'] for device in input_devices]
        
        input_device_dropdown = ModernOptionMenu(
            audio_devices_frame,
            self.vars['input_device'],
            *input_device_names
        )
        input_device_dropdown.pack(side='left', padx=5)

        # Seleção do Dispositivo de Saída
        output_device_frame = ModernFrame(self.root)
        output_device_frame.pack(pady=5, padx=10, fill='x')

        output_device_label = tk.Label(
            output_device_frame, 
            text="Dispositivo de Saída:", 
            bg=DarkTheme.BG_SECONDARY, 
            fg=DarkTheme.TEXT_PRIMARY
        )
        output_device_label.pack(side='left', padx=5)

        output_devices = AudioDeviceConfig.list_audio_devices()['output']
        output_device_names = [device['name'] for device in output_devices]
        
        output_device_dropdown = ModernOptionMenu(
            output_device_frame,
            self.vars['output_device'],
            *output_device_names
        )
        output_device_dropdown.pack(side='left', padx=5)

        return input_device_dropdown, output_device_dropdown


class AudioDeviceConfig:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.logger = logging.getLogger(__name__)

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
                clean_name = device_info['name']
                
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
                return self.input_device_index
            else:
                raise ValueError(f"O dispositivo {device_index} não suporta entrada")
        except Exception as e:
            self.logger.error(f"Erro ao definir o dispositivo de entrada: {e}")
            # Reverte para o dispositivo padrão
            return self._get_default_input_device()

    def set_output_device(self, device_index):
        """Define o dispositivo de áudio de saída."""        
        try:
            # Verifica se o dispositivo existe e suporta saída
            device_info = self.p.get_device_info_by_index(int(device_index))
            if device_info['maxOutputChannels'] > 0:
                self.output_device_index = int(device_index)
                self.logger.info(f"Dispositivo de saída definido como: {device_info['name']} (índice: {device_index})")
                return self.output_device_index
            else:
                raise ValueError(f"O dispositivo {device_index} não suporta saída")
        except Exception as e:
            self.logger.error(f"Erro ao definir o dispositivo de saída: {e}")
            # Reverte para o dispositivo padrão
            return self._get_default_output_device()

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
