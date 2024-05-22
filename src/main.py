"""
Clipper 0.1
"""

import curses
import asyncio
from chat_app import ChatApp # type: ignore

async def main(screen):
    curses.curs_set(1)
    model = "llava"
    app = ChatApp(screen, model)
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
