import threading
import time
import logging
import json
import io
from ui.theme import DarkTheme
from config.audio_config import AudioConfig, AudioDeviceConfig
from config.log_config import LogConfig  # Importação do sistema de logs
from modules.open_ai.tts.tts_base import get_audio_stream_manager

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class EventHandlers:
    def __init__(self, app_components, handlers, variables, settings_manager):
        self.components = app_components
        self.handlers = handlers
        self.vars = variables
        self.settings_manager = settings_manager
        self.message_start_time = None
        self.total_time = 0
        self.audio_start_time = None
        self.device_config = AudioDeviceConfig()
        
        # Armazena os dispositivos atuais
        self.current_input_device = None
        self.current_output_device = None

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
            'toggle_logs': self.toggle_logs,  # Novo callback para controle de logs
        }

    def toggle_logs(self):
        """Alterna a visibilidade dos logs do sistema."""
        show_logs = self.vars['show_logs'].get()
        LogConfig.get_instance().set_log_visibility(show_logs)
        self.settings_manager.set_setting("show_logs", show_logs)
        log.info("Visibilidade dos logs alterada para: %s", show_logs)

    def handle_recording_complete(self, audio_file):
        """Lida com a gravação concluída.""" 
        recording_time = time.time() - self.message_start_time
        log.info("Tempo de gravação: %.2f segundos", recording_time)
        self.total_time = recording_time

        # Verifica se está usando TTS-GPT4
        is_skip_transcription = self.vars['voice_engine'].get() == "tts-gpt4"
        
        if is_skip_transcription:
            log.info("Usando TTS-GPT4, enviando áudio diretamente sem transcrição")
            
            # Lê o conteúdo do áudio
            if isinstance(audio_file, io.BytesIO):
                # Se já é um BytesIO, usa diretamente
                audio_data = audio_file.getvalue()
            else:
                # Se é um caminho de arquivo, abre e lê
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()
            
            import base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            if self.vars['hear_response'].get():
                self.audio_start_time = time.time()
                
                # 1. Define a voz primeiro para configurar o modelo e skip_transcription
                self.handlers['speech'].set_voice(
                    self.vars['voice'].get(),
                    self.vars['voice_engine'].get()
                )
                
                # 2. Define o callback para atualizar o texto do chat
                def update_chat_text(text):
                    self.components['chat_display'].add_message(text, "Junin")
                self.handlers['speech'].set_transcript_callback(update_chat_text)
                
                # 3. Define o áudio para o TTS com skip_transcription=True
                self.handlers['speech'].set_input_audio(audio_base64, skip_transcription=True)
                
                # 4. Finalmente, processa o áudio
                self.handlers['speech'].speak_response(
                    "Processando áudio...",
                    on_speech_start=self.on_speech_start
                )
            return
        
        # Fluxo normal para outros engines
        log.info("Usando modo de transcrição normal")
        transcription_start = time.time()
        transcript, is_corrected = self.handlers['speech'].handle_recording_complete(audio_file)
        transcription_time = time.time() - transcription_start
        log.info("Tempo de transcrição: %.2f segundos", transcription_time)
        
        if transcript is not None:
            self.components['chat_display'].add_message(transcript, "Eu")
            
            response_start = time.time()
            response = self.handlers['chat'].get_response(
                transcript,
                use_ollama=(self.vars['api_selection'].get() == "Ollama"),
                model=self.vars['chatgpt_model'].get(),
                is_corrected_text=is_corrected
            )
            
            response_time = time.time() - response_start
            log.info("Tempo de resposta: %.2f segundos", response_time)
            
            # Extrai o texto da resposta
            response_text = self.extract_response_text(response)
            self.components['chat_display'].add_message(response_text, "Junin")
            
            if self.vars['hear_response'].get():
                self.audio_start_time = time.time()
                # Define a voz antes de falar
                self.handlers['speech'].set_voice(
                    self.vars['voice'].get(),
                    self.vars['voice_engine'].get()
                )
                
                self.handlers['speech'].speak_response(
                    response_text,
                    on_speech_start=self.on_speech_start
                )

    def extract_response_text(self, response):
        """Extrai o texto da resposta do JSON se necessário."""
        try:
            # Remove marcadores de código JSON se presentes
            if isinstance(response, str):
                response = response.replace('```json\n', '').replace('\n```', '')
                if response.strip().startswith('{'):
                    data = json.loads(response)
                    if isinstance(data, dict):
                        if 'content' in data and isinstance(data['content'], dict):
                            return data['content'].get('answer', '')
                        elif 'answer' in data:
                            return data['answer']
            return response
        except:
            return response

    def get_available_voices(self, engine_type="tts-1"):
        """
        Obtém as vozes disponíveis para o mecanismo especificado.
        
        Args:
            engine_type: "tts-1" ou "Voz do PC"
        """
        return self.handlers['speech'].get_available_voices(engine_type)

    def on_speech_start(self):
        """Callback chamado quando a fala começa.""" 
        speech_start_time = time.time()
        log.info("Tempo de preparação do áudio até o início da fala: %.2f segundos", speech_start_time - self.audio_start_time)

    def toggle_recording(self, event=None):
        """Alterna a gravação de áudio.""" 
        if self.handlers['audio'].is_recording or self.handlers['audio'].is_recording_vad:
            self.stop_recording()
        else:
            self.components['record_button'].config(text="Gravando...", bg=DarkTheme.ACCENT_ERROR)
            self.message_start_time = time.time()
            if self.vars['vad_enabled'].get():
                # Apenas inicia a gravação VAD se não estiver já gravando
                if not self.handlers['audio'].is_recording_vad:
                    self.handlers['audio'].is_recording_vad = True
                    self.handlers['audio'].stop_event.clear()
                    threading.Thread(target=self.handlers['audio'].vad_recording).start()
            else:
                self.handlers['audio'].is_recording = True
                self.handlers['audio'].start_recording()

    def stop_recording(self):
        """Para a gravação de áudio.""" 
        if self.handlers['audio'].is_recording_vad:
            self.handlers['audio'].stop_event.set()
            self.handlers['audio'].is_recording_vad = False
        if self.handlers['audio'].is_recording:
            self.handlers['audio'].is_recording = False
            self.handlers['audio'].stop_recording()
        self.components['record_button'].config(text="Clique para Gravar", bg=DarkTheme.BUTTON_BG)

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
        log.info("Tempo de resposta: %.2f segundos", response_time)
        
        # Extrai o texto da resposta
        response_text = self.extract_response_text(response)
        self.components['chat_display'].add_message(response_text, "Junin")
        
        if self.vars['hear_response'].get():
            self.audio_start_time = time.time()
            # Define a voz antes de falar
            self.handlers['speech'].set_voice(
                self.vars['voice'].get(),
                self.vars['voice_engine'].get()
            )
            self.handlers['speech'].speak_response(
                response_text,
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
        voices = self.get_available_voices(selected_engine)
        menu = self.components['voice_dropdown']['menu']
        menu.delete(0, 'end')
        
        for voice in voices:
            menu.add_command(
                label=voice,
                command=lambda v=voice: self._update_voice(v, selected_engine)
            )
        
        # Define a voz atual com o novo engine
        if voices:
            # Se houver uma voz salva nas configurações, usa ela
            saved_voice = self.settings_manager.get_setting("selected_voice")
            if saved_voice and saved_voice in voices:
                self._update_voice(saved_voice, selected_engine)
            else:
                self._update_voice(voices[0], selected_engine)
        
        self.settings_manager.set_setting("selected_voice_engine", selected_engine)
        log.info("Engine de voz atualizado para: %s", selected_engine)

    def _update_voice(self, voice, engine_type):
        """Atualiza a voz e o engine.""" 
        self.vars['voice'].set(voice)
        self.handlers['speech'].set_voice(voice, engine_type)
        # Salva a voz selecionada nas configurações
        self.settings_manager.set_setting("selected_voice", voice)
        log.info("Voz atualizada para: %s com engine: %s", voice, engine_type)

    def vad_checkbox_callback(self):
        """Lida com a mudança de estado da caixa de seleção VAD.""" 
        if self.vars['vad_enabled'].get():
            # Apenas calibra o threshold, mas não inicia a gravação automaticamente
            self.handlers['audio'].threshold = self.handlers['audio'].calibrate_noise_threshold()
            log.info("VAD ativado e calibrado.")
        else:
            # Garante que a gravação VAD seja interrompida ao desativar
            if self.handlers['audio'].is_recording_vad:
                self.stop_recording()
                log.info("VAD desativado.")
        self.settings_manager.set_setting("vad_enabled", self.vars['vad_enabled'].get())

    def on_input_device_select(self, *args):
        """Lida com a seleção do dispositivo de entrada.""" 
        try:
            selected_device = self.vars['input_device'].get()
            
            # Verifica se o dispositivo realmente mudou
            if selected_device == self.current_input_device:
                log.info("Dispositivo de entrada já está selecionado: %s", selected_device)
                return
                
            log.info("Iniciando atualização do dispositivo de entrada para: %s", selected_device)
            
            # Obtém o índice do dispositivo
            audio_devices = AudioDeviceConfig.list_audio_devices()
            device_index = next(
                (device['index'] for device in audio_devices['input'] if device['name'] == selected_device), 
                None
            )
            
            if device_index is not None:
                # Atualiza o dispositivo no AudioHandler
                if self.handlers['audio'].set_input_device(device_index):
                    log.info("Dispositivo de entrada atualizado: %s", selected_device)
                    self.current_input_device = selected_device
                    self.settings_manager.set_setting("input_device", selected_device)
                    log.info("Configuração do dispositivo de entrada salva: %s", selected_device)
                else:
                    log.error("Falha ao atualizar dispositivo de entrada")
        except Exception as e:
            log.error("Erro ao selecionar o dispositivo de entrada: %s", e)

    def on_output_device_select(self, *args):
        """Lida com a seleção do dispositivo de saída.""" 
        try:
            selected_device = self.vars['output_device'].get()
            
            # Verifica se o dispositivo realmente mudou
            if selected_device == self.current_output_device:
                log.info("Dispositivo de saída já está selecionado: %s", selected_device)
                return
                
            log.info("Iniciando atualização do dispositivo de saída para: %s", selected_device)
            
            # Obtém o índice do dispositivo
            audio_devices = AudioDeviceConfig.list_audio_devices()
            device_index = next(
                (device['index'] for device in audio_devices['output'] if device['name'] == selected_device), 
                None
            )
            
            if device_index is not None:
                # Atualiza o AudioHandler
                if self.handlers['audio'].set_output_device(device_index):
                    log.info("Dispositivo de saída atualizado no AudioHandler: %s", selected_device)
                else:
                    log.error("Falha ao atualizar dispositivo de saída no AudioHandler")
                    return

                # Atualiza o AudioStreamManager global
                audio_stream = get_audio_stream_manager()
                if audio_stream.update_output_device(selected_device):
                    log.info("Dispositivo de saída atualizado no AudioStreamManager: %s", selected_device)
                else:
                    log.error("Falha ao atualizar dispositivo de saída no AudioStreamManager")
                    return

                # Salva a configuração e atualiza o dispositivo atual
                self.settings_manager.set_setting("output_device", selected_device)
                self.current_output_device = selected_device
                log.info("Configuração do dispositivo de saída salva: %s", selected_device)
        except Exception as e:
            log.error("Erro ao selecionar o dispositivo de saída: %s", e)

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
            
            log.info("Configurações do monitor atualizadas - Índice: %d, Deslocamento: [%d, %d]", monitor_index, x_offset, y_offset)
        except ValueError:
            log.warning("Valores de deslocamento do monitor inválidos. Usando os padrões.")
            self.vars['monitor_offset_x'].set("0")
            self.vars['monitor_offset_y'].set("0")

    def on_computer_speech_change(self, *args):
        """Lida com mudanças na configuração de fala do computador.""" 
        computer_speech = self.vars['computer_speech'].get()
        self.handlers['computer'].falar = computer_speech
        self.settings_manager.set_setting("computer_speech", computer_speech)
        log.info("Fala do computador %s", 'ativada' if computer_speech else 'desativada')
