import tkinter as tk
import keyboard
from PIL import Image, ImageTk
import pyaudio
import threading
from openai import OpenAI
import wave
import io
import json
import os
from dotenv import load_dotenv
import pyaudio
import numpy as np
from collections import deque
import time
from task_manager import TaskManager

# Load environment variables
load_dotenv()

# Audio recording settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24_000 #24_000 # 16000

# Parâmetros de configuração
MOVING_AVERAGE_WINDOW = 50  # Número de amostras para a média móvel inicial (ruído ambiente)
VOLUME_MULTIPLIER = 3  # Multiplicador para definir o threshold
NOISE_FLOOR = 100  # Filtro de ruído para volumes muito baixos
RECORD_TIME_AFTER_DETECTION = 2.0  # Tempo de gravação após a detecção (em segundos)
DETECTION_TIME = 0.2  # Tempo necessário para considerar que o som é contínuo (em segundos)

client = OpenAI()
task_manager = TaskManager()

class ChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JUNIN")
        self.root.configure(bg='white')

        # Load saved settings
        self.settings_file = os.path.join(os.getcwd(), "junin_settings.json")
        self.settings = self.load_settings()
        
        # Configure language and update UI
        self.language_var = tk.StringVar(value=self.settings.get("selected_language", "English"))
        
        # Add selection for OpenAI or Ollama
        self.api_selection_var = tk.StringVar(value=self.settings.get("selected_api", "OpenAI"))
        api_selection_frame = tk.Frame(root)
        api_selection_frame.pack(pady=5, padx=10, fill='x')
        self.api_selection_label = tk.Label(api_selection_frame, text="Selecionar API:")
        self.api_selection_label.pack(side='left')
        self.api_selection_dropdown = tk.OptionMenu(api_selection_frame, self.api_selection_var, "OpenAI", "Ollama")
        self.api_selection_dropdown.pack(side='left', padx=10)

        # Add checkbox for "Always on Top"
        self.always_on_top_var = tk.BooleanVar(value=self.settings.get("always_on_top", True))
        always_on_top_frame = tk.Frame(root)
        always_on_top_frame.pack(pady=5, padx=10, fill='x')
        self.always_on_top_checkbox = tk.Checkbutton(always_on_top_frame, text="Sempre no Topo", variable=self.always_on_top_var, command=self.toggle_always_on_top)
        self.language_dropdown = tk.OptionMenu(always_on_top_frame, self.language_var, "English", "Português do Brasil", command=self.update_language)
        self.always_on_top_checkbox.pack(side='left')
        self.language_dropdown.pack(side='left', padx=10)
                
        self.root.attributes('-topmost', self.always_on_top_var.get())

        # Load and display the image
        script_dir = os.path.dirname(__file__)
        image_path = os.path.join(script_dir, "junin.jfif")
        image = Image.open(image_path)
        image.thumbnail((400, 400), Image.LANCZOS)
        altura_complementar_window = 560
        self.root.geometry(f"{image.width + 50}x{image.height + altura_complementar_window}+100+100")
        self.photo = ImageTk.PhotoImage(image)
        self.label = tk.Label(root, image=self.photo, bg='white')
        self.label.pack(side="top", pady=10)

        # Chat display area
        self.chat_display = tk.Text(root, height=10, width=50, state='disabled', wrap='word', bg='lightgrey')
        self.chat_display.pack(pady=10, padx=20, fill='x')

        # User input area
        self.user_input = tk.Text(root, width=50, height=3)
        self.user_input.pack(pady=5, padx=20, fill='x')
        #self.user_input.bind("<Return>", self.send_message)
        self.user_input.bind("<Return>", self.send_message)
        self.user_input.bind("<Shift-Return>", self.new_line)
        self.user_input.focus_set()

        # Voice record button
        self.record_button = tk.Button(root, text="Clique para Gravar", command=self.toggle_recording, bg='blue', fg='white')
        self.record_button.pack(pady=5)
        # Register global hotkey for recording
        keyboard.add_hotkey('ctrl+alt', self.toggle_recording)

        # Hear response checkbox
        voice_config_frame = tk.Frame(root)
        voice_config_frame.pack(pady=5, padx=10, fill='x')
        self.hear_response_var = tk.BooleanVar(value=self.settings.get("hear_response", False))
        self.hear_response_checkbox = tk.Checkbutton(voice_config_frame, text="Ouvir a resposta", variable=self.hear_response_var)
        self.hear_response_checkbox.pack(pady=5)

        # Checkbox para ativar/desativar gravação com VAD
        self.vad_enabled_var = tk.BooleanVar(value=self.settings.get("vad_enabled", False))
        self.vad_checkbox = tk.Checkbutton(voice_config_frame, text="Ativar Gravação com VAD", variable=self.vad_enabled_var, command=self.vad_checkbox_callback)
        self.vad_checkbox.pack(pady=5)
        self.hear_response_checkbox.pack(side='left')
        self.vad_checkbox.pack(side='left', padx=10)

        # Voice engine selection dropdown
        voice_engine_frame = tk.Frame(root)
        voice_engine_frame.pack(pady=5, padx=10, fill='x')
        self.voice_engine_label = tk.Label(voice_engine_frame, text="Selecionar Motor de Voz:")
        self.voice_engine_label.pack(side='left')
        self.voice_engine_var = tk.StringVar(value=self.settings.get("selected_voice_engine", "tts-1"))
        self.voice_engine_dropdown = tk.OptionMenu(voice_engine_frame, self.voice_engine_var, "tts-1", "PC Voice", command=self.update_voice_dropdown)
        self.voice_engine_dropdown.pack(side='left', padx=10)

        # Voice selection dropdown
        voice_selection_frame = tk.Frame(root)
        voice_selection_frame.pack(pady=5, padx=10, fill='x')
        self.voice_label = tk.Label(voice_selection_frame, text="Selecionar Voz:")
        self.voice_label.pack(side='left')
        self.voice_var = tk.StringVar(value=self.settings.get("selected_voice", "alloy"))
        self.voice_dropdown = tk.OptionMenu(voice_selection_frame, self.voice_var, "alloy", "echo", "fable", "onyx", "nova", "shimmer")
        self.voice_dropdown.pack(side='left', padx=10)

        # Whisper selection dropdown
        whisper_mode_frame = tk.Frame(root)
        whisper_mode_frame.pack(pady=5, padx=10, fill='x')
        self.whisper_label = tk.Label(whisper_mode_frame, text="Selecionar Modo Whisper:")
        self.whisper_label.pack(side='left')
        self.whisper_var = tk.StringVar(value=self.settings.get("selected_whisper", "Online"))
        self.whisper_dropdown = tk.OptionMenu(whisper_mode_frame, self.whisper_var, "Online", "Local")
        self.whisper_dropdown.pack(side='left', padx=10)

        # PyAudio setup
        self.p = pyaudio.PyAudio()
        self.audio_stream = None
        self.is_recording = False
        self.is_recording_vad = False
        self.stop_event = threading.Event()
        #self.is_vad_active = False  # Para rastrear se a gravação VAD está ativa ou não
        self.vad_status_changed = True  # Para evitar múltiplas impressões
        self.chat_history = []

        self.interromper = False
        self.please_interrupt = True

        #global is_recording, last_detection_time, continuous_detection_start_time, threshold, is_vad_active, vad_status_changed

        self.update_voice_dropdown(self.voice_engine_var.get())
        self.update_language(self.language_var.get())

        # Save settings on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        #self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=8,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        output=True,
                        frames_per_buffer=CHUNK)
        
        # calibrando ruido
        if self.vad_enabled_var.get():
            self.threshold = self.calibrate_noise_threshold()
        else:
            self.threshold = 200

    def vad_checkbox_callback(self):
        if self.vad_enabled_var.get():
            print("VAD enabled")
            self.threshold = self.calibrate_noise_threshold()
        else:
            print("VAD disabled")
    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as file:
                return json.load(file)
        return {}

    def update_language(self, selected_language):
        if selected_language == "English":
            self.always_on_top_checkbox.config(text="Always on Top")
            self.record_button.config(text="Click to Record")
            self.hear_response_checkbox.config(text="Hear the response")
            self.voice_engine_label.config(text="Select Voice Engine:")
            self.voice_label.config(text="Select Voice:")
            self.whisper_label.config(text="Select Whisper Mode:")
            self.api_selection_label.config(text="Select API:")
            self.vad_checkbox.config(text="Activate VAD Recording")
        elif selected_language == "Português do Brasil":
            self.always_on_top_checkbox.config(text="Sempre no Topo")
            self.record_button.config(text="Clique para Gravar")
            self.hear_response_checkbox.config(text="Ouvir a resposta")
            self.voice_engine_label.config(text="Selecionar Motor de Voz:")
            self.voice_label.config(text="Selecionar Voz:")
            self.whisper_label.config(text="Selecionar Modo Whisper:")
            self.api_selection_label.config(text="Selecionar API:")
            self.vad_checkbox.config(text="Ativar Gravação VAD")

    def save_settings(self):
        print("Salvando preferencias.")
        self.settings["selected_voice"] = self.voice_var.get()
        self.settings["always_on_top"] = self.always_on_top_var.get()
        self.settings["selected_language"] = self.language_var.get()
        self.settings["hear_response"] = self.hear_response_var.get()
        self.settings["selected_voice_engine"] = self.voice_engine_var.get()
        self.settings["selected_whisper"] = self.whisper_var.get()
        self.settings["selected_api"] = self.api_selection_var.get()
        self.settings["vad_enabled"] = self.vad_enabled_var.get()
        with open(self.settings_file, 'w') as file:
            json.dump(self.settings, file)

    def toggle_always_on_top(self):
        self.root.attributes('-topmost', self.always_on_top_var.get())

    def update_voice_dropdown(self, selected_engine):
        # Initialize TTS engine for PC voice only when needed
        if selected_engine == "PC Voice" and not hasattr(self, 'tts_engine'):
            import pyttsx3
            self.tts_engine = pyttsx3.init()
        # Update the voice dropdown options based on the selected engine
        menu = self.voice_dropdown['menu']
        menu.delete(0, 'end')

        if selected_engine == "tts-1":
            voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        elif selected_engine == "PC Voice":
            if not hasattr(self, 'tts_engine'):
                import pyttsx3
                self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')
            voices = [(voice.id, voice.name.split(' - ')[-1]) for voice in voices]
        else:
            voices = []

        for voice in voices:
            if isinstance(voice, tuple):  # For PC Voice
                menu.add_command(label=voice[1], command=lambda v=voice[0]: self.voice_var.set(v))
            else:
                menu.add_command(label=voice, command=lambda v=voice: self.voice_var.set(v))

        # Update the selected voice to reflect the first available option if not already set
        if voices and self.voice_var.get() not in [v[0] if isinstance(v, tuple) else v for v in voices]:
            self.voice_var.set(voices[0][0] if isinstance(voices[0], tuple) else voices[0])

    def toggle_recording(self, event=None):
        if self.is_recording:
            self.stop_recording()
            self.record_button.config(text="Click to Record", bg='blue')
        elif self.is_recording_vad:
            self.is_recording_vad = False
            self.stop_recording()
            self.record_button.config(text="Click to Record", bg='blue')
        else:
            self.record_button.config(text="Gravando...", bg='red')
            self.stop_event.clear()
            self.vad_status_changed = True
            if self.vad_enabled_var.get():
                self.is_recording_vad = True
                print("Iniciando gravação com VAD...")
                threading.Thread(target=self.vad_recording).start()
            else:
                print("Iniciando gravação contínua...")
                self.is_recording = True
                self.start_recording()

    def start_recording(self):
        self.frames = []
        self.audio_stream = self.p.open(format=FORMAT,
                                        channels=CHANNELS,
                                        rate=RATE,
                                        input=True,
                                        frames_per_buffer=CHUNK)
        # Start a new thread to handle recording
        self.recording_thread = threading.Thread(target=self.record)
        self.recording_thread.start()

    def record(self):
        self.please_interrupt = True
        while self.is_recording:
            data = self.audio_stream.read(CHUNK)
            self.frames.append(data)

        # Stop the audio stream after recording ends
        self.audio_stream.stop_stream()
        self.audio_stream.close()

        self.please_interrupt = False

        # Convert recorded audio to bytes
        audio_data = b''.join(self.frames)
        audio_file = io.BytesIO()
        with wave.open(audio_file, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(audio_data)
        audio_file.name = "output.wav"

        # Use Whisper for speech-to-text
        transcript = self.transcribe_audio(audio_file)
        
        print("Transcrição", transcript)
        if transcript:
            self.display_message("You: " + transcript)
            response = self.get_response(transcript)
            self.display_message("Bot: " + response)
            if self.hear_response_var.get():
                self.speak_response(response)

    def stop_recording(self):
        self.is_recording = False
        self.stop_event.set()

    def transcribe_audio(self, audio_file):
        try:
            if self.whisper_var.get() == "Local":
                import whisper
                model = whisper.load_model("base")
                audio_file.seek(0)
                audio_data = np.frombuffer(audio_file.read(), np.int16).astype(np.float32) / 32768.0  # Convert to float32 for Whisper
                result = model.transcribe(audio_data)
                return result.get("text", "")
            else:
                audio_file.seek(0)  # Ensure the file pointer is at the start
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                return response.text
        except Exception as e:
            print("Error during transcription:", e)
            return ""

    def get_response(self, user_message):
        if self.api_selection_var.get() == "OpenAI":
            return self.get_response_openai(user_message)
        else:
            return self.get_response_ollama(user_message)

    def get_response_openai(self, user_message):
        try:
            # Get the dynamically constructed system prompt from TaskManager
            system_prompt = task_manager.build_system_prompt()

            if len(self.chat_history) == 0:
                self.chat_history.append({"role": "system", "content": system_prompt})
            else:
                self.chat_history[0] = {"role": "system", "content": system_prompt}
            
            self.chat_history.append({"role": "user", "content": user_message})

            #print("SYSTEM\n\n", system_prompt)
            #print("HIST", self.get_chat_history())

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=self.get_chat_history(),
                #messages=[
                #    {"role": "system", "content": system_prompt},
                #    {"role": "assistant", "content": self.get_chat_history()},
                #    {"role": "user", "content": user_message}
                #]
            )

            json_response = json.loads(response.choices[0].message.content)
            print("json_response", json_response)

            response_type = json_response.get('type')
            response_content = json_response.get('content')

            # Use TaskManager to execute the appropriate task
            resposta_task_manager = task_manager.execute_task(response_type, response_content)

            self.chat_history.append({"role": "assistant", "content": resposta_task_manager})

            return resposta_task_manager

        except Exception as e:
            return f"Sorry, I couldn't get a response. Please try again later. Error: {e}"

    def get_response_ollama(self, user_message):
        try:
            client = OpenAI(api_key="nada", base_url="http://localhost:11434/v1/")
            response = client.chat.completions.create(
                model="llama3.2:1b",
                messages=[
                    {"role": "user", "content": user_message}
                ],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Sorry, I couldn't get a response from Ollama. Please try again later. Error: {e}"

    def get_chat_history(self):
        #return "\n".join(self.chat_history)
        return self.chat_history

    def speak_response(self, response_text):
        try:
            selected_engine = self.voice_engine_var.get()
            selected_voice = self.voice_var.get()

            if selected_engine == "tts-1":
                with client.audio.speech.with_streaming_response.create(
                        model="tts-1",
                        voice=selected_voice,
                        input=response_text,
                        response_format="pcm"
                ) as response:
                    for chunk in response.iter_bytes(1024):
                        self.stream.write(chunk)
                        
                        if self.please_interrupt:
                            print("INTERROMPEU")
                            break
                    self.interromper = False
            elif selected_engine == "PC Voice":
                self.tts_engine.setProperty('voice', selected_voice)
                self.tts_engine.say(response_text)
                self.tts_engine.runAndWait()
        except Exception as e:
            print("Error during text-to-speech:", e)

    def display_message(self, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, message + "\n")
        #self.chat_history.append(message)
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)

    def send_message(self, event=None):
        user_message = self.user_input.get("1.0", tk.END).strip()
        if user_message:
            self.display_message("You: " + user_message)
            self.user_input.delete("1.0", tk.END)
            response = self.get_response(user_message)

            if response != "":
                self.display_message("Bot: " + response)
                if self.hear_response_var.get():
                    self.speak_response(response)

    def new_line(self, event=None):
        self.user_input.insert(tk.INSERT, "\n")
        return "break"  # Prevent the default behavior of "Enter"

    def on_closing(self):
        try:
            keyboard.unhook_all_hotkeys()
            if self.voice_engine_var.get() == "PC Voice":
                self.tts_engine.stop()  # Stop the TTS engine to release resources
            self.save_settings()
        except PermissionError:
            print("Permission denied when trying to save settings.")
        finally:
            self.root.destroy()

    # Função de calibração do ruído ambiente
    def calibrate_noise_threshold(self):
        """Função para calcular a média móvel do ruído ambiente e definir o threshold."""
        print("Calibrando o som ambiente. Permaneça em silêncio durante esta calibração...")

        stream = self.p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        volume_history = deque(maxlen=MOVING_AVERAGE_WINDOW)

        for _ in range(MOVING_AVERAGE_WINDOW):
            # Lê os dados de áudio do microfone
            data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
            # Calcula a intensidade do som
            volume = np.linalg.norm(data)
            if volume < NOISE_FLOOR:
                volume = 0  # Considera como nenhum som detectado
            volume_history.append(volume)
        
        stream.stop_stream()
        stream.close()
        
        average_volume = np.mean(volume_history)
        threshold = average_volume * VOLUME_MULTIPLIER
        print(f"Calibração completa. Som ambiente fixado em: {threshold:.2f}")
        return threshold
    
    # Função para gravação com detecção VAD
    def vad_recording(self):
        #global is_recording, last_detection_time, continuous_detection_start_time, threshold, is_vad_active, vad_status_changed
        stream = self.p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        last_detection_time = None
        continuous_detection_start_time = None
        is_vad_active = False  # Inicialmente, a gravação VAD não está ativa

        while self.is_recording_vad and not self.stop_event.is_set():
            data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
            volume = np.linalg.norm(data)

            if volume < NOISE_FLOOR:
                volume = 0
            
            if volume > self.threshold:
                if continuous_detection_start_time is None:
                    continuous_detection_start_time = time.time()
                else:
                    elapsed_detection_time = time.time() - continuous_detection_start_time
                    if elapsed_detection_time >= DETECTION_TIME:
                        if not is_vad_active:
                            print("Som detectado! Gravando...")
                            
                            if self.please_interrupt:
                                self.interromper = True
                            self.is_recording = True
                            
                            self.start_recording()
                            #update_button_state("Parar Gravação", "Recording.TButton")
                            is_vad_active = True  # A gravação está ativa
                        last_detection_time = time.time()
                        vad_status_changed = False
            else:
                continuous_detection_start_time = None
            
            if last_detection_time:
                elapsed_time = time.time() - last_detection_time
                if elapsed_time > RECORD_TIME_AFTER_DETECTION and is_vad_active:
                    print("Som finalizado. Aguardando...")
                    #self.stop_recording()
                    #self.stop_event.set()
                    self.is_recording = False
                    #update_button_state("Aguardando Voz", "TButton")
                    is_vad_active = False  # A gravação está inativa
                    vad_status_changed = True

        stream.stop_stream()
        stream.close()

    

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()
