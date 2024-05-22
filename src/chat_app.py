import curses
import asyncio
from ai_client import AsyncAIClient
from clipboard_manager import ClipboardManager
from color_setup import setup_colors

class ChatApp:
    def __init__(self, screen, model):
        self.model = model
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
        setup_colors(screen)
        self.clipboard_manager = ClipboardManager(self)

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
            async_client = AsyncAIClient()
            messages = self.history
            if base64_image:
                messages[-1]["images"] = [base64_image]
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
            messages[-1]["images"] = None  # llava jumbles more than one image
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
        return await self.clipboard_manager.check_clipboard(last_clipboard)
