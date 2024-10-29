from io import BytesIO
import base64
from openai import OpenAI
from PIL import Image
import mss

# Metadata for this task
description = "Handle a request about an image."
trigger = "If the user ask about the screen or image, the type is 'image' and pass the question as content."
example = "{'type': 'handle_image', 'content': 'Question about the image'}"

def capture_and_show_image_from_second_monitor(width=400, height=400):
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

def ler_tela(message):
    client = OpenAI()

    image = capture_and_show_image_from_second_monitor(1920, 1080)
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

# Function that handles the task
def execute(content):
    resposta = ler_tela(content)
    return resposta
