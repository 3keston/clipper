"""Native clipboard access without third-party Python packages."""

import re
import shutil
import struct
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union


@dataclass(frozen=True)
class Clip:
    kind: str
    content: Union[str, bytes]
    size: Optional[Tuple[int, int]] = None


class ClipboardError(RuntimeError):
    pass


def png_dimensions(data: bytes) -> Tuple[int, int]:
    """Read image dimensions from the PNG header without decoding the image."""
    if len(data) < 24 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ClipboardError("The clipboard did not return a valid PNG image")
    if data[12:16] != b"IHDR":
        raise ClipboardError("The clipboard PNG is missing its IHDR header")
    return struct.unpack(">II", data[16:24])


def parse_applescript_png(output: str) -> bytes:
    """Decode output from `osascript -e 'the clipboard as «class PNGf»'`."""
    match = re.search(r"«data\s+PNGf([0-9A-Fa-f\s]+)»", output)
    if not match:
        raise ClipboardError("Could not decode the image returned by AppleScript")
    data = bytes.fromhex(match.group(1))
    png_dimensions(data)
    return data


class Clipboard:
    def __init__(self, platform_name: Optional[str] = None):
        self.platform = platform_name or sys.platform
        if self.platform == "darwin":
            self._require_commands("pbpaste", "pbcopy", "osascript")
        elif self.platform.startswith("win"):
            self.powershell = shutil.which("powershell") or shutil.which("pwsh")
            if not self.powershell:
                raise ClipboardError("PowerShell is required for clipboard access")
        elif self.platform.startswith("linux"):
            self.linux_backend = self._linux_backend()
        else:
            raise ClipboardError(f"Unsupported platform: {self.platform}")

    @staticmethod
    def _require_commands(*commands: str):
        missing = [command for command in commands if not shutil.which(command)]
        if missing:
            raise ClipboardError(
                "Missing required clipboard commands: " + ", ".join(missing)
            )

    @staticmethod
    def _linux_backend() -> str:
        if shutil.which("wl-paste") and shutil.which("wl-copy"):
            return "wayland"
        if shutil.which("xclip"):
            return "x11"
        raise ClipboardError(
            "Linux clipboard access requires wl-clipboard (Wayland) or xclip (X11)"
        )

    @staticmethod
    def _run(command: List[str], input_data: Optional[bytes] = None):
        try:
            return subprocess.run(
                command,
                input=input_data,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ClipboardError(f"Clipboard command not found: {command[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise ClipboardError(f"Clipboard command timed out: {command[0]}") from exc

    @staticmethod
    def _check_result(result, command: str):
        if result.returncode:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            message = f"{command} failed with exit code {result.returncode}"
            if detail:
                message += f": {detail}"
            raise ClipboardError(message)

    def read(self) -> Optional[Clip]:
        # Try an image first: copied files can also expose their path as text.
        image = self._read_image()
        if image:
            return Clip("image", image, png_dimensions(image))

        text = self._read_text()
        if text:
            return Clip("text", text)
        return None

    def clear(self):
        if self.platform == "darwin":
            result = self._run(["pbcopy"], b"")
        elif self.platform.startswith("win"):
            result = self._run(self._powershell_command(
                "Add-Type -AssemblyName System.Windows.Forms; "
                "[System.Windows.Forms.Clipboard]::Clear()"
            ))
        elif self.linux_backend == "wayland":
            result = self._run(["wl-copy", "--clear"])
        else:
            result = self._run(["xclip", "-selection", "clipboard"], b"")
        self._check_result(result, "Clearing the clipboard")

    def _read_image(self) -> Optional[bytes]:
        if self.platform == "darwin":
            result = self._run([
                "osascript", "-e", "the clipboard as «class PNGf»"
            ])
            # Conversion fails normally when the clipboard contains only text.
            if result.returncode or not result.stdout:
                return None
            return parse_applescript_png(
                result.stdout.decode("utf-8", errors="replace")
            )

        if self.platform.startswith("win"):
            script = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "Add-Type -AssemblyName System.Drawing; "
                "$image = [System.Windows.Forms.Clipboard]::GetImage(); "
                "if ($null -eq $image) { exit 0 }; "
                "$stream = [Console]::OpenStandardOutput(); "
                "$image.Save($stream, [System.Drawing.Imaging.ImageFormat]::Png); "
                "$image.Dispose()"
            )
            result = self._run(self._powershell_command(script))
            self._check_result(result, "Reading a clipboard image")
            return result.stdout or None

        if self.linux_backend == "wayland":
            command = ["wl-paste", "--type", "image/png"]
        else:
            command = ["xclip", "-selection", "clipboard", "-target", "image/png", "-out"]
        result = self._run(command)
        # No available image is an expected result, not an application error.
        return result.stdout or None

    def _read_text(self) -> str:
        if self.platform == "darwin":
            result = self._run(["pbpaste"])
        elif self.platform.startswith("win"):
            script = (
                "$text = Get-Clipboard -Raw; "
                "if ($null -ne $text) { "
                "$bytes = [System.Text.Encoding]::UTF8.GetBytes($text); "
                "$stream = [Console]::OpenStandardOutput(); "
                "$stream.Write($bytes, 0, $bytes.Length) }"
            )
            result = self._run(self._powershell_command(script))
        elif self.linux_backend == "wayland":
            result = self._run(["wl-paste", "--no-newline"])
        else:
            result = self._run([
                "xclip", "-selection", "clipboard", "-target", "UTF8_STRING", "-out"
            ])

        # An empty clipboard commonly makes native commands return nonzero.
        if result.returncode and not result.stdout:
            return ""
        return result.stdout.decode("utf-8")

    def _powershell_command(self, script: str) -> List[str]:
        return [
            self.powershell,
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            script,
        ]
