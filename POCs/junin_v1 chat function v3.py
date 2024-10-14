import tkinter as tk
from tkinter import PhotoImage
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
import wave
import pyaudio
import mss
import base64
from io import BytesIO
import re
import matplotlib.pyplot as plt
import pyautogui
import replicate

# Load environment variables
load_dotenv()

# Audio recording settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

client = OpenAI()

class ChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JUNIN")
        self.root.configure(bg='white')
        
        # Load saved settings
        self.settings_file = "settings.json"
        self.settings = self.load_settings()
        
        # Remove overrideredirect to restore taskbar icon
        # self.root.overrideredirect(True)

        # Add checkbox for "Always on Top"
        self.always_on_top_var = tk.BooleanVar(value=self.settings.get("always_on_top", True))
        self.always_on_top_checkbox = tk.Checkbutton(root, text="Always on Top", variable=self.always_on_top_var, command=self.toggle_always_on_top)
        self.always_on_top_checkbox.pack(pady=5)
        self.root.attributes('-topmost', self.always_on_top_var.get())

        # Load and display the image
        image = Image.open("junin.jfif")
        image.thumbnail((400, 400), Image.LANCZOS)
        self.root.geometry(f"{image.width + 50}x{image.height + 450}+100+100")
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
        self.record_button = tk.Button(root, text="Click to Record", command=self.toggle_recording, bg='blue', fg='white')
        self.record_button.pack(pady=5)
        # Register global hotkey for recording
        keyboard.add_hotkey('ctrl+alt', self.toggle_recording)

        # Hear response checkbox
        self.hear_response_var = tk.BooleanVar(value=self.settings.get("hear_response", False))
        self.hear_response_checkbox = tk.Checkbutton(root, text="Hear the response", variable=self.hear_response_var)
        self.hear_response_checkbox.pack(pady=5)

        # Voice selection dropdown
        self.voice_var = tk.StringVar(value=self.settings.get("selected_voice", "alloy"))
        self.voice_label = tk.Label(root, text="Select Voice:")
        self.voice_label.pack(pady=5)
        self.voice_dropdown = tk.OptionMenu(root, self.voice_var, "alloy", "echo", "fable", "onyx", "nova", "shimmer")
        self.voice_dropdown.pack(pady=5, padx=10)

        # PyAudio setup
        self.p = pyaudio.PyAudio()
        self.audio_stream = None
        self.is_recording = False
        self.chat_history = []

        # Save settings on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as file:
                return json.load(file)
        return {}

    def save_settings(self):
        self.settings["selected_voice"] = self.voice_var.get()
        self.settings["always_on_top"] = self.always_on_top_var.get()
        self.settings["hear_response"] = self.hear_response_var.get()
        with open(self.settings_file, 'w') as file:
            json.dump(self.settings, file)

    def toggle_always_on_top(self):
        self.root.attributes('-topmost', self.always_on_top_var.get())

    def toggle_recording(self, event=None):
        if self.is_recording:
            self.stop_recording()
            self.record_button.config(text="Click to Record", bg='blue')
        else:
            self.is_recording = True
            self.record_button.config(text="Recording...", bg='red')
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

        # Use OpenAI's speech-to-text
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
            audio_file.seek(0)  # Ensure the file pointer is at the start
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return response.text
        except Exception as e:
            print("Error during transcription:", e)
            return ""

    def get_chat_history(self):
        return "\n".join(self.chat_history)

    def get_response(self, user_message):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format= { "type": "json_object" },
                messages=[
                    {"role": "system", "content": """You are a helpful assistant.
                     Your answer must be a JSON.
                     If it was a regular question, the type is 'normal'.
                     If the user ask to click or to point to something, the type is 'click'.
                     The click content must be always in english starting with 'point to the...'
                     If the user ask about the screen or image, the type is 'image' and pass the question as content.

                     Examples of responses:
                     {'type': 'normal', 'content': 'The response to the user'}

                     {'type': 'click', 'content': 'point to the ...'}

                     {'type': 'image', 'content': 'Question about the image'}
                     """},
                    {"role": "assistant", "content": self.get_chat_history()},
                    {"role": "user", "content": user_message}
                ]
            )

            json_response = json.loads(response.choices[0].message.content)
            if json_response.get('type') == 'normal':
                return json_response.get('content')
            elif json_response.get('type') == 'image':
                #print("Image:", json_response.get('content'))
                resposta = self.ler_tela(json_response.get('content'))
                return resposta
            else:
                print("Click:", json_response.get('content'))
                self.click_on(json_response.get('content'))
                return json_response.get('content')

        except Exception as e:
            return f"Sorry, I couldn't get a response. Please try again later. Error: {e}"

    def speak_response(self, response_text):
        try:
            selected_voice = self.voice_var.get()
            response = client.audio.speech.create(
                model="tts-1",
                voice=selected_voice,
                input=response_text,
                response_format="wav"
            )
            audio_data = response.content
            audio_file = io.BytesIO(audio_data)
            audio_file.seek(0)

            # Play the WAV audio using PyAudio
            wf = wave.open(audio_file, 'rb')
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True)
            data = wf.readframes(CHUNK)
            while data:
                stream.write(data)
                data = wf.readframes(CHUNK)

            stream.stop_stream()
            stream.close()
            p.terminate()
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
        keyboard.unhook_all_hotkeys()
        self.save_settings()
        self.root.destroy()

    def ler_tela(self, message):
        #segundo_monitor_pixels = 1920
        image = self.capture_and_show_image_from_second_monitor(1920, 1080)
        buffered = BytesIO()
        image.save(buffered, format="PNG")  # Save image in buffer as PNG format
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": message},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/png;base64," + base64_image,
                            }
                        },
                    ],
                }
            ],
            max_tokens=300,
        )

        print("Resposta:", response.choices[0].message.content)
        return response.choices[0].message.content

    def click_on(self, click_this):
        segundo_monitor_pixels = 1920
        image = self.capture_and_show_image_from_second_monitor(1920, 1080)
        buffered = BytesIO()
        image.save(buffered, format="PNG")  # Save image in buffer as PNG format
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        print("Chamando replicate")
        # Run the model and get the output
        output = replicate.run(
            "zsxkib/molmo-7b:76ebd700864218a4ca97ac1ccff068be7222272859f9ea2ae1dd4ac073fa8de8",
            input={
                "text": click_this,
                "image": "data:image/png;base64," + base64_image,
                "top_k": 100,
                "top_p": 1,
                "temperature": 1,
                "length_penalty": 1,
                "max_new_tokens": 1000
            }
        )

        # Print the output to check its structure
        print("Output:", output)

        # Pattern to extract x and y coordinates from the output, whether in <point> or <points> format
        pattern = r'x\d*="([\d.]+)" y\d*="([\d.]+)"'
        matches = re.findall(pattern, output)

        # Convert the extracted strings into float values and store as a list of tuples
        coordinates = [(float(x), float(y)) for x, y in matches]

        # Print the coordinates
        print("Coordinates of points:")
        for i, (x, y) in enumerate(coordinates):
            print(f"Point {i + 1}: ({x + segundo_monitor_pixels}, {y})")

        # Convert coordinates from relative to pixel positions
        width, height = image.size
        x_coords = [x / 100 * width for x, y in coordinates]
        y_coords = [y / 100 * height for x, y in coordinates]

        # After extracting the coordinates
        for x, y in zip(x_coords, y_coords):
            pyautogui.moveTo(x + segundo_monitor_pixels, y, duration=0.5)  # Move the mouse cursor to the coordinates
            pyautogui.click()  # Click the mouse at the coordinates

        # Plot points on the image
        plotar = False
        if plotar:
            # Display the image and the points
            fig, ax = plt.subplots()
            ax.imshow(image)

            ax.scatter(x_coords, y_coords, color='black', s=400, marker='o')

            print("coords", x_coords, y_coords, image.size)

            with mss.mss() as sct:
                # Get the second monitor's position
                second_monitor = sct.monitors[2]
                x_pos, y_pos = second_monitor["left"], second_monitor["top"]

                # Set the figure position on the second monitor
                fig.canvas.manager.window.wm_geometry(f"+{x_pos}+{y_pos + 600}")

                # Show plot with points
                plt.title("Coordinates on Image")
                plt.show()
        return output
    
    def capture_and_show_image_from_second_monitor(self, width=400, height=400):
        # Initialize mss for screen capturing
        with mss.mss() as sct:
            # Get the monitor information
            monitors = sct.monitors
            
            # Check if there's a second monitor available
            if len(monitors) < 2:
                raise ValueError("No second monitor detected.")
            
            # Monitor 2 is at index 2 (index 1 is the primary monitor)
            second_monitor = monitors[2]
            
            # Define the region to capture: 400x400 starting from the top-left corner of the second monitor
            capture_region = {
                "top": second_monitor["top"],
                "left": second_monitor["left"],
                "width": width,
                "height": height
            }
            
            # Capture the screen in the defined region
            screenshot = sct.grab(capture_region)
            
            # Convert it to a PIL Image
            return Image.frombytes("RGB", screenshot.size, screenshot.rgb)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()