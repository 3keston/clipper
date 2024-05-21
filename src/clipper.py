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
import time


def convert_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Define the Breezy chat application
class ChatApp:
    def __init__(self, screen):
        self.model = "llava"
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
        self.system_msg = f"""
        You are Breezy Bob, a helpful assistant confined to a terminal window.
        You are powered by a totally private local LLM called {self.model}.
        """
        self.history = [{"role": "user", "content": self.system_msg}]
        self.setup_colors()

    def setup_colors(self):
        curses.start_color()
        if curses.can_change_color():
            curses.init_color(16, 205, 205, 182)  # Background
            curses.init_color(17, 514, 569, 482)  # Foreground
            curses.init_color(18, 333, 427, 216)  # Comment
            curses.init_color(19, 705, 352, 353)  # Red
            curses.init_color(20, 282, 462, 718)  # Blue
            curses.init_color(21, 462, 718, 462)  # Green
            curses.init_color(22, 689, 555, 386)  # Yellow
            curses.init_pair(1, 17, 16)  # User color (foreground on background)
            curses.init_pair(2, 19, 16)  # Agent color (red on background)
            curses.init_pair(3, 22, 16)  # Prompt color (yellow on background)
        else:
            curses.init_pair(
                1, curses.COLOR_WHITE, curses.COLOR_BLACK
            )  # User color (white on black)
            curses.init_pair(
                2, curses.COLOR_RED, curses.COLOR_BLACK
            )  # Agent color (red on black)
            curses.init_pair(
                3, curses.COLOR_YELLOW, curses.COLOR_BLACK
            )  # Prompt color (yellow on black)
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

    async def chat_with_ai(self, query, base64_image=None):
        try:
            self.history.append({"role": "user", "content": query})
            async_client = AsyncClient()
            messages = self.history
            if base64_image:
                messages[-1]['images'] = [base64_image]
            stream = await async_client.chat(
                model=self.model,
                messages=messages,
                stream=True,
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
            messages[-1]['images'] = None # llava jumbles more than one image
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
            if isinstance(current_clipboard, Image.Image) and current_clipboard != last_clipboard:
                width, height = current_clipboard.size
                self.add_text(f"\nCaught a new  clip! ({width}x{height}).\n", color_pair=3)
                base64_image = convert_image_to_base64(current_clipboard)
                last_clipboard = current_clipboard
                return base64_image, last_clipboard
        except Exception as e:
            self.add_text(f"\nError checking clipboard: {str(e)}\n", color_pair=2)
        return None, last_clipboard

async def main(screen):
    curses.curs_set(1)
    app = ChatApp(screen)
    last_clipboard = None
    while True:
        query = await app.get_user_input()
        if query.lower() in ("exit", "quit"):
            break
        
        base64_image, last_clipboard = await app.check_clipboard(last_clipboard)
        if base64_image:
            await app.chat_with_ai(query, base64_image)
        else:
            await app.chat_with_ai(query)
        
        app.screen.move(0, len(app.prompt_text))
        app.screen.clrtoeol()
        app.screen.refresh()

if __name__ == "__main__":
    curses.wrapper(lambda screen: asyncio.run(main(screen)))
