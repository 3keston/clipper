import time
from PIL import ImageGrab, Image
import datetime
import base64
import requests
import json
import io

def get_image_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def send_image_to_ollama(image_base64):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llava",
        "prompt": "What is in this picture?",
        "images": [image_base64]
    }
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), stream=True)
        response.raise_for_status()  # Raise an HTTPError if the response was unsuccessful

        # Collect the streaming response
        response_text = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                response_data = json.loads(decoded_line)
                response_text += response_data.get('response', '')
        
        print(f"Ollama response: {response_text}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending image to Ollama: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw response: {response.text}")

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
                image_base64 = get_image_base64(current_clipboard)
                send_image_to_ollama(image_base64)
                last_clipboard = current_clipboard
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(1)  # Polling interval

if __name__ == "__main__":
    main()
