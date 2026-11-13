"""Minimal asynchronous Ollama client using only the Python standard library."""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaError(RuntimeError):
    """An error returned by Ollama or its HTTP transport."""


class ChatStream:
    """Asynchronously decode Ollama's newline-delimited JSON response."""

    def __init__(self, response):
        self._response = response
        self._closed = False

    def __aiter__(self):
        return self

    async def __anext__(self) -> Dict[str, Any]:
        if self._closed:
            raise StopAsyncIteration

        try:
            while True:
                # urllib is synchronous, so keep socket reads off the UI event loop.
                line = await asyncio.to_thread(self._response.readline)
                if not line:
                    await self.aclose()
                    raise StopAsyncIteration
                if not line.strip():
                    continue

                chunk = json.loads(line)
                if "error" in chunk:
                    raise OllamaError(str(chunk["error"]))
                return chunk
        except StopAsyncIteration:
            raise
        except (OllamaError, json.JSONDecodeError):
            await self.aclose()
            raise
        except Exception as exc:
            await self.aclose()
            raise OllamaError(f"Failed reading Ollama's response: {exc}") from exc

    async def aclose(self):
        if not self._closed:
            self._closed = True
            await asyncio.to_thread(self._response.close)


class OllamaClient:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 300):
        host = base_url or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
        if "://" not in host:
            host = f"http://{host}"
        self.base_url = host.rstrip("/")
        self.timeout = timeout

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None,
    ) -> ChatStream:
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": options or {},
        }
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Accept": "application/x-ndjson",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            response = await asyncio.to_thread(
                urlopen, request, timeout=self.timeout
            )
        except HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace").strip()
            finally:
                exc.close()
            message = f"Ollama returned HTTP {exc.code}"
            if detail:
                message += f": {detail}"
            raise OllamaError(message) from exc
        except URLError as exc:
            raise OllamaError(
                f"Could not connect to Ollama at {self.base_url}: {exc.reason}"
            ) from exc
        except OSError as exc:
            raise OllamaError(f"Could not connect to Ollama: {exc}") from exc

        return ChatStream(response)
