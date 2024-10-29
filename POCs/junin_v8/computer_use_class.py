import queue
import threading
import anthropic
import mss
import base64
import io
from dotenv import load_dotenv
import mss.tools
import pyautogui
import keyboard
from PIL import Image
load_dotenv()

# Audio recording settings
CHUNK = 1024
CHANNELS = 1
RATE = 24_000

class AnthropicToolHandler:
    def __init__(self, monitor_index=1, monitor_offset=None, falar=False):
        self.monitor_index = monitor_index
        self.monitor_offset = monitor_offset if monitor_offset else [0, 0]
        self.client = anthropic.Anthropic()
        self.messages = []
        self.falar = falar

        self.tts = TextToSpeech()

        falar_muito = False
        if falar_muito:
            from openai import OpenAI
            import pyaudio
            self.client_openai = OpenAI()
            # PyAudio setup
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(format=8,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            output=True,
                            frames_per_buffer=CHUNK)

    def perguntando(self, messages):
        response = self.client.beta.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            tools=[
                {
                    "type": "computer_20241022",
                    "name": "computer",
                    "display_width_px": 1024,
                    "display_height_px": 768,
                    "display_number": 1,
                },
            ],
            messages=messages,
            betas=["computer-use-2024-10-22"],
        )
        #print("Resposta:", response)
        return response

    def grab_screen_of_monitor(self):
        with mss.mss() as sct:
            monitors = sct.monitors

            if self.monitor_index < 1 or self.monitor_index >= len(monitors):
                raise ValueError(f"Invalid monitor index: {self.monitor_index}. Available monitors: 1 to {len(monitors) - 1}")

            monitor = monitors[self.monitor_index]
            screenshot = sct.grab(monitor)

            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            img = img.resize((1024, 768))

            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG')
            img_buffer.seek(0)

            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            return img_base64

    # Function to call the `speak_response` method in a new thread
    def speak_response_thread(self, response_text):
        thread = threading.Thread(target=self.speak_response, args=(response_text,))
        thread.start()
        
    def speak_response(self, response_text):
        try:
            selected_engine = "tts-1" #self.voice_engine_var.get()
            selected_voice = "alloy" # self.voice_var.get()

            if selected_engine == "tts-1":
                with self.client_openai.audio.speech.with_streaming_response.create(
                        model="tts-1",
                        voice=selected_voice,
                        input=response_text,
                        response_format="pcm"
                ) as response:
                    for chunk in response.iter_bytes(1024):
                        self.stream.write(chunk)
        except Exception as e:
            print("Error during text-to-speech:", e)

    def template_resposta_tool(self, mensagem, tool_id):
        return {
            "role": "user",
            "content": [
                {"tool_use_id": tool_id, "type": "tool_result"},
                {"type": "text", "text": mensagem}
            ]
        }

    def handle_tool_response(self, response):
        action = response.content[1].input.get('action')
        tool_id = response.content[1].id
        output_message = ""

        if self.falar:
            #self.tts.enqueue_speak(response.content[0].text)
            pass

        if action == "screenshot":
            image_base64 = self.grab_screen_of_monitor()
            tool_response = {
                "role": "user",
                "content": [
                    {"tool_use_id": tool_id, "type": "tool_result"},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_base64}}
                ]
            }
            self.messages.append(tool_response)
            print("Resposta SCREENSHOT:", response.content[0].text, "\n")
            if self.falar:
                #self.tts.enqueue_speak(response.content[0].text)
                pass
            output_message = "Screenshot realizado."

        elif action == "mouse_move":
            new_coordinate = self.convert_coordinate((1024, 768), (1920, 1080), response.content[1].input['coordinate'])
            if self.monitor_index == 2:
                new_coordinate[0] += self.monitor_offset[0]
            pyautogui.moveTo(new_coordinate)
            self.messages.append(self.template_resposta_tool("Mouse Movido", tool_id))
            print("Resposta MOVE:", response.content[0].text, "\n")
            output_message = "Mouse movido."
            if self.falar:
                self.tts.enqueue_speak(response.content[0].text)
                pass

        elif action == "left_click":
            pyautogui.click(button='left')
            self.messages.append(self.template_resposta_tool("Clique esquerdo realizado", tool_id))
            print("Resposta Left Click:", response.content[0].text, "\n")
            output_message = "Clique esquerdo realizado."

        elif action == "type":
            pyautogui.write(response.content[1].input['text'])
            self.messages.append(self.template_resposta_tool("Texto escrito", tool_id))
            print("Resposta Type:", response.content[0].text, "\n")
            output_message = "Texto escrito."

        elif action == "key":
            key_text = response.content[1].input['text']
            if key_text == "Return":
                pyautogui.press("return")
            else:
                keyboard.press_and_release(key_text)
            self.messages.append(self.template_resposta_tool(f"Apertado {key_text}", tool_id))
            print("Resposta Key:", response.content[0].text, "\n")
            output_message = f"Apertado {key_text}."

        elif action == "left_click_drag":
            coord = response.content[1].input['coordinate']
            self.left_click_drag(coord[0], coord[1])
            self.messages.append(self.template_resposta_tool("Clique esquerdo e arrasta realizado", tool_id))
            print("Resposta Left Click Drag:", response.content[0].text, "\n")
            output_message = "Clique esquerdo e arrasta realizado."

        elif action == "right_click":
            pyautogui.click(button='right')
            self.messages.append(self.template_resposta_tool("Clique direito realizado", tool_id))
            print("Resposta Right Click:", response.content[0].text, "\n")
            output_message = "Clique direito realizado."

        elif action == "middle_click":
            pyautogui.click(button='middle')
            self.messages.append(self.template_resposta_tool("Clique do meio realizado", tool_id))
            print("Resposta Middle Click:", response.content[0].text, "\n")
            output_message = "Clique do meio realizado."

        elif action == "double_click":
            pyautogui.doubleClick()
            self.messages.append(self.template_resposta_tool("Clique duplo realizado", tool_id))
            print("Resposta Double Click:", response.content[0].text, "\n")
            output_message = "Clique duplo realizado."

        elif action == "cursor_position":
            x, y = pyautogui.position()
            self.messages.append(self.template_resposta_tool(f"Posição do mouse: x={x}, y={y}", tool_id))
            print("Resposta Cursor Position:", response.content[0].text, "\n")
            output_message = f"Posição do mouse: x={x}, y={y}."

        return output_message

    def convert_coordinate(self, old_resolution, new_resolution, point):
        old_width, old_height = old_resolution
        new_width, new_height = new_resolution
        x, y = point

        new_x = x * new_width / old_width
        new_y = y * new_height / old_height

        return [int(new_x), int(new_y)]

    def left_click_drag(self, x, y):
        pyautogui.mouseDown(button='left')
        pyautogui.moveTo(x, y, duration=0.5)
        pyautogui.mouseUp(button='left')

    def handle_chat(self, question):
        self.messages.append({"role": "user", "content": question})
        response = self.perguntando(self.messages)
        print("Resposta:", response.content[0].text, "\n")
        self.messages.append({"role": "assistant", "content": response.content})
        output = [response.content[0].text]

        if self.falar:
            #self.tts.enqueue_speak(response.content[0].text)
            pass

        while response.stop_reason == "tool_use":
            output_message = self.handle_tool_response(response)
            output.append(output_message)
            response = self.perguntando(self.messages)
            print("Resposta Tool Use:", response.content[0].text, "\n")
            output.append(response.content[0].text)
            self.messages.append({"role": "assistant", "content": response.content})

        return output

