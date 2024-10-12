import tkinter as tk
from tkinter import PhotoImage
from PIL import Image, ImageTk
import pyaudio
import threading
from openai import OpenAI
import wave
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Audio recording settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

import time
client = OpenAI()

class MicRecorderApp:
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_motion(self, event):
        x = event.x_root - self.x
        y = event.y_root - self.y
        self.root.geometry(f'+{x}+{y}')
    def __init__(self, root):
        self.root = root
        self.root.title("Mic Recorder")
        
        self.root.configure(bg='white')
        self.root.overrideredirect(True)
        # Add a close button
        
        
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.on_motion)  # Remove title bar to make it floating
        self.root.attributes('-topmost', True)  # Keep on top
        self.root.lift()  # Ensure it's always on top
        self.root.after(10, self.keep_on_top)  # Keep it on top continuously
        self.is_recording = False
        
        # Load and display the PNG image
        image = Image.open("junin.jfif")
        # Resize image to maintain aspect ratio
        image.thumbnail((400, 400), Image.LANCZOS)
        self.root.geometry(f"{image.width}x{image.height + 50}+100+100")
        self.photo = ImageTk.PhotoImage(image)
        # Resize image to maintain aspect ratio
        image.thumbnail((400, 400), Image.LANCZOS)
        
        self.photo = ImageTk.PhotoImage(image)
        # Resize image to maintain aspect ratio
        image.thumbnail((400, 400), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(image)
        self.label = tk.Label(root, image=self.photo, bg='white')
        self.label.pack(side="top", pady=10)
        # Add a close button
        close_button = tk.Button(root, text='X', command=self.root.quit, bg='red', fg='white')
        close_button.place(x=image.width - 30, y=10)

        # Add the record button
        self.record_button = tk.Button(root, text="Start Recording", command=self.toggle_recording, bg='red', fg='white')
        self.record_button.pack(before=self.label, pady=10)

        # PyAudio
        self.p = pyaudio.PyAudio()
        self.audio_stream = None

    def keep_on_top(self):
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(10, self.keep_on_top)

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
            self.record_button.config(text="Start Recording", bg='red')
        else:
            self.is_recording = True
            self.record_button.config(text="Stop Recording", bg='green')
            self.start_recording()
            self.root.after(20000, self.stop_recording)  # Stop after 20 seconds

    def stop_recording(self):
        self.is_recording = False
        self.record_button.config(text="Start Recording", bg='red')

    def start_recording(self):
        self.frames = []
        self.audio_stream = self.p.open(format=FORMAT,
                                        channels=CHANNELS,
                                        rate=RATE,
                                        input=True,
                                        frames_per_buffer=CHUNK)
        self.frames = []

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

        # Use OpenAI's speech-to-text
        transcript = self.transcribe_audio(audio_file)
        print("Transcript:", transcript)

    def transcribe_audio(self, audio_file):
        try:
            audio_file.seek(0)  # Ensure the file pointer is at the start
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return response.text
        except Exception as e:
            print("Error during transcription:", e)
            return ""

if __name__ == "__main__":
    root = tk.Tk()
    app = MicRecorderApp(root)
    root.mainloop()