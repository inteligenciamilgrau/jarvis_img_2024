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
#import mss
#import base64
#from io import BytesIO
#import re
#import matplotlib.pyplot as plt
#import pyautogui
#import replicate
import numpy as np
from task_manager import TaskManager

# Load environment variables
load_dotenv()

# Audio recording settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

client = OpenAI()
task_manager = TaskManager()

class ChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JUNIN")
        self.root.configure(bg='white')
        
        # Load saved settings
        self.settings_file = os.path.join(os.path.expanduser("~"), "junin_settings.json")
        self.settings = self.load_settings()
        
        # Configure language and update UI
        self.language_var = tk.StringVar(value=self.settings.get("selected_language", "English"))
        
        # Add selection for OpenAI or Ollama
        self.api_selection_var = tk.StringVar(value=self.settings.get("selected_api", "OpenAI"))
        api_selection_frame = tk.Frame(root)
        api_selection_frame.pack(pady=5, fill='x')
        self.api_selection_label = tk.Label(api_selection_frame, text="Selecionar API:")
        self.api_selection_label.pack(side='left')
        self.api_selection_dropdown = tk.OptionMenu(api_selection_frame, self.api_selection_var, "OpenAI", "Ollama")
        self.api_selection_dropdown.pack(side='left', padx=10)
        
        # Remove overrideredirect to restore taskbar icon
        # self.root.overrideredirect(True)

        # Add checkbox for "Always on Top"
        self.always_on_top_var = tk.BooleanVar(value=self.settings.get("always_on_top", True))
        always_on_top_frame = tk.Frame(root)
        always_on_top_frame.pack(pady=5, fill='x')
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
        self.root.geometry(f"{image.width + 50}x{image.height + 500}+100+100")
        self.photo = ImageTk.PhotoImage(image)
        self.label = tk.Label(root, image=self.photo, bg='white')
        self.label.pack(side="top", pady=10)

        # Chat display area
        self.chat_display = tk.Text(root, height=10, width=50, state='disabled', wrap='word', bg='lightgrey')
        self.chat_display.pack(pady=10)

        # User input area
        self.user_input = tk.Entry(root, width=50)
        self.user_input.pack(pady=5)
        self.user_input.bind("<Return>", self.send_message)

        # Voice record button
        self.record_button = tk.Button(root, text="Clique para Gravar", command=self.toggle_recording, bg='blue', fg='white')
        self.record_button.pack(pady=5)
        # Register global hotkey for recording
        keyboard.add_hotkey('ctrl+alt', self.toggle_recording)

        # Hear response checkbox
        self.hear_response_var = tk.BooleanVar(value=self.settings.get("hear_response", False))
        self.hear_response_checkbox = tk.Checkbutton(root, text="Ouvir a resposta", variable=self.hear_response_var)
        self.hear_response_checkbox.pack(pady=5)

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
        self.chat_history = []

        self.update_voice_dropdown(self.voice_engine_var.get())
        self.update_language(self.language_var.get())

        # Save settings on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=8,
                        channels=1,
                        rate=24_000,
                        output=True)

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
        elif selected_language == "Português do Brasil":
            self.always_on_top_checkbox.config(text="Sempre no Topo")
            self.record_button.config(text="Clique para Gravar")
            self.hear_response_checkbox.config(text="Ouvir a resposta")
            self.voice_engine_label.config(text="Selecionar Motor de Voz:")
            self.voice_label.config(text="Selecionar Voz:")
            self.whisper_label.config(text="Selecionar Modo Whisper:")

    def save_settings(self):
        self.settings["selected_voice"] = self.voice_var.get()
        self.settings["always_on_top"] = self.always_on_top_var.get()
        self.settings["selected_language"] = self.language_var.get()
        self.settings["hear_response"] = self.hear_response_var.get()
        self.settings["selected_voice_engine"] = self.voice_engine_var.get()
        self.settings["selected_whisper"] = self.whisper_var.get()
        self.settings["selected_api"] = self.api_selection_var.get()
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
        else:
            self.is_recording = True
            self.record_button.config(text="Gravando...", bg='red')
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
        while self.is_recording:
            data = self.audio_stream.read(CHUNK)
            self.frames.append(data)

        # Stop the audio stream after recording ends
        self.audio_stream.stop_stream()
        self.audio_stream.close()

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

            print("SYSTEM\n\n", system_prompt)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )

            json_response = json.loads(response.choices[0].message.content)
            print("json_response", json_response)

            response_type = json_response.get('type')
            response_content = json_response.get('content')

            # Use TaskManager to execute the appropriate task
            return task_manager.execute_task(response_type, response_content)

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
        return "\n".join(self.chat_history)

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
            elif selected_engine == "PC Voice":
                self.tts_engine.setProperty('voice', selected_voice)
                self.tts_engine.say(response_text)
                self.tts_engine.runAndWait()
        except Exception as e:
            print("Error during text-to-speech:", e)

    def display_message(self, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_history.append(message)
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)

    def send_message(self, event=None):
        user_message = self.user_input.get().strip()
        if user_message:
            self.display_message("You: " + user_message)
            self.user_input.delete(0, tk.END)
            response = self.get_response(user_message)
            self.display_message("Bot: " + response)
            if self.hear_response_var.get():
                self.speak_response(response)

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

    

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()