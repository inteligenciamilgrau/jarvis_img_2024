# Import necessary libraries
import asyncio  # For asynchronous programming
import base64  # For encoding/decoding audio data
import json  # For handling JSON data
import os  # For interacting with the operating system
import websockets  # For WebSocket communication
import sounddevice as sd  # For audio input/output
import numpy as np  # For numerical operations
import threading  # For thread-based parallelism
from typing import Dict, Any, Callable
from dotenv import load_dotenv, set_key
load_dotenv()
# Class to handle audio output
class AudioOut:
    def __init__(self, sample_rate, channels, output_device_id):
        # Initialize audio output parameters
        self.sample_rate = sample_rate
        self.channels = channels
        self.output_device_id = output_device_id
        self.audio_buffer = bytearray()  # Buffer to store audio data
        self.audio_buffer_lock = asyncio.Lock()  # Lock for thread-safe access to the buffer
        self.audio_playback_queue = asyncio.Queue()  # Queue for audio playback
        self.stream = None  # Audio output stream

    async def start(self):
        # Start the audio output stream
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='int16',
            callback=self._audio_callback,
            device=self.output_device_id,
            latency='low'
        )
        self.stream.start()
        await self._playback_loop()  # Start the playback loop

    def _audio_callback(self, outdata, frames, time, status):
        # Callback function for the audio output stream
        if status:
            print(status)
        bytes_to_read = frames * self.channels * 2
        with threading.Lock():
            # Read data from the buffer and write to the output
            if len(self.audio_buffer) >= bytes_to_read:
                data = self.audio_buffer[:bytes_to_read]
                del self.audio_buffer[:bytes_to_read]
            else:
                # If not enough data, pad with zeros
                data = self.audio_buffer + bytes([0] * (bytes_to_read - len(self.audio_buffer)))
                self.audio_buffer.clear()
        outdata[:] = np.frombuffer(data, dtype='int16').reshape(-1, self.channels)

    async def _playback_loop(self):
        # Continuous loop to process audio chunks from the queue
        while True:
            chunk = await self.audio_playback_queue.get()
            if chunk is None:
                continue
            async with self.audio_buffer_lock:
                self.audio_buffer.extend(chunk)

    async def add_audio(self, chunk):
        # Add audio chunk to the playback queue
        await self.audio_playback_queue.put(chunk)

    async def clear_audio(self):
        # Clear the audio playback queue and buffer
        while not self.audio_playback_queue.empty():
            try:
                await self.audio_playback_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        async with self.audio_buffer_lock:
            self.audio_buffer.clear()

    async def stop(self):
        # Stop and close the audio output stream
        if self.stream:
            self.stream.stop()
            self.stream.close()

# Tool registry to manage available tools
class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, func: Callable):
        self.tools[name] = func

    def get_tool(self, name: str) -> Callable:
        return self.tools.get(name)

    def get_tool_definitions(self) -> list:
        return [
            {
                "type": "function",
                "name": name,
                "description": func.__doc__,
                "parameters": getattr(func, "parameters", {})
            }
            for name, func in self.tools.items()
        ]
    
