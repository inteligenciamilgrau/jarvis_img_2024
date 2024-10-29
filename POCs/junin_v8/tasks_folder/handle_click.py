from io import BytesIO
import base64
import threading
import replicate
import re
import pyautogui
import matplotlib.pyplot as plt
import mss
from PIL import Image
from computer_use_class import AnthropicToolHandler

setar_molmo = False

if setar_molmo:
    # Metadata for this task
    description = "Handle clicking a part of the screen."
    trigger = """If the user ask to click or to point to something, the type is 'click'.
    The click content must be always in english starting with 'point to the...'"""
    example = "{'type': 'handle_click', 'content': 'point to the ...'}"
else:
    description = """Usa o computador para buscar na internet, e clicar em sites, botões ou notícias.
    Informe onde deseja clicar, ou o site que quer acessar, ou a busque que gostaria de fazer.
    Explique na forma de texto como no exemplo:
        'Clique no instagram'
        'Busque no google um site de viagens'
    """
    trigger = """Se o usuário pedir para clicar, fazer uma busca ou quiser ver algo na tela, rode isto'"""
    example = "{'type': 'handle_click', 'content': 'Clique no ...'}"
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

def click_on(click_this):
    segundo_monitor_pixels = 1920
    image = capture_and_show_image_from_second_monitor(1920, 1080)
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

def chat_handler_thread(message):
    print("Usando PC!", message)
    handler = AnthropicToolHandler(monitor_index=2, monitor_offset=[1920, 0], falar=False)
    print("Iniciando tool")
    result = handler.handle_chat(message)
    # Do something with the result if needed
    print(result)


# Function that handles the task
def execute(content):
    print("Click:", content)

    if setar_molmo:
        click_on(content)
        return content
    else:
        message_thread = threading.Thread(target=chat_handler_thread, args=(content,))
        # Start the thread
        message_thread.start()

        #return str(result)
        return "Deu certo?"
