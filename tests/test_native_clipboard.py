import struct
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from native_clipboard import Clipboard, ClipboardError, parse_applescript_png, png_dimensions


def png_header(width, height):
    return (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", width, height)
        + b"\x08\x06\x00\x00\x00"
        + b"\x00" * 16
    )


class NativeClipboardTests(unittest.TestCase):
    def test_png_dimensions(self):
        self.assertEqual(png_dimensions(png_header(640, 480)), (640, 480))

    def test_applescript_png_output(self):
        data = png_header(32, 20)
        self.assertEqual(
            parse_applescript_png(f"«data PNGf{data.hex().upper()}»\n"),
            data,
        )

    def test_invalid_png_is_rejected(self):
        with self.assertRaises(ClipboardError):
            png_dimensions(b"not a png")

    def test_invalid_applescript_output_is_rejected(self):
        with self.assertRaises(ClipboardError):
            parse_applescript_png("clipboard contains text")

    def test_macos_image_capture(self):
        data = png_header(100, 50)
        image_result = subprocess.CompletedProcess(
            "osascript", 0, f"«data PNGf{data.hex()}»".encode(), b""
        )
        with patch("native_clipboard.shutil.which", return_value="/usr/bin/tool"), patch(
            "native_clipboard.subprocess.run", return_value=image_result
        ):
            clip = Clipboard("darwin").read()

        self.assertEqual(clip.kind, "image")
        self.assertEqual(clip.content, data)
        self.assertEqual(clip.size, (100, 50))

    def test_macos_text_capture(self):
        no_image = subprocess.CompletedProcess("osascript", 1, b"", b"not an image")
        text = subprocess.CompletedProcess("pbpaste", 0, b"hello", b"")
        with patch("native_clipboard.shutil.which", return_value="/usr/bin/tool"), patch(
            "native_clipboard.subprocess.run", side_effect=[no_image, text]
        ):
            clip = Clipboard("darwin").read()

        self.assertEqual(clip.kind, "text")
        self.assertEqual(clip.content, "hello")
        self.assertIsNone(clip.size)


if __name__ == "__main__":
    unittest.main()
