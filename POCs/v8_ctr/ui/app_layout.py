import tkinter as tk
from PIL import Image, ImageTk
import os
from config.theme import DarkTheme
from ui.components import (
    ModernButton, ModernFrame, ModernCheckbutton, 
    ModernOptionMenu, ChatDisplay, ChatGPTModelSelector
)
from modules.audio_handler import AudioHandler

class AppLayout:
    def __init__(self, root, handlers, variables, callbacks):
        self.root = root
        self.handlers = handlers
        self.vars = variables
        self.callbacks = callbacks
        self.sidebar_visible = True
        
        # Callbacks padrão para evitar KeyError
        self.default_callbacks = {
            'send_message': self._default_send_message,
            'new_line': self._default_new_line,
            'toggle_recording': self._default_toggle_recording,
            'update_language': self._default_update_language,
            'toggle_always_on_top': self._default_toggle_always_on_top,
            'update_voice_dropdown': self._default_update_voice_dropdown,
            'vad_checkbox': self._default_vad_checkbox,
        }
        
        # Mescla os callbacks padrão com os callbacks fornecidos
        self.callbacks = {**self.default_callbacks, **self.callbacks}

        # Configura o evento para salvar a posição da janela
        self.root.bind("<Configure>", self._save_window_position)
        
    def _default_send_message(self, event=None):
        """Placeholder padrão para o callback send_message.""" 
        print("send_message padrão chamado")
        return "break"
    
    def _default_new_line(self, event=None):
        """Placeholder padrão para o callback new_line.""" 
        print("new_line padrão chamado")
        return "break"
    
    def _default_toggle_recording(self, event=None):
        """Placeholder padrão para o callback toggle_recording.""" 
        print("toggle_recording padrão chamado")
    
    def _default_update_language(self, selected_language):
        """Placeholder padrão para o callback update_language.""" 
        print(f"update_language padrão chamado com {selected_language}")
    
    def _default_toggle_always_on_top(self):
        """Placeholder padrão para o callback toggle_always_on_top.""" 
        print("toggle_always_on_top padrão chamado")
    
    def _default_update_voice_dropdown(self, selected_engine):
        """Placeholder padrão para o callback update_voice_dropdown.""" 
        print(f"update_voice_dropdown padrão chamado com {selected_engine}")
    
    def _default_vad_checkbox(self):
        """Placeholder padrão para o callback vad_checkbox.""" 
        print("vad_checkbox padrão chamado")

    def _save_window_position(self, event=None):
        """Salva a posição e tamanho da janela quando movida ou redimensionada"""
        # Ignora eventos que não são da janela principal
        if event.widget != self.root:
            return
            
        # Obtém a geometria atual da janela
        geometry = self.root.geometry()
        # Salva em um arquivo de configuração
        if hasattr(self.handlers, 'settings'):
            self.handlers.settings.save_window_geometry(geometry)
        
    def setup_window(self):
        """Configura a janela principal.""" 
        self.root.title("J.U.N.I.N. Release v1.0.0")
        self.root.configure(bg=DarkTheme.BG_PRIMARY)
        
        # Carrega a geometria salva ou usa o padrão
        if hasattr(self.handlers, 'settings'):
            geometry = self.handlers.settings.get_window_geometry()
            if geometry:
                self.root.geometry(geometry)
            else:
                self.root.geometry("800x1000+100+100")
        else:
            self.root.geometry("800x1000+100+100")
        
        # Cria o container principal
        self.main_container = tk.Frame(self.root, bg=DarkTheme.BG_PRIMARY)
        self.main_container.pack(fill='both', expand=True)
        
        # Cria o frame de conteúdo
        self.content_frame = tk.Frame(self.main_container, bg=DarkTheme.BG_PRIMARY)
        self.content_frame.pack(side='left', fill='both', expand=True)
        
        # Cria o frame da barra lateral
        self.sidebar_frame = ModernFrame(self.main_container)
        self.sidebar_frame.pack(side='right', fill='y', padx=5)
        
    def toggle_sidebar(self):
        """Alterna a visibilidade da barra lateral"""
        if self.sidebar_visible:
            self.sidebar_frame.pack_forget()
        else:
            self.sidebar_frame.pack(side='right', fill='y', padx=5)
        self.sidebar_visible = not self.sidebar_visible

    def setup_chat_area(self):
        """Configura a área de exibição do chat.""" 
        # Container principal do chat com padding fixo
        chat_container = ModernFrame(self.content_frame)
        chat_container.pack(padx=20, fill='both', expand=True)
        
        # Cabeçalho do chat com largura fixa
        chat_header = ModernFrame(chat_container)
        chat_header.pack(fill='x', pady=(0, 5))
        
        # Container para centralizar o título
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

        # Botão de toggle no cabeçalho
        toggle_button = ModernButton(
            chat_header,
            text="☰",
            command=self.toggle_sidebar,
            width=2
        )
        toggle_button.place(relx=1.0, rely=0.5, anchor='e', x=-5)

        # Área do chat
        self.chat_display = ChatDisplay(
            chat_container,
            height=15,
            width=50
        )
        self.chat_display.pack(fill='both', expand=True, pady=(0, 5))

        # Botão de gravação abaixo do chat
        record_button = ModernButton(
            chat_container,
            text="Clique para Gravar",
            command=self.callbacks['toggle_recording']
        )
        record_button.pack()
        
        return self.chat_display, record_button

    def setup_input_area(self):
        """Configura a área de entrada do usuário.""" 
        input_frame = ModernFrame(self.content_frame)
        input_frame.pack(pady=(10, 10), padx=20, fill='x')

        # Container para centralizar o label
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
        """Configura o painel de controle na barra lateral.""" 
        # Seção superior para o logo
        logo_section = ModernFrame(self.sidebar_frame)
        logo_section.pack(fill='x', pady=5)

        # Adiciona o logo
        script_dir = os.path.dirname(os.path.dirname(__file__))
        image_path = os.path.join(script_dir, "junin.png")
        if os.path.exists(image_path):
            image = Image.open(image_path)
            # Logo com altura flexível mantendo proporção
            image.thumbnail((400, 150), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(image)
            logo_label = tk.Label(
                logo_section, 
                image=self.photo, 
                bg=DarkTheme.BG_SECONDARY
            )
            logo_label.pack(fill='both', expand=True)

        # Container para as duas colunas
        columns_container = ModernFrame(self.sidebar_frame)
        columns_container.pack(fill='both', expand=True)

        # Coluna Esquerda
        self.sidebar_left = ModernFrame(columns_container)
        self.sidebar_left.pack(side='left', fill='both', expand=True, padx=2)
        
        # Coluna Direita
        self.sidebar_right = ModernFrame(columns_container)
        self.sidebar_right.pack(side='right', fill='both', expand=True, padx=2)

        # Seção da API (Coluna Esquerda)
        api_section_label = tk.Label(
            self.sidebar_left,
            text="Configurações da API",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY,
            font=('Arial', 10, 'bold')
        )
        api_section_label.pack(pady=(10,5), fill='x')

        # Seleção de Idioma
        language_label = tk.Label(
            self.sidebar_left,
            text="Idioma do Sistema:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        )
        language_label.pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_left,
            self.vars['language'],
            "English",
            "Português do Brasil",
            command=self.callbacks['update_language']
        ).pack(pady=(0,5), fill='x')

        # Seleção da API
        api_label = tk.Label(
            self.sidebar_left,
            text="Provedor da API:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        )
        api_label.pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_left,
            self.vars['api_selection'],
            "OpenAI",
            "Ollama"
        ).pack(pady=(0,5), fill='x')

        # Seleção do Modelo
        model_label = tk.Label(
            self.sidebar_left,
            text="Modelo de IA:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        )
        model_label.pack(pady=(5,2), fill='x')
        
        ChatGPTModelSelector(
            self.sidebar_left,
            self.vars['chatgpt_model']
        ).pack(pady=(0,5), fill='x')

        # Configurações de Fala
        voice_section_label = tk.Label(
            self.sidebar_left,
            text="Configurações de Fala",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY,
            font=('Arial', 10, 'bold')
        )
        voice_section_label.pack(pady=(10,5), fill='x')

        # Ouvir Resposta
        ModernCheckbutton(
            self.sidebar_left,
            text="Ouvir Resposta",
            variable=self.vars['hear_response']
        ).pack(pady=2, fill='x')

        # Engine de Voz
        voice_engine_label = tk.Label(
            self.sidebar_left,
            text="Engine de Voz:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        )
        voice_engine_label.pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_left,
            self.vars['voice_engine'],
            "tts-1",
            "Voz do PC",
            command=self.callbacks['update_voice_dropdown']
        ).pack(pady=(0,5), fill='x')
        
        # Voz Selecionada
        voice_selection_label = tk.Label(
            self.sidebar_left,
            text="Voz Selecionada:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        )
        voice_selection_label.pack(pady=(5,2), fill='x')
        
        voice_dropdown = ModernOptionMenu(
            self.sidebar_left,
            self.vars['voice'],
            *self.handlers['speech'].get_available_voices(self.vars['voice_engine'].get())
        )
        voice_dropdown.pack(pady=(0,5), fill='x')

        # Velocidade da Voz
        voice_speed_label = tk.Label(
            self.sidebar_left,
            text="Velocidade da Voz:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        )
        voice_speed_label.pack(pady=(5,2), fill='x')
        
        # Cria lista de velocidades de 0.5 a 2.5 com incremento de 0.1
        speeds = [str(round(x * 0.1, 1)) for x in range(5, 26)]
        
        ModernOptionMenu(
            self.sidebar_left,
            self.vars['voice_speed'],
            *speeds
        ).pack(pady=(0,5), fill='x')

        # Modo de Transcrição
        whisper_label = tk.Label(
            self.sidebar_left,
            text="Modo de Transcrição:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        )
        whisper_label.pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_left,
            self.vars['whisper'],
            "Online",
            "Local",
            "Com Correção Ortográfica"
        ).pack(pady=(0,5), fill='x')

        # Gravação VAD
        ModernCheckbutton(
            self.sidebar_left,
            text="Gravação VAD",
            variable=self.vars['vad_enabled'],
            command=self.callbacks['vad_checkbox']
        ).pack(pady=2, fill='x')

        # Controle Computador
        computer_control_label = tk.Label(
            self.sidebar_left,
            text="Controle Computador",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY,
            font=('Arial', 10, 'bold')
        )
        computer_control_label.pack(pady=(10,5), fill='x')

        # Computador por Voz
        ModernCheckbutton(
            self.sidebar_left,
            text="Computador por Voz",
            variable=self.vars['computer_speech']
        ).pack(pady=(0,5), fill='x')

        # Seção de Dispositivos de Áudio (Coluna Direita)
        audio_section_label = tk.Label(
            self.sidebar_right,
            text="Dispositivos de Áudio",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY,
            font=('Arial', 10, 'bold')
        )
        audio_section_label.pack(pady=(10,5), fill='x')

        # Seleção do Dispositivo de Entrada
        input_devices = AudioHandler.list_audio_devices()['input']
        input_device_names = [device['name'] for device in input_devices]
        
        input_device_label = tk.Label(
            self.sidebar_right,
            text="Dispositivo de Entrada:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        )
        input_device_label.pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_right,
            self.vars['input_device'],
            *input_device_names
        ).pack(pady=(0,5), fill='x')

        # Seleção do Dispositivo de Saída
        output_devices = AudioHandler.list_audio_devices()['output']
        output_device_names = [device['name'] for device in output_devices]
        
        output_device_label = tk.Label(
            self.sidebar_right,
            text="Dispositivo de Saída:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        )
        output_device_label.pack(pady=(5,2), fill='x')
        
        ModernOptionMenu(
            self.sidebar_right,
            self.vars['output_device'],
            *output_device_names
        ).pack(pady=(0,5), fill='x')

        # Seção de Opções
        options_section_label = tk.Label(
            self.sidebar_right,
            text="Opções",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY,
            font=('Arial', 10, 'bold')
        )
        options_section_label.pack(pady=(10,5), fill='x')

        # Sempre no Topo
        ModernCheckbutton(
            self.sidebar_right,
            text="Sempre no Topo",
            variable=self.vars['always_on_top'],
            command=self.callbacks['toggle_always_on_top']
        ).pack(pady=2, fill='x')

        # Monitor
        monitor_index_label = tk.Label(
            self.sidebar_right,
            text="Monitor:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        )
        monitor_index_label.pack(pady=(5,2), fill='x')

        ModernOptionMenu(
            self.sidebar_right,
            self.vars['monitor_index'],
            0, 1
        ).pack(pady=(0,5), fill='x')

        # Deslocamento do Monitor
        offset_frame = ModernFrame(self.sidebar_right)
        offset_frame.pack(pady=5, fill='x')

        offset_label = tk.Label(
            offset_frame,
            text="Deslocamento do Monitor:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        )
        offset_label.pack(fill='x')

        # Deslocamento X
        x_frame = ModernFrame(offset_frame)
        x_frame.pack(fill='x', pady=2)
        
        tk.Label(
            x_frame,
            text="X:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(side='left', padx=5)
        
        x_entry = tk.Entry(
            x_frame,
            textvariable=self.vars['monitor_offset_x'],
            bg=DarkTheme.INPUT_BG,
            fg=DarkTheme.INPUT_TEXT,
            relief=tk.FLAT,
            width=10
        )
        x_entry.pack(side='left', padx=5)

        # Deslocamento Y
        y_frame = ModernFrame(offset_frame)
        y_frame.pack(fill='x', pady=2)
        
        tk.Label(
            y_frame,
            text="Y:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY
        ).pack(side='left', padx=5)
        
        y_entry = tk.Entry(
            y_frame,
            textvariable=self.vars['monitor_offset_y'],
            bg=DarkTheme.INPUT_BG,
            fg=DarkTheme.INPUT_TEXT,
            relief=tk.FLAT,
            width=10
        )
        y_entry.pack(side='left', padx=5)

        return voice_dropdown
