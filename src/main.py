"""
main
"""

import curses
import asyncio

from chat_app import ChatApp
from config import config


async def main(screen):
    model = config["model"]
    app = ChatApp(screen, model)
    last_clipboard = None
    while True:
        query = await app.get_user_input()
        if query.lower() in ("exit", "quit"):
            break

        clipboard_content, last_clipboard = await app.check_clipboard(last_clipboard)
        if clipboard_content:
            content_type, content = clipboard_content
            match content_type:
                case "image":
                    await app.chat_with_ai(query, base64_image=content)
                case "text":
                    await app.chat_with_ai(query, text=content)
        else:
            await app.chat_with_ai(query)

        app.screen.move(0, len(app.prompt_text))
        app.screen.clrtoeol()
        app.screen.refresh()


if __name__ == "__main__":
    curses.wrapper(lambda screen: asyncio.run(main(screen)))