class TextToSpeech:
    def __init__(self):
        from openai import OpenAI
        import pyaudio
        self.client_openai = OpenAI()
        # PyAudio setup
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=8,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        output=True,
                        frames_per_buffer=CHUNK)
        self.queue = queue.Queue()  # Fila para gerenciar as mensagens de fala
        self.lock = threading.Lock()  # Lock para sincronização (caso necessário)
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def speak_response(self, response_text):
        try:
            selected_engine = "tts-1"  # self.voice_engine_var.get()
            selected_voice = "alloy"  # self.voice_var.get()

            if selected_engine == "tts-1":
                with self.client_openai.audio.speech.with_streaming_response.create(
                        model="tts-1",
                        voice=selected_voice,
                        input=response_text,
                        response_format="pcm"
                ) as response:
                    for chunk in response.iter_bytes(1024):
                        self.stream.write(chunk)
        except Exception as e:
            print("Error during text-to-speech:", e)

    def enqueue_speak(self, response_text):
        self.queue.put(response_text)

    def _process_queue(self):
        while True:
            # Obtém o próximo texto da fila (bloqueia se a fila estiver vazia)
            response_text = self.queue.get()
            if response_text is None:
                break  # Encerrar a thread quando receber um comando para finalizar
            
            # Executa a função de fala em uma nova thread, sem bloquear o resto do código
            thread = threading.Thread(target=self.speak_response, args=(response_text,))
            thread.start()
            thread.join()  # Aguarda a finalização da thread para pegar o próximo na fila


def main():
    handler = AnthropicToolHandler(monitor_index=2, monitor_offset=[1920, 0], falar=True)
    result = handler.handle_chat("Clique no instagram?")
    print(result)

if __name__ == "__main__":
    main()
