import tkinter as tk
import keyboard
from dotenv import load_dotenv

from modules.audio_handler import AudioHandler
from modules.speech_handler import SpeechHandler
from modules.chat_handler import ChatHandler
from modules.computer_control import AnthropicToolHandler
from modules.task_manager import TaskManager
from ui.app_layout import AppLayout
from ui.settings_manager import SettingsManager
from ui.event_handlers import EventHandlers

class JuninApp:
    def __init__(self, root):
        # Carrega as variáveis de ambiente
        load_dotenv()
        
        self.root = root
        
        # Inicializa as configurações primeiro
        self.initialize_settings()
        
        # Inicializa as variáveis em seguida
        self.initialize_variables()
        
        # Inicializa os handlers
        self.initialize_handlers()
        
        # Cria callbacks vazios iniciais
        self.callbacks = {
            'send_message': None,
            'new_line': None,
            'toggle_recording': None,
            'update_language': None,
            'toggle_always_on_top': None,
            'update_voice_dropdown': None,
            'vad_checkbox': None,
            'spelling_correction': None,
        }
        
        # Inicializa os componentes da UI
        self.initialize_ui()
        
        # Configura as teclas de atalho
        self.setup_hotkeys()

    def initialize_settings(self):
        """Inicializa o gerenciador de configurações.""" 
        self.settings_manager = SettingsManager("junin_settings.json")

    def initialize_variables(self):
        """Inicializa todas as variáveis tkinter.""" 
        self.vars = {
            'language': tk.StringVar(value=self.settings_manager.get_setting("selected_language", "English")),
            'api_selection': tk.StringVar(value=self.settings_manager.get_setting("selected_api", "OpenAI")),
            'always_on_top': tk.BooleanVar(value=self.settings_manager.get_setting("always_on_top", True)),
            'hear_response': tk.BooleanVar(value=self.settings_manager.get_setting("hear_response", False)),
            'vad_enabled': tk.BooleanVar(value=self.settings_manager.get_setting("vad_enabled", False)),
            'voice_engine': tk.StringVar(value=self.settings_manager.get_setting("selected_voice_engine", "tts-1")),
            'voice': tk.StringVar(value=self.settings_manager.get_setting("selected_voice", "alloy")),
            'voice_speed': tk.StringVar(value=str(self.settings_manager.get_setting("voice_speed", "1.5"))),
            'whisper': tk.StringVar(value=self.settings_manager.get_setting("selected_whisper", "Online")),
            'chatgpt_model': tk.StringVar(value=self.settings_manager.get_setting("selected_model", "gpt-4-mini")),
            'spelling_correction': tk.StringVar(value="None"),
            # Configurações do monitor
            'monitor_index': tk.IntVar(value=self.settings_manager.get_setting("monitor_index", 1)),
            'monitor_offset_x': tk.StringVar(value=str(self.settings_manager.get_setting("monitor_offset", [0, 0])[0])),
            'monitor_offset_y': tk.StringVar(value=str(self.settings_manager.get_setting("monitor_offset", [0, 0])[1])),
            'computer_speech': tk.BooleanVar(value=self.settings_manager.get_setting("computer_speech", False))
        }

        # Variáveis do dispositivo de áudio
        audio_devices = AudioHandler.list_audio_devices()
        default_input = audio_devices['input'][0]['name'] if audio_devices['input'] else ""
        default_output = audio_devices['output'][0]['name'] if audio_devices['output'] else ""
        
        self.vars.update({
            'input_device': tk.StringVar(value=self.settings_manager.get_setting("input_device", default_input)),
            'output_device': tk.StringVar(value=self.settings_manager.get_setting("output_device", default_output)),
        })

    def initialize_handlers(self):
        """Inicializa todos os handlers necessários.""" 
        # Handlers principais
        self.handlers = {
            'audio': AudioHandler(on_recording_complete=self.handle_recording_complete),
            'speech': SpeechHandler(voice_speed_var=self.vars['voice_speed']),
            'chat': ChatHandler(),
            'task': TaskManager(),
            'computer': AnthropicToolHandler(
                monitor_index=self.settings_manager.get_setting("monitor_index", 1),
                monitor_offset=self.settings_manager.get_setting("monitor_offset", [0, 0]),
                falar=self.settings_manager.get_setting("computer_speech", False)
            ),
            'settings': self.settings_manager  # Adiciona o settings_manager aos handlers
        }

    def initialize_ui(self):
        """Inicializa todos os componentes da UI.""" 
        # Inicializa os manipuladores de eventos com componentes vazios primeiro
        self.event_handlers = EventHandlers(
            {},  # Dicionário de componentes vazio por enquanto
            self.handlers,
            self.vars,
            self.settings_manager
        )

        # Atualiza os callbacks com os métodos reais dos manipuladores de eventos
        self.callbacks.update({
            'send_message': self.event_handlers.send_message,
            'new_line': self.event_handlers.new_line,
            'toggle_recording': self.event_handlers.toggle_recording,
            'update_language': self.event_handlers.update_language,
            'toggle_always_on_top': self.event_handlers.toggle_always_on_top,
            'update_voice_dropdown': self.event_handlers.update_voice_dropdown,
            'vad_checkbox': self.event_handlers.vad_checkbox_callback,
            'spelling_correction': self.event_handlers.handle_spelling_correction,
        })

        # Inicializa o layout com os callbacks atualizados
        self.app_layout = AppLayout(self.root, self.handlers, self.vars, self.callbacks)
        
        # Configura a janela e os componentes da UI
        self.app_layout.setup_window()
        
        # Inicializa o dicionário de componentes
        chat_display, record_button = self.app_layout.setup_chat_area()
        self.components = {
            'root': self.root,
            'chat_display': chat_display,
            'record_button': record_button,
        }
        
        # Configura a área de entrada
        user_input, _ = self.app_layout.setup_input_area()
        self.components['user_input'] = user_input
        
        # Configura o painel de controle e armazena o menu suspenso de voz
        voice_dropdown = self.app_layout.setup_control_panel()
        self.components['voice_dropdown'] = voice_dropdown

        # Atualiza os manipuladores de eventos com os componentes completos
        self.event_handlers.components = self.components
        
        # Vincula os eventos de seleção de dispositivo
        self.vars['input_device'].trace('w', self.event_handlers.on_input_device_select)
        self.vars['output_device'].trace('w', self.event_handlers.on_output_device_select)
        self.vars['chatgpt_model'].trace('w', self.event_handlers.on_model_select)
        
        # Vincula os eventos de configurações do monitor
        self.vars['monitor_index'].trace('w', self.event_handlers.on_monitor_settings_change)
        self.vars['monitor_offset_x'].trace('w', self.event_handlers.on_monitor_settings_change)
        self.vars['monitor_offset_y'].trace('w', self.event_handlers.on_monitor_settings_change)
        self.vars['computer_speech'].trace('w', self.event_handlers.on_computer_speech_change)

        # Aplica o estado inicial da janela
        self.root.attributes('-topmost', self.vars['always_on_top'].get())

    def setup_hotkeys(self):
        """Configura teclas de atalho globais.""" 
        keyboard.add_hotkey('ctrl+alt', self.event_handlers.toggle_recording)

    def handle_recording_complete(self, audio_file):
        """Wrapper para o handler de gravação completa.""" 
        self.event_handlers.handle_recording_complete(audio_file)

    def save_settings(self):
        """Salva todas as configurações atuais.""" 
        try:
            x_offset = int(self.vars['monitor_offset_x'].get())
            y_offset = int(self.vars['monitor_offset_y'].get())
        except ValueError:
            x_offset, y_offset = 0, 0

        settings = {
            "selected_voice": self.vars['voice'].get(),
            "voice_speed": self.vars['voice_speed'].get(),
            "always_on_top": self.vars['always_on_top'].get(),
            "selected_language": self.vars['language'].get(),
            "hear_response": self.vars['hear_response'].get(),
            "selected_voice_engine": self.vars['voice_engine'].get(),
            "selected_whisper": self.vars['whisper'].get(),
            "selected_api": self.vars['api_selection'].get(),
            "vad_enabled": self.vars['vad_enabled'].get(),
            "input_device": self.vars['input_device'].get(),
            "output_device": self.vars['output_device'].get(),
            "selected_model": self.vars['chatgpt_model'].get(),
            # Configurações do monitor
            "monitor_index": self.vars['monitor_index'].get(),
            "monitor_offset": [x_offset, y_offset],
            "computer_speech": self.vars['computer_speech'].get(),
            # Salva a geometria da janela
            "window_geometry": self.root.geometry()
        }
        self.settings_manager.save_settings(settings)

    def cleanup(self):
        """Limpa os recursos antes de fechar.""" 
        try:
            keyboard.unhook_all_hotkeys()
            self.handlers['audio'].cleanup()
            self.handlers['speech'].cleanup()
            if self.handlers['computer'].falar and self.handlers['computer'].tts:
                self.handlers['computer'].tts.cleanup()
            self.save_settings()
        except Exception as e:
            print(f"Erro durante a limpeza: {e}")
        finally:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = JuninApp(root)
    root.protocol("WM_DELETE_WINDOW", app.cleanup)
    root.mainloop()
