import threading
import time
from config.theme import DarkTheme, AudioConfig

class EventHandlers:
    def __init__(self, app_components, handlers, variables, settings_manager):
        self.components = app_components
        self.handlers = handlers
        self.vars = variables
        self.settings_manager = settings_manager
        self.message_start_time = None
        self.total_time = 0
        self.audio_start_time = None

        # Adiciona o callback de correção ortográfica
        self.callbacks = {
            'send_message': self.send_message,
            'new_line': self.new_line,
            'toggle_recording': self.toggle_recording,
            'update_language': self.update_language,
            'toggle_always_on_top': self.toggle_always_on_top,
            'update_voice_dropdown': self.update_voice_dropdown,
            'vad_checkbox': self.vad_checkbox_callback,
            'spelling_correction': self.handle_spelling_correction,
        }

    def on_speech_start(self):
        """Callback chamado quando a fala começa."""
        speech_start_time = time.time()
        prep_time = speech_start_time - self.audio_start_time
        print(f"Tempo de preparação do áudio até o início da fala: {prep_time:.2f} segundos")

    def toggle_recording(self, event=None):
        """Alterna a gravação de áudio."""
        if self.handlers['audio'].is_recording or self.handlers['audio'].is_recording_vad:
            self.stop_recording()
            self.components['record_button'].config(text="Clique para Gravar", bg=DarkTheme.BUTTON_BG)
        else:
            self.components['record_button'].config(text="Gravando...", bg=DarkTheme.ACCENT_ERROR)
            self.message_start_time = time.time()
            if self.vars['vad_enabled'].get():
                self.handlers['audio'].is_recording_vad = True
                self.handlers['audio'].stop_event.clear()
                threading.Thread(target=self.handlers['audio'].vad_recording).start()
            else:
                self.handlers['audio'].is_recording = True
                self.handlers['audio'].start_recording()

    def stop_recording(self):
        """Para a gravação de áudio."""
        self.handlers['audio'].stop_recording()
        self.components['record_button'].config(text="Clique para Gravar", bg=DarkTheme.BUTTON_BG)

    def handle_recording_complete(self, audio_file):
        """Lida com a gravação concluída."""
        recording_time = time.time() - self.message_start_time
        print(f"\nTempo de gravação: {recording_time:.2f} segundos")
        self.total_time = recording_time

        transcription_start = time.time()
        transcript = self.handlers['speech'].transcribe_audio(
            audio_file, 
            use_local=(self.vars['whisper'].get() == "Local")
        )
        
        if transcript:
            transcription_time = time.time() - transcription_start
            print(f"Tempo de transcrição: {transcription_time:.2f} segundos")
            
            self.components['chat_display'].add_message(transcript, "Eu")
            
            response_start = time.time()
            response = self.handlers['chat'].get_response(
                transcript,
                use_ollama=(self.vars['api_selection'].get() == "Ollama"),
                model=self.vars['chatgpt_model'].get()
            )
            
            response_time = time.time() - response_start
            print(f"Tempo de resposta: {response_time:.2f} segundos")
            
            self.components['chat_display'].add_message(response, "Junin")
            
            if self.vars['hear_response'].get():
                self.audio_start_time = time.time()
                # Define a voz antes de falar
                self.handlers['speech'].text_to_speech.set_voice(self.vars['voice'].get())
                self.handlers['speech'].text_to_speech.speak_response(
                    response,
                    on_speech_start=self.on_speech_start
                )

    def send_message(self, event=None):
        """Envia uma mensagem de texto."""
        message = self.components['user_input'].get("1.0", "end-1c").strip()
        if message:
            threading.Thread(target=self.process_message, args=(message,)).start()
        return "break"

    def process_message(self, message):
        """Processa a mensagem em uma thread separada.""" 
        self.message_start_time = time.time()
        
        self.components['chat_display'].add_message(message, "Eu")
        self.components['user_input'].delete("1.0", "end")
        
        response_start = time.time()
        response = self.handlers['chat'].get_response(
            message,
            use_ollama=(self.vars['api_selection'].get() == "Ollama"),
            model=self.vars['chatgpt_model'].get()
        )
        
        response_time = time.time() - response_start
        print(f"\nTempo de resposta: {response_time:.2f} segundos")
        
        self.components['chat_display'].add_message(response, "Junin")
        
        if self.vars['hear_response'].get():
            self.audio_start_time = time.time()
            # Define a voz antes de falar
            self.handlers['speech'].text_to_speech.set_voice(self.vars['voice'].get())
            self.handlers['speech'].text_to_speech.speak_response(
                response,
                on_speech_start=self.on_speech_start
            )

    def new_line(self, event=None):
        """Adiciona uma nova linha na área de entrada.""" 
        self.components['user_input'].insert("insert", "\n")
        return "break"

    def update_language(self, selected_language):
        """Atualiza o idioma da interface.""" 
        if selected_language == "English":
            self.components['record_button'].config(text="Click to Record")
        else:
            self.components['record_button'].config(text="Clique para Gravar")
        self.settings_manager.set_setting("selected_language", selected_language)

    def toggle_always_on_top(self):
        """Alterna a janela sempre no topo.""" 
        self.components['root'].attributes('-topmost', self.vars['always_on_top'].get())
        self.settings_manager.set_setting("always_on_top", self.vars['always_on_top'].get())

    def update_voice_dropdown(self, selected_engine):
        """Atualiza as opções de voz com base no mecanismo selecionado.""" 
        voices = self.handlers['speech'].get_available_voices(selected_engine)
        menu = self.components['voice_dropdown']['menu']
        menu.delete(0, 'end')
        
        for voice in voices:
            if isinstance(voice, tuple):
                menu.add_command(
                    label=voice[1],
                    command=lambda v=voice[0]: self.vars['voice'].set(v)
                )
            else:
                menu.add_command(
                    label=voice,
                    command=lambda v=voice: self.vars['voice'].set(v)
                )
        
        self.settings_manager.set_setting("selected_voice_engine", selected_engine)

    def vad_checkbox_callback(self):
        """Lida com a mudança de estado da caixa de seleção VAD.""" 
        if self.vars['vad_enabled'].get():
            self.handlers['audio'].threshold = self.handlers['audio'].calibrate_noise_threshold()
        self.settings_manager.set_setting("vad_enabled", self.vars['vad_enabled'].get())

    def on_input_device_select(self, *args):
        """Lida com a seleção do dispositivo de entrada.""" 
        try:
            selected_device = self.vars['input_device'].get()
            audio_devices = self.handlers['audio'].list_audio_devices()
            
            device_index = next(
                (device['index'] for device in audio_devices['input'] if device['name'] == selected_device), 
                None
            )
            
            if device_index is not None:
                self.handlers['audio'].set_input_device(device_index)
                print(f"Dispositivo de entrada selecionado: {selected_device}")
                self.settings_manager.set_setting("input_device", selected_device)
        except Exception as e:
            print(f"Erro ao selecionar o dispositivo de entrada: {e}")

    def on_output_device_select(self, *args):
        """Lida com a seleção do dispositivo de saída.""" 
        try:
            selected_device = self.vars['output_device'].get()
            audio_devices = self.handlers['audio'].list_audio_devices()
            
            device_index = next(
                (device['index'] for device in audio_devices['output'] if device['name'] == selected_device), 
                None
            )
            
            if device_index is not None:
                self.handlers['audio'].set_output_device(device_index)
                print(f"Dispositivo de saída selecionado: {selected_device}")
                self.handlers['audio'].stream = self.handlers['audio'].p.open(
                    format=AudioConfig.FORMAT,
                    channels=AudioConfig.CHANNELS,
                    rate=AudioConfig.RATE,
                    output=True,
                    output_device_index=device_index,
                    frames_per_buffer=AudioConfig.CHUNK
                )
                print("Fluxo de áudio inicializado.")
                self.settings_manager.set_setting("output_device", selected_device)
        except Exception as e:
            print(f"Erro ao selecionar o dispositivo de saída: {e}")

    def on_model_select(self, *args):
        """Lida com a seleção do modelo ChatGPT.""" 
        selected_model = self.vars['chatgpt_model'].get()
        self.settings_manager.set_setting("selected_model", selected_model)

    def handle_spelling_correction(self, event=None):
        """Lida com a seleção da correção ortográfica OnlineSpelling."""
        selected_option = self.vars['spelling_correction'].get()
        if selected_option == "OnlineSpelling":
            audio_file = self.handlers['audio'].get_last_recorded_file()
            if audio_file:
                # Usa o prompt de correção ortográfica carregado do TaskManager
                system_message = self.handlers['task'].get_spelling_correction_prompt()
                threading.Thread(target=self.handlers['speech'].transcribe_with_spellcheck, args=(system_message, audio_file)).start()

    def on_monitor_settings_change(self, *args):
        """Lida com mudanças nas configurações do monitor."""
        try:
            monitor_index = self.vars['monitor_index'].get()
            x_offset = int(self.vars['monitor_offset_x'].get())
            y_offset = int(self.vars['monitor_offset_y'].get())
            
            # Atualiza as configurações do manipulador do computador
            self.handlers['computer'].monitor_index = monitor_index
            self.handlers['computer'].monitor_offset = [x_offset, y_offset]
            
            # Salva as configurações
            self.settings_manager.set_setting("monitor_index", monitor_index)
            self.settings_manager.set_setting("monitor_offset", [x_offset, y_offset])
            
            print(f"Configurações do monitor atualizadas - Índice: {monitor_index}, Deslocamento: [{x_offset}, {y_offset}]")
        except ValueError:
            print("Valores de deslocamento do monitor inválidos. Usando os padrões.")
            self.vars['monitor_offset_x'].set("0")
            self.vars['monitor_offset_y'].set("0")

    def on_computer_speech_change(self, *args):
        """Lida com mudanças na configuração de fala do computador."""
        computer_speech = self.vars['computer_speech'].get()
        self.handlers['computer'].falar = computer_speech
        self.settings_manager.set_setting("computer_speech", computer_speech)
        print(f"Fala do computador {'ativada' if computer_speech else 'desativada'}")
