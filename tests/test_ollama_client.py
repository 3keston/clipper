import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ollama_client import OllamaClient


class FakeResponse(io.BytesIO):
    pass


class OllamaClientTests(unittest.IsolatedAsyncioTestCase):
    @patch("ollama_client.urlopen")
    async def test_chat_sends_request_and_decodes_stream(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(
            b'{"message":{"content":"Hello"}}\n\n'
            b'{"message":{"content":" world"},"done":true}\n'
        )
        client = OllamaClient("127.0.0.1:11434")

        stream = await client.chat(
            "test-model",
            [{"role": "user", "content": "Hi"}],
            {"num_ctx": 4096},
        )
        chunks = [chunk async for chunk in stream]

        self.assertEqual(
            [chunk["message"]["content"] for chunk in chunks],
            ["Hello", " world"],
        )
        request = mock_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/chat")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(
            json.loads(request.data),
            {
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hi"}],
                "stream": True,
                "options": {"num_ctx": 4096},
            },
        )
        self.assertTrue(mock_urlopen.return_value.closed)

    @patch("ollama_client.urlopen")
    async def test_host_environment_is_supported(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(b"")
        with patch.dict("os.environ", {"OLLAMA_HOST": "localhost:1234"}):
            client = OllamaClient()
            await client.chat("test-model", [])
        request = mock_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:1234/api/chat")


if __name__ == "__main__":
    unittest.main()
