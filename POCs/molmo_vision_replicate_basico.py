import replicate
from dotenv import load_dotenv
from PIL import Image
import matplotlib.pyplot as plt
import base64
import re
from io import BytesIO
import requests

# Load environment variables
load_dotenv()

# Set this flag to choose between local image or URL
use_local = True  # Set to True for local image, False for URL

# Define image URL and local image path
image_url = "https://img.freepik.com/free-vector/sticker-set-mixed-daily-objects_1308-104785.jpg"
local_image_path = "./tela_jogo.png"  # Replace with the path to your local image

# Check if using local or URL image
if use_local:
    # Load the local image file and convert it to base64
    with open(local_image_path, "rb") as img_file:
        base64_image = base64.b64encode(img_file.read()).decode('utf-8')
    image_input = base64_image
else:
    # Load image from URL and convert it to base64
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    buffered = BytesIO()
    image.save(buffered, format="PNG")  # Save image in buffer as JPEG format
    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
    image_input = base64_image

#print("IMAGE", image_input[:100])

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

segundo_monitor_pixels = 1920

# Print the coordinates
print("Coordinates of points:")
for i, (x, y) in enumerate(coordinates):
    print(f"Point {i + 1}: ({x + segundo_monitor_pixels}, {y})")

# Open the image for display purposes based on source type
if use_local:
    img = Image.open(local_image_path)
else:
    img = image  # Use the image loaded from URL

# Display the image and the points
fig, ax = plt.subplots()
ax.imshow(img)

# Convert coordinates from relative to pixel positions
width, height = img.size
x_coords = [x / 100 * width for x, y in coordinates]
y_coords = [y / 100 * height for x, y in coordinates]

# Plot points on the image
ax.scatter(x_coords, y_coords, color='red', s=100, marker='o')

print("coords", x_coords, y_coords, img.size)

# Show plot with points
plt.title("Coordinates on Image")
plt.show()
