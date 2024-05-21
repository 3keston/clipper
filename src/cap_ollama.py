"""
clipper with ollama api
"""

import time
from PIL import ImageGrab, Image
import datetime
import requests
import json
import io
import ollama

def save_image_to_file(image, file_path):
    image.save(file_path, format="PNG")
    return file_path

def send_image_to_ollama(image_path):
    # Prepare the message to send to the LLaVA model
    message = {
        'role': 'user',
        'content': 'Describe this image:',
        'images': [image_path]
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
                
                # Save the image to a file
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                image_path = f"clipboard_image_{timestamp}.png"
                save_image_to_file(current_clipboard, image_path)
                
                # Send the saved image to Ollama
                send_image_to_ollama(image_path)
                last_clipboard = current_clipboard
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(1)  # Polling interval

if __name__ == "__main__":
    main()