# Class to handle the main audio streaming functionality
class AudioStreamer:
    def __init__(self, api_key, input_device_id, output_device_id):
        # Initialize the audio streamer with API key and device IDs
        self.api_key = api_key
        self.input_device_id = input_device_id
        self.output_device_id = output_device_id
        self.url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        self.sample_rate = 24000
        self.chunk_duration = 0.02  # 20ms chunks
        self.audio_format = 'int16'
        self.channels = 1
        self.should_record = True
        self.audio_out = AudioOut(self.sample_rate, self.channels, self.output_device_id)
        self.tool_registry = ToolRegistry()
    
    def register_tool(self, name: str, func: Callable):
        self.tool_registry.register_tool(name, func)
        print(f"Registered tool: {name}")  # Add this line for debugging

    def print_registered_tools(self):
        print("Registered tools:")
        for name in self.tool_registry.tools.keys():
            print(f" - {name}")

    async def start(self):
        # Start the audio streaming session
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1",
        }

        # Add this line before connecting to the API
        self.print_registered_tools()

        async with websockets.connect(self.url, extra_headers=headers) as ws:
            print("Conectado à API em tempo real da OpenAI.")

            # Wait for session creation confirmation
            event = await ws.recv()
            event_data = json.loads(event)
            if event_data["type"] == "session.created":
                print("Sessão inicializada.")

            # Configure session parameters
            await ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "turn_detection": {
                        "type": "server_vad"
                    },
                "tools": self.tool_registry.get_tool_definitions(),
                "tool_choice": "auto"
                }
            }))
            # Start tasks for receiving events and playing audio
            receive_task = asyncio.create_task(self.receive_events(ws))
            play_task = asyncio.create_task(self.audio_out.start())

            try:
                # Main loop for sending audio
                while True:
                    self.should_record = True
                    await self.send_audio(ws)
                    await asyncio.sleep(0.1)

            except KeyboardInterrupt:
                # Handle graceful shutdown on keyboard interrupt
                print("Saindo...")
                self.should_record = False
                receive_task.cancel()
                play_task.cancel()
                await self.audio_out.stop()
                await ws.close()

    async def send_audio(self, ws):
        # Function to send audio data to the API
        print("Comece a falar com o assistente (Pressione Ctrl+C para sair).")
        loop = asyncio.get_event_loop()

        def callback(indata, frames, time, status):
            # Callback function for audio input
            if status:
                print(status, flush=True)
            audio_bytes = indata.tobytes()
            encoded_audio = base64.b64encode(audio_bytes).decode('utf-8')
            message_event = {
                "type": "input_audio_buffer.append",
                "audio": encoded_audio
            }
            asyncio.run_coroutine_threadsafe(ws.send(json.dumps(message_event)), loop)

        # Set up and start the audio input stream
        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels,
                            dtype=self.audio_format, callback=callback,
                            blocksize=int(self.sample_rate * self.chunk_duration),
                            device=self.input_device_id):
            while self.should_record:
                await asyncio.sleep(self.chunk_duration)

    async def receive_events(self, ws):
        # Function to receive and process events from the API
        while True:
            try:
                response = await ws.recv()
                event = json.loads(response)

                if event["type"] == "response.audio.delta":
                    audio_chunk = base64.b64decode(event["delta"])
                    await self.audio_out.add_audio(audio_chunk)
                elif event["type"] == "response.audio.done":
                    await self.audio_out.add_audio(None)
                    print("Response complete.")
                elif event["type"] == "input_audio_buffer.speech_started":
                    await ws.send(json.dumps({
                        "type": "response.cancel"
                    }))
                    await self.audio_out.clear_audio()
                    print("User started speaking. Clearing audio playback.")
                elif event["type"] == "input_audio_buffer.speech_stopped":
                    print("User stopped speaking.")
                    
                elif event["type"] == "response.function_call_arguments.delta":
                    print(f"Function call arguments delta: {event['delta']}")
                elif event["type"] == "response.function_call_arguments.done":
                    print(f"Function call arguments complete: {event}")
                    await self.handle_function_call(ws, event)
                    # Trigger a response after function call
                    await ws.send(json.dumps({"type": "response.create"}))
                elif event["type"] == "error":
                    error = event.get("error", {})
                    message = error.get("message", "")
                    if message != "Error committing input audio buffer: the buffer is empty.":
                        print(f"Error: {message}")
                #else:
                #    pass

                    #if not event["type"].endswith(".delta"):
                    #    print(f"Received event: {event['type']}")
                else:
                    pass
                    # debug print(f"Unhandled event type: {event['type']}")
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed.")
                break

    async def handle_function_call(self, ws, event):
        call_id = event["call_id"]
        arguments = json.loads(event["arguments"])
        function_name = event["name"]  # Use the 'name' field from the event

        print(f"Attempting to call function: {function_name}")

        tool = self.tool_registry.get_tool(function_name)
        if tool:
            try:
                result = tool(**arguments)
                await ws.send(json.dumps({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": json.dumps(result)
                        }
                    }))
                print(f"Function {function_name} called successfully")
            except Exception as e:
                error_message = f"Error calling function {function_name}: {str(e)}"
                print(error_message)
                await ws.send(json.dumps({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": json.dumps({"error": error_message})
                        }
                    }))
        else:
            error_message = f"Function {function_name} not found in tool registry"
            print(error_message)
            self.print_registered_tools()  # Print registered tools for debugging
            await ws.send(json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps({"error": error_message})
                }
            }))

def select_audio_device(input_output, saved_device=None):
    # Function to let user select audio input/output device
    if saved_device is not None:
        print(f"Using saved {input_output} device: {saved_device}")
        return saved_device

    devices = sd.query_devices()
    print(f"Dispositivos de áudio {input_output} disponíveis:")
    for i, device in enumerate(devices):
        if (input_output == 'input' and device['max_input_channels'] > 0) or \
            (input_output == 'output' and device['max_output_channels'] > 0):
            print(f"{i}: {device['name']}")
    return int(input(f"Digite o número do dispositivo de {input_output} que você deseja usar: "))

# Example tool functions
def get_time(timezone: str = "UTC") -> Dict[str, Any]:
    """Get the current time for a given timezone."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    current_time = datetime.now(ZoneInfo(timezone)).strftime("%H:%M:%S")
    return {"time": current_time, "timezone": timezone}

def calculate(operation: str, x: float, y: float) -> Dict[str, Any]:
    """Perform a basic calculation."""
    operations = {
        "add": lambda a, b: a + b,
        "subtract": lambda a, b: a - b,
        "multiply": lambda a, b: a * b,
        "divide": lambda a, b: a / b if b != 0 else "Error: Division by zero"
    }
    if operation not in operations:
        return {"error": f"Unknown operation: {operation}"}
    result = operations[operation](x, y)
    return {"operation": operation, "x": x, "y": y, "result": result}

def main():
    # Main function to set up and start the audio streamer
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_key = input("Por favor, insira sua chave de API da OpenAI: ")
        with open('.env', 'a') as f:
            f.write(f'OPENAI_API_KEY="{api_key}"')
        set_key('.env', "OPENAI_API_KEY", api_key)

    # Load previously selected devices if available
    input_device_id = os.getenv("INPUT_DEVICE_ID")
    output_device_id = os.getenv("OUTPUT_DEVICE_ID")

    if input_device_id is None:
        input_device_id = select_audio_device('input')
        save_preference = input("Você quer salvar este dispositivo de entrada para uso futuro? (s/n): ").strip().lower()
        if save_preference.lower() == 's':
            os.environ["INPUT_DEVICE_ID"] = str(input_device_id)
            set_key('.env', "INPUT_DEVICE_ID", str(input_device_id))

    if output_device_id is None:
        output_device_id = select_audio_device('output')
        save_preference = input("Você quer salvar este dispositivo de saída para uso futuro? (s/n): ").strip().lower()
        if save_preference.lower() == 's':
            os.environ["OUTPUT_DEVICE_ID"] = str(output_device_id)
            set_key('.env', "OUTPUT_DEVICE_ID", str(output_device_id))

    streamer = AudioStreamer(api_key, int(input_device_id), int(output_device_id))

    # Register tools
    streamer.register_tool("get_time", get_time)
    streamer.register_tool("calculate", calculate)

    # Print registered tools before starting
    streamer.print_registered_tools()

    try:
        asyncio.run(streamer.start())
    except Exception as e:
        print(f"Ocorreu um erro: {str(e)}")

if __name__ == "__main__":
    main()
