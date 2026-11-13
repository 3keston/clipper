"""
clipper 0.1
"""

# Import necessary modules
import curses
import asyncio
import base64

from color_setup import change_colors
from config import config
from native_clipboard import Clipboard
from ollama_client import OllamaClient


class ChatApp:
    def __init__(self, screen):
        curses.curs_set(1)
        self.clipboard = Clipboard()
        self.clipboard.clear()  # clear clipboard before start
        # ollama config
        self.ollama_client = OllamaClient()
        self.ollama_options = config["ollama_options"]
        self.model = config["model"]
        self.system_msg = config["system_msg"]
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
        self.scroll_adjust_step = 4  # num lines to scroll up when hitting the bottom
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
                    m.pop("images", None)
            if text:
                query = f"{query}\nUser clipboard:\n{text}"
            current_message = {"role": "user", "content": query}
            if base64_image:
                current_message["images"] = [base64_image]
            self.history.append(current_message)
            stream = await self.ollama_client.chat(
                model=self.model,
                messages=messages,
                options=self.ollama_options,
            )
            self.add_text(f"User: {query}\n", color_pair=1)
            self.add_text("Agent: ", color_pair=2)
            agent_message = ""
            try:
                async for chunk in stream:
                    chunk_text = chunk["message"]["content"]
                    for char in chunk_text:
                        self.add_text(char, color_pair=2)
                        agent_message += char
                        await asyncio.sleep(0.01)
            finally:
                await stream.aclose()
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

    async def check_clipboard(self):
        try:
            clip = await asyncio.to_thread(self.clipboard.read)
            if clip is None:
                return None

            await asyncio.to_thread(self.clipboard.clear)
            if clip.kind == "image":
                width, height = clip.size
                self.add_text(
                    f"\nCaught an image clip! - ({width}x{height}).\n", color_pair=3
                )
                base64_image = base64.b64encode(clip.content).decode("ascii")
                return "image", base64_image

            self.add_text("\nCaught a text clip!\n", color_pair=3)
            return "text", clip.content

        except Exception as e:
            self.add_text(f"\nError checking clipboard: {str(e)}\n", color_pair=2)

        return None
