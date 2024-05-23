"""
clipper 0.1
"""

# Import necessary modules
import curses
import asyncio
from ollama import AsyncClient  # type: ignore
from PIL import ImageGrab, Image
import io
import base64
import pyperclip  # type: ignore

from color_setup import change_colors


# Define the Breezy chat application
class ChatApp:
    def __init__(self, screen, model):
        curses.curs_set(1)
        pyperclip.copy("")  # clear clipboard before start
        # ollama config
        self.ollama_client = AsyncClient()
        self.ollama_options = {"num_ctx": 4096}
        self.model = model
        self.system_msg = f"""
        You are Clipper, a helpful assistant confined to a terminal window.
        You are powered by a totally private local LLM called {self.model}.
        """
        self.history = [{"role": "user", "content": self.system_msg}]
        # screen config
        self.screen = screen
        self.cursor_x = 0
        self.cursor_y = 1  # Start below the prompt
        self.height, self.width = screen.getmaxyx()
        self.height -= 1  # Buffer a line at the bottom
        self.text_lines = [""]
        self.text_colors = [0]
        self.scroll_position = 0
        self.scroll_adjust_step = 4
        self.prompt_text = "> "
        self.setup_colors()

    def setup_colors(self):
        change_colors()
        self.screen.bkgd(" ", curses.color_pair(1))

    def add_text(self, text, color_pair=0):
        for char in text:
            if char == "\n" or self.cursor_x >= self.width:
                self.cursor_x = 0
                self.cursor_y += 1
                if self.cursor_y >= self.height:
                    self.scroll_position += self.scroll_adjust_step
                    self.cursor_y = self.height - self.scroll_adjust_step
            while len(self.text_lines) <= self.cursor_y + self.scroll_position:
                self.text_lines.append("")
                self.text_colors.append(0)
            if char != "\n":
                self.text_lines[self.cursor_y + self.scroll_position] += char
                self.text_colors[self.cursor_y + self.scroll_position] = color_pair
                self.cursor_x += 1
        self.refresh_screen()

    def refresh_screen(self):
        self.screen.clear()
        self.screen.addstr(0, 0, self.prompt_text, curses.color_pair(3))
        for i in range(1, self.height):
            line_index = i + self.scroll_position - 1
            if line_index < len(self.text_lines):
                try:
                    self.screen.addstr(
                        i,
                        0,
                        self.text_lines[line_index][: self.width],
                        curses.color_pair(self.text_colors[line_index]),
                    )
                except curses.error:
                    pass
        self.screen.refresh()

    async def chat_with_ai(self, query, base64_image=None, text=None):
        try:
            # clear out the previous images, else keep it to continue chatting
            messages = self.history
            if base64_image:
                for m in messages:
                    m["images"] = None
            if text:
                query = f"{query}\nUser clipboard:\n{text}"
            current_message = {"role": "user", "content": query}
            if base64_image:
                current_message["images"] = [base64_image]
            self.history.append(current_message)
            stream = await self.ollama_client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options=self.ollama_options,
            )
            self.add_text(f"User: {query}\n", color_pair=1)
            self.add_text("Agent: ", color_pair=2)
            agent_message = ""
            async for chunk in stream:
                chunk_text = chunk["message"]["content"]
                for char in chunk_text:
                    self.add_text(char, color_pair=2)
                    agent_message += char
                    await asyncio.sleep(0.01)
            self.add_text("\n", color_pair=2)
            self.history.append({"role": "assistant", "content": agent_message})
            self.refresh_screen()
        except Exception as e:
            self.add_text(f"\nError: {str(e)}\n", color_pair=2)
            self.refresh_screen()

    async def get_user_input(self):
        prompt = self.prompt_text
        self.screen.addstr(0, 0, prompt, curses.color_pair(3))
        self.screen.clrtoeol()
        self.screen.refresh()
        curses.echo()
        user_input = self.screen.getstr(0, len(prompt)).decode("utf-8")
        curses.noecho()
        return user_input

    async def check_clipboard(self, last_clipboard):
        try:
            current_clipboard = ImageGrab.grabclipboard()

            # Check if the clipboard contains an image
            if (
                isinstance(current_clipboard, Image.Image)
                and current_clipboard != last_clipboard
            ):
                width, height = current_clipboard.size
                self.add_text(
                    f"\nCaught an image clip! - ({width}x{height}).\n", color_pair=3
                )
                buffered = io.BytesIO()
                current_clipboard.save(buffered, format="PNG")
                base64_image = base64.b64encode(buffered.getvalue()).decode()
                last_clipboard = current_clipboard
                pyperclip.copy("")  # Clear the clipboard
                return ("image", base64_image), last_clipboard

            # Check if the clipboard contains text
            clipboard_text = pyperclip.paste()
            if clipboard_text and clipboard_text != last_clipboard:
                self.add_text(f"\nCaught a text clip!\n", color_pair=3)
                text_data = clipboard_text
                last_clipboard = clipboard_text
                pyperclip.copy("")  # Clear the clipboard
                return ("text", text_data), last_clipboard

        except Exception as e:
            self.add_text(f"\nError checking clipboard: {str(e)}\n", color_pair=2)

        return None, last_clipboard
