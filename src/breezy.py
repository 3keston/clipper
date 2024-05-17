import curses
import asyncio
from ollama import AsyncClient


class ChatApp:
    def __init__(self, screen):
        self.screen = screen
        self.cursor_x = 0
        self.cursor_y = 1  # Start below the prompt
        self.height, self.width = screen.getmaxyx()
        self.height -= 1  # Buffer a line at the bottom
        self.text_lines = [""]
        self.scroll_position = 0
        self.scroll_adjust_step = int(self.height / 2.0)  # Clear half the page
        self.prompt_text = "> "
        self.history = []

    def add_text(self, text):
        """Add text to the screen, handling new lines and scrolling."""
        for char in text:
            if char == "\n" or self.cursor_x >= self.width:
                self.cursor_x = 0
                self.cursor_y += 1
                if self.cursor_y >= self.height:
                    self.scroll_position += self.scroll_adjust_step
                    self.cursor_y = self.height - self.scroll_adjust_step
            while len(self.text_lines) <= self.cursor_y + self.scroll_position:
                self.text_lines.append("")
            if char != "\n":
                self.text_lines[self.cursor_y + self.scroll_position] += char
                self.cursor_x += 1

        self.refresh_screen()

    def refresh_screen(self):
        """Refresh the screen with the current text buffer."""
        self.screen.clear()
        self.screen.addstr(0, 0, self.prompt_text)  # Add the prompt at the top
        for i in range(1, self.height):
            line_index = i + self.scroll_position - 1
            if line_index < len(self.text_lines):
                try:
                    self.screen.addstr(i, 0, self.text_lines[line_index][: self.width])
                except curses.error:
                    pass
        self.screen.refresh()

    async def chat_with_ai(self, query):
        """Send a query to the AI and display the response."""
        try:
            self.history.append({"role": "user", "content": query})

            async_client = AsyncClient()
            stream = await async_client.chat(
                model="llama3",
                messages=self.history,
                stream=True,
            )

            self.add_text(f"User: {query}\n")
            self.add_text("Agent: ")
            agent_message = ""

            async for chunk in stream:
                chunk_text = chunk["message"]["content"]
                for char in chunk_text:
                    self.add_text(char)
                    agent_message += char
                    await asyncio.sleep(0.01)  # Sleep asynchronously

            self.add_text("\n")
            self.history.append({"role": "assistant", "content": agent_message})
            self.refresh_screen()
        except Exception as e:
            self.add_text(f"\nError: {str(e)}\n")
            self.refresh_screen()

    async def get_user_input(self):
        """Get user input from the screen."""
        prompt = self.prompt_text
        self.screen.addstr(0, 0, prompt)
        self.screen.clrtoeol()  # Clear the input line
        self.screen.refresh()
        curses.echo()
        user_input = self.screen.getstr(0, len(prompt)).decode("utf-8")
        curses.noecho()
        return user_input


async def main(screen):
    """Main function to run the chat application."""
    curses.curs_set(1)
    app = ChatApp(screen)

    while True:
        query = await app.get_user_input()
        if query.lower() in ("exit", "quit"):
            break
        await app.chat_with_ai(query)

        # Return focus to the prompt area
        app.screen.move(0, len(app.prompt_text))
        app.screen.clrtoeol()  # Clear the input line after moving cursor
        app.screen.refresh()


if __name__ == "__main__":
    curses.wrapper(lambda screen: asyncio.run(main(screen)))
