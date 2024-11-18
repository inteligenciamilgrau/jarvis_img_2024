import tkinter as tk
from PIL import Image, ImageTk
import os
import logging
from ui.theme import DarkTheme
from ui.components import (
    ModernButton, ModernFrame, ModernCheckbutton, 
    ModernOptionMenu, ChatDisplay, ChatGPTModelSelector
)
from config.audio_config import AudioDeviceConfig
from config.log_config import LogConfig

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class AppLayout:
    def __init__(self, root, handlers, variables, callbacks):
        self.root = root
        self.handlers = handlers
        self.vars = variables
        self.callbacks = callbacks
        self.sidebar_visible = True
        
        self.log_config = LogConfig.get_instance()
        
        self.default_callbacks = {
            'send_message': self._default_send_message,
            'new_line': self._default_new_line,
            'toggle_recording': self._default_toggle_recording,
            'update_language': self._default_update_language,
            'toggle_always_on_top': self._default_toggle_always_on_top,
            'update_voice_dropdown': self._default_update_voice_dropdown,
            'vad_checkbox': self._default_vad_checkbox,
            'toggle_logs': self._toggle_logs,
        }
        
        self.callbacks = {**self.default_callbacks, **self.callbacks}
        self.root.bind("<Configure>", self._save_window_position)
        
    def _default_send_message(self, event=None):
        log.info("send_message padrão chamado")
        return "break"
    
    def _default_new_line(self, event=None):
        log.info("new_line padrão chamado")
        return "break"
    
    def _default_toggle_recording(self, event=None):
        log.info("toggle_recording padrão chamado")
    
    def _default_update_language(self, selected_language):
        log.info(f"update_language padrão chamado com {selected_language}")
    
    def _default_toggle_always_on_top(self):
        log.info("toggle_always_on_top padrão chamado")
    
    def _default_update_voice_dropdown(self, selected_engine):
        log.info(f"update_voice_dropdown padrão chamado com {selected_engine}")
    
    def _default_vad_checkbox(self):
        log.info("vad_checkbox padrão chamado")

    def _toggle_logs(self):
        show_logs = self.vars['show_logs'].get()
        self.log_config.set_log_visibility(show_logs)
        log.info(f"Visibilidade dos logs alterada para: {show_logs}")

    def _save_window_position(self, event=None):
        if event.widget != self.root:
            return
        geometry = self.root.geometry()
        if hasattr(self.handlers, 'settings'):
            self.handlers.settings.save_window_geometry(geometry)
        
    def setup_window(self):
        self.root.title("J.U.N.I.N. Release v1.0.0")
        self.root.configure(bg=DarkTheme.BG_PRIMARY)
        
        if hasattr(self.handlers, 'settings'):
            geometry = self.handlers.settings.get_window_geometry()
            if geometry:
                self.root.geometry(geometry)
            else:
                self.root.geometry("1100x700+560+100")
        else:
            self.root.geometry("1100x700+560+100")
        
        self.main_container = tk.Frame(self.root, bg=DarkTheme.BG_PRIMARY)
        self.main_container.pack(fill='both', expand=True)
        
        self.content_frame = tk.Frame(self.main_container, bg=DarkTheme.BG_PRIMARY)
        self.content_frame.pack(side='left', fill='both', expand=True)
        
        self.sidebar_frame = ModernFrame(self.main_container)
        self.sidebar_frame.pack(side='right', fill='y', padx=5)
        
    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar_frame.pack_forget()
        else:
            self.sidebar_frame.pack(side='right', fill='y', padx=5)
        self.sidebar_visible = not self.sidebar_visible

    def setup_chat_area(self):
        chat_container = ModernFrame(self.content_frame)
        chat_container.pack(padx=20, fill='both', expand=True)
        
        chat_header = ModernFrame(chat_container)
        chat_header.pack(fill='x', pady=(0, 5))
        
        title_container = tk.Frame(chat_header, bg=DarkTheme.BG_SECONDARY)
        title_container.pack(fill='x', expand=True)
        
        header_label = tk.Label(
            title_container,
            text="J.U.N.I.N Chat",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY,
            font=('Arial', 12, 'bold')
        )
        header_label.pack(expand=True)

        toggle_button = ModernButton(
            chat_header,
            text="☰",
            command=self.toggle_sidebar,
            width=2
        )
        toggle_button.place(relx=1.0, rely=0.5, anchor='e', x=-5)

        self.chat_display = ChatDisplay(
            chat_container,
            height=15,
            width=50
        )
        self.chat_display.pack(fill='both', expand=True, pady=(0, 5))

        record_button = ModernButton(
            chat_container,
            text="Clique para Gravar",
            command=self.callbacks['toggle_recording']
        )
        record_button.pack()
        
        return self.chat_display, record_button

    def setup_input_area(self):
        input_frame = ModernFrame(self.content_frame)
        input_frame.pack(pady=(10, 10), padx=20, fill='x')

        label_container = tk.Frame(input_frame, bg=DarkTheme.BG_SECONDARY)
        label_container.pack(fill='x')
        
        input_label = tk.Label(
            label_container,
            text="Digite sua mensagem:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        )
        input_label.pack(anchor='center', padx=10)

        user_input = tk.Text(
            input_frame,
            height=3,
            width=50,
            bg=DarkTheme.INPUT_BG,
            fg=DarkTheme.INPUT_TEXT,
            insertbackground=DarkTheme.TEXT_PRIMARY,
            selectbackground=DarkTheme.ACCENT_PRIMARY,
            selectforeground=DarkTheme.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        user_input.pack(fill='x', expand=True)
        user_input.bind("<Return>", self.callbacks['send_message'])
        user_input.bind("<Shift-Return>", self.callbacks['new_line'])
        
        return user_input, None

    def setup_control_panel(self):
        # Logo section with increased height
        logo_section = ModernFrame(self.sidebar_frame)
        logo_section.pack(fill='x', pady=5)

        script_dir = os.path.dirname(os.path.dirname(__file__))
        image_path = os.path.join(script_dir, "ui/imgs", "junin.png")
        if os.path.exists(image_path):
            # Carrega a imagem original
            original_image = Image.open(image_path)
            
            # Define o tamanho desejado para preencher a largura total
            target_width = 600  # Largura aumentada para as três colunas
            target_height = 250  # Altura aumentada
            
            # Mantém a proporção da imagem
            original_width, original_height = original_image.size
            width_ratio = target_width / original_width
            height_ratio = target_height / original_height
            ratio = min(width_ratio, height_ratio)
            
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            
            # Redimensiona a imagem
            resized_image = original_image.resize((new_width, new_height), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(resized_image)
            
            logo_label = tk.Label(
                logo_section, 
                image=self.photo, 
                bg=DarkTheme.BG_SECONDARY
            )
            logo_label.pack(fill='both', expand=True, padx=5, pady=5)

        # Container para as três colunas
        columns_container = ModernFrame(self.sidebar_frame)
        columns_container.pack(fill='both', expand=True)

        # Coluna 1 - Configurações da API
        self.sidebar_col1 = ModernFrame(columns_container)
        self.sidebar_col1.pack(side='left', fill='both', expand=True, padx=2)
        
        # Coluna 2 - Configurações de Fala
        self.sidebar_col2 = ModernFrame(columns_container)
        self.sidebar_col2.pack(side='left', fill='both', expand=True, padx=2)
        
        # Coluna 3 - Dispositivos e Opções
        self.sidebar_col3 = ModernFrame(columns_container)
        self.sidebar_col3.pack(side='left', fill='both', expand=True, padx=2)

        # === COLUNA 1: Configurações da API ===
        api_section_label = tk.Label(
            self.sidebar_col1,
            text="Configurações da API",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY,
            font=('Arial', 10, 'bold')
        )
        api_section_label.pack(pady=(10,5), fill='x')

        # Idioma
        tk.Label(
            self.sidebar_col1,
            text="Idioma do Sistema:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_col1,
            self.vars['language'],
            "English",
            "Português do Brasil",
            command=self.callbacks['update_language']
        ).pack(pady=(0,5), fill='x')

        # API
        tk.Label(
            self.sidebar_col1,
            text="Provedor da API:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_col1,
            self.vars['api_selection'],
            "OpenAI",
            "Ollama"
        ).pack(pady=(0,5), fill='x')

        # Modelo
        tk.Label(
            self.sidebar_col1,
            text="Modelo de IA:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(pady=(5,2), fill='x')
        
        ChatGPTModelSelector(
            self.sidebar_col1,
            self.vars['chatgpt_model']
        ).pack(pady=(0,5), fill='x')

        # === COLUNA 2: Configurações de Fala ===
        voice_section_label = tk.Label(
            self.sidebar_col2,
            text="Configurações de Fala",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY,
            font=('Arial', 10, 'bold')
        )
        voice_section_label.pack(pady=(10,5), fill='x')

        # Engine de Voz
        tk.Label(
            self.sidebar_col2,
            text="Engine de Voz:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_col2,
            self.vars['voice_engine'],
            "tts-1",
            "tts-1-hd",
            "tts-gpt4",
            "Voz do PC",
            command=self.callbacks['update_voice_dropdown']
        ).pack(pady=(0,5), fill='x')
        
        # Voz Selecionada
        tk.Label(
            self.sidebar_col2,
            text="Voz Selecionada:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(pady=(5,2), fill='x')
        
        voice_dropdown = ModernOptionMenu(
            self.sidebar_col2,
            self.vars['voice'],
            *self.handlers['events'].get_available_voices(self.vars['voice_engine'].get())
        )
        voice_dropdown.pack(pady=(0,5), fill='x')

        # Velocidade da Voz
        tk.Label(
            self.sidebar_col2,
            text="Velocidade da Voz:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(pady=(5,2), fill='x')
        
        speeds = [str(round(x * 0.1, 1)) for x in range(5, 26)]
        ModernOptionMenu(
            self.sidebar_col2,
            self.vars['voice_speed'],
            *speeds
        ).pack(pady=(0,5), fill='x')

        # Sotaque
        tk.Label(
            self.sidebar_col2,
            text="Sotaque:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_col2,
            self.vars['accent'],
            "Default (Sem sotaque)",
            "Mineiro",
            "Baiano",
            "Paulista"
        ).pack(pady=(0,5), fill='x')

        # Entonação
        tk.Label(
            self.sidebar_col2,
            text="Entonação:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_col2,
            self.vars['intonation'],
            "Default (Sem entonação)",
            "Susurrando bem baixinho",
            "Falando alto",
            "Gritando",
            "Chorando"
        ).pack(pady=(0,5), fill='x')

        # Emoção
        tk.Label(
            self.sidebar_col2,
            text="Emoção:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_col2,
            self.vars['emotion'],
            "Default (Sem emoção)",
            "Bem calmo",
            "Muito feliz",
            "Muito animado",
            "Bem triste"
        ).pack(pady=(0,5), fill='x')

        # Modo de Transcrição
        tk.Label(
            self.sidebar_col2,
            text="Modo de Transcrição:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_col2,
            self.vars['whisper'],
            "Online",
            "Local",
            "Com Correção Ortográfica"
        ).pack(pady=(0,5), fill='x')

        # Gravação VAD
        ModernCheckbutton(
            self.sidebar_col2,
            text="Gravação VAD",
            variable=self.vars['vad_enabled'],
            command=self.callbacks['vad_checkbox']
        ).pack(pady=2, fill='x')

        # === COLUNA 3: Dispositivos de Áudio e Opções ===
        # Dispositivos de Áudio
        tk.Label(
            self.sidebar_col3,
            text="Dispositivos de Áudio",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY,
            font=('Arial', 10, 'bold')
        ).pack(pady=(10,5), fill='x')

        # Dispositivo de Entrada
        input_devices = AudioDeviceConfig.list_audio_devices()['input']
        input_device_names = [device['name'] for device in input_devices]
        
        tk.Label(
            self.sidebar_col3,
            text="Dispositivo de Entrada:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_col3,
            self.vars['input_device'],
            *input_device_names
        ).pack(pady=(0,5), fill='x')

        # Dispositivo de Saída
        output_devices = AudioDeviceConfig.list_audio_devices()['output']
        output_device_names = [device['name'] for device in output_devices]
        
        tk.Label(
            self.sidebar_col3,
            text="Dispositivo de Saída:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_col3,
            self.vars['output_device'],
            *output_device_names
        ).pack(pady=(0,5), fill='x')

        # Opções
        tk.Label(
            self.sidebar_col3,
            text="Opções",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY,
            font=('Arial', 10, 'bold')
        ).pack(pady=(10,5), fill='x')

        # Ouvir Resposta (movido para primeira opção)
        ModernCheckbutton(
            self.sidebar_col3,
            text="Ouvir Resposta",
            variable=self.vars['hear_response']
        ).pack(pady=2, fill='x')

        # Sempre no Topo
        ModernCheckbutton(
            self.sidebar_col3,
            text="Sempre no Topo",
            variable=self.vars['always_on_top'],
            command=self.callbacks['toggle_always_on_top']
        ).pack(pady=2, fill='x')

        # Exibir Logs
        ModernCheckbutton(
            self.sidebar_col3,
            text="Exibir Logs",
            variable=self.vars['show_logs'],
            command=self.callbacks['toggle_logs']
        ).pack(pady=2, fill='x')

        # Controle Computador
        tk.Label(
            self.sidebar_col3,
            text="Controle Computador",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY,
            font=('Arial', 10, 'bold')
        ).pack(pady=(10,5), fill='x')

        # Computador por Voz
        ModernCheckbutton(
            self.sidebar_col3,
            text="Computador por Voz",
            variable=self.vars['computer_speech']
        ).pack(pady=(0,5), fill='x')

        # Monitor
        tk.Label(
            self.sidebar_col3,
            text="Monitor:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_col3,
            self.vars['monitor_index'],
            0, 1
        ).pack(pady=(0,5), fill='x')

        # Deslocamento do Monitor
        offset_frame = ModernFrame(self.sidebar_col3)
        offset_frame.pack(pady=5, fill='x')

        tk.Label(
            offset_frame,
            text="Deslocamento do Monitor:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(fill='x')

        # Deslocamento X
        x_frame = ModernFrame(offset_frame)
        x_frame.pack(fill='x', pady=2)
        
        tk.Label(
            x_frame,
            text="X:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(side='left', padx=5)
        
        tk.Entry(
            x_frame,
            textvariable=self.vars['monitor_offset_x'],
            bg=DarkTheme.INPUT_BG,
            fg=DarkTheme.INPUT_TEXT,
            relief=tk.FLAT,
            width=10
        ).pack(side='left', padx=5)

        # Deslocamento Y
        y_frame = ModernFrame(offset_frame)
        y_frame.pack(fill='x', pady=2)
        
        tk.Label(
            y_frame,
            text="Y:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(side='left', padx=5)
        
        tk.Entry(
            y_frame,
            textvariable=self.vars['monitor_offset_y'],
            bg=DarkTheme.INPUT_BG,
            fg=DarkTheme.INPUT_TEXT,
            relief=tk.FLAT,
            width=10
        ).pack(side='left', padx=5)

        return voice_dropdown
