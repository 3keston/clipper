""" 
Cap your screen from clipboard
"""

import time
from PIL import ImageGrab
import datetime


def save_image(image_data):
    # Generate a timestamped filename for the image
    filename = f"clipboard_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    image_data.save(filename)
    print(f"Saved image to {filename}")


def main():
    last_clipboard = None
    while True:
        # Try to capture an image from the clipboard
        try:
            current_clipboard = ImageGrab.grabclipboard()
            if current_clipboard and current_clipboard != last_clipboard:
                print("Clipboard changed!")
                save_image(current_clipboard)
                last_clipboard = current_clipboard
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(1)  # Polling interval


if __name__ == "__main__":
    main()
