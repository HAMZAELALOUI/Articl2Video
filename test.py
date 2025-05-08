# Import the packages
from openai import OpenAI
from dotenv import load_dotenv
import os
import base64
import time
# Load the API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
# Initialize the OpenAI client
client = OpenAI(api_key=api_key)
# Ask the user to input a prompt in the terminal
print("What do you want to generate?")
prompt = input("> ")
print("Generating image...")
# Send the prompt to the API
img = client.images.generate(
  model="gpt-image-1",
  prompt=prompt,
  background="auto",
  n=1,
  quality="high",
  size="1024x1024",
  output_format="png",
  moderation="auto",
)
# Save the image into a file in the root directory
image_bytes = base64.b64decode(img.data[0].b64_json)
output_filename = "generated_image.png"
with open(output_filename, "wb") as f:
  f.write(image_bytes)

print(f"Image saved to: {output_filename}")