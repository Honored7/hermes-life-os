# Voice input — speech to text, then straight into the write path.
#
# Upstream owns the Whisper machinery (demo/voice_transcribe.py, local
# faster-whisper, CPU, ~150MB model on first use, no key, no cloud).
# This seam owns the HTTP shape: bytes in, {text} out, honest
# {unavailable} when the package/model/audio isn't there. The PWA posts
# a MediaRecorder blob; the transcript it gets back is shown for review
# and only persisted when the user sends it — dictation, not surveillance.

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any

AUDIO_SUFFIXES = {
    ".wav", ".mp3", ".ogg", ".oga", ".opus", ".m4a", ".mp4", ".webm",
    ".flac",
}
MAX_BYTES = 10 * 1024 * 1024


def _demo():
    demo = str(Path(__file__).resolve().parent.parent.parent / "demo")
    if demo not in sys.path:
        sys.path.insert(0, demo)


def transcribe_upload(data: bytes, filename: str = "note.webm") -> dict[str, Any]:
    """Transcribe uploaded audio bytes. Never raises for expected
    problems — returns {text} (possibly "") or {unavailable, reason}."""
    if not data:
        return {"unavailable": True, "reason": "Empty audio."}
    if len(data) > MAX_BYTES:
        return {"unavailable": True,
                "reason": "Audio too long — keep it under a couple of minutes."}
    suffix = Path(filename or "note.webm").suffix.lower() or ".webm"
    if suffix not in AUDIO_SUFFIXES:
        return {"unavailable": True,
                "reason": f"Unsupported audio type '{suffix}'."}
    _demo()
    try:
        import voice_transcribe as upstream_voice
    except ImportError as e:
        return {"unavailable": True,
                "reason": f"Voice engine missing: {e}"}
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix,
                                         delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        text = upstream_voice.transcribe_audio(
            tmp_path, os.environ.get("WHISPER_MODEL"))
        return {"text": text}
    except Exception as e:
        reason = str(e)
        if "faster-whisper" in reason:
            reason = ("Voice engine not installed on the server. "
                      "pip install faster-whisper")
        return {"unavailable": True, "reason": reason}
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
