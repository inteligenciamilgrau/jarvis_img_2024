import replicate
from dotenv import load_dotenv
from PIL import Image
import matplotlib.pyplot as plt
import base64
import re
from io import BytesIO
import requests
import mss

# Load environment variables
load_dotenv()

# Set this flag to choose between local image or URL
use_local = True  # Set to True for local image, False for URL

# Define image URL and local image path
image_url = "https://img.freepik.com/free-vector/sticker-set-mixed-daily-objects_1308-104785.jpg"
#local_image_path = "./game_XP/capture.png"  # Replace with the path to your local image

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

# Check if using local or URL image
if use_local:
    # Load the local image file and convert it to base64
    image = capture_and_show_image_from_second_monitor(800, 600)
    buffered = BytesIO()
    image.save(buffered, format="PNG")  # Save image in buffer as PNG format
    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # Print the first 100 characters of the base64_image
    # print("Base64 image data:", base64_image[:100])

    # Try loading the image from the base64 data
    image_input = base64_image
else:
    # Load image from URL and convert it to base64
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    buffered = BytesIO()
    image.save(buffered, format="PNG")  # Save image in buffer as PNG format
    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
    image_input = base64_image

# Run the model and get the output
output = replicate.run(
    "zsxkib/molmo-7b:76ebd700864218a4ca97ac1ccff068be7222272859f9ea2ae1dd4ac073fa8de8",
    input={
        "text": "first discover what object I need to click, and them point to this object",
        "image": "data:image/png;base64,"+image_input,
        "top_k": 50,
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
    print(f"Point {i + 1}: ({x + 1080}, {y})")

# Open the image for display purposes based on source type
img = capture_and_show_image_from_second_monitor(800,600)

# Display the image and the points
fig, ax = plt.subplots()
ax.imshow(img)

# Convert coordinates from relative to pixel positions
width, height = img.size
x_coords = [x / 100 * width for x, y in coordinates]
y_coords = [y / 100 * height for x, y in coordinates]

# Plot points on the image
ax.scatter(x_coords, y_coords, color='black', s=400, marker='o')

print("coords", x_coords, y_coords, img.size)

# Show plot with points
plt.title("Coordinates on Image")
plt.show()
