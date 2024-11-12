import tkinter as tk
from config.theme import DarkTheme
from ui.components import ModernFrame, ModernOptionMenu
from modules.audio_handler import AudioHandler

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

        input_devices = AudioHandler.list_audio_devices()['input']
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

        output_devices = AudioHandler.list_audio_devices()['output']
        output_device_names = [device['name'] for device in output_devices]
        
        output_device_dropdown = ModernOptionMenu(
            output_device_frame,
            self.vars['output_device'],
            *output_device_names
        )
        output_device_dropdown.pack(side='left', padx=5)

        return input_device_dropdown, output_device_dropdown


class SettingsManager:
    def __init__(self, settings_file):
        self.settings_file = settings_file
        self.settings = self.load_settings()

    def load_settings(self):
        """Carrega as configurações do arquivo."""
        try:
            with open(self.settings_file, 'r') as f:
                import json
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_settings(self, settings):
        """Salva as configurações no arquivo."""
        with open(self.settings_file, 'w') as f:
            import json
            json.dump(settings, f, indent=4)

    def get_setting(self, key, default=None):
        """Obtém uma configuração específica."""
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        """Define uma configuração específica."""
        self.settings[key] = value
        self.save_settings(self.settings)

    def save_window_geometry(self, geometry):
        """Salva a geometria da janela nas configurações."""
        self.set_setting('window_geometry', geometry)

    def get_window_geometry(self):
        """Obtém a geometria da janela salva."""
        return self.get_setting('window_geometry', '800x1000+100+100')
