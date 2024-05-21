import time
from PIL import ImageGrab, Image
import datetime
import requests
import json
import io
import base64
import ollama

def save_image_to_file(image, file_path):
    image.save(file_path, format="PNG")
    return file_path

def convert_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def send_image_to_ollama(base64_image):
    # Prepare the message to send to the LLaVA model
    message = {
        'role': 'user',
        'content': 'Describe this image:',
        'images': [base64_image]
    }

    try:
        # Use the ollama.chat function to send the image and retrieve the description
        response = ollama.chat(
            model="llava",  # Specify the desired LLaVA model size
            messages=[message]
        )

        # Print the model's description of the image
        print(f"Ollama response: {response['message']['content']}")
    except Exception as e:
        print(f"Error sending image to Ollama: {e}")

def main():
    last_clipboard = None
    while True:
        # Try to capture an image from the clipboard
        try:
            current_clipboard = ImageGrab.grabclipboard()
            if isinstance(current_clipboard, Image.Image) and current_clipboard != last_clipboard:
                print("Clipboard changed!")
                width, height = current_clipboard.size
                print(f"Image dimensions: {width}x{height}")
                
                # Convert the image to a base64 string
                base64_image = convert_image_to_base64(current_clipboard)
                
                # Send the base64 image to Ollama
                send_image_to_ollama(base64_image)
                last_clipboard = current_clipboard
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(1)  # Polling interval

if __name__ == "__main__":
    main()