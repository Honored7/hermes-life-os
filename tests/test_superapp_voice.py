"""Voice input seam: bytes in, text out, honest when it can't. No network."""
import io
import sys
import types
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def _fake_voice_module(text="hello world"):
    mod = types.ModuleType("voice_transcribe")

    def transcribe_audio(path, model_size=None):
        assert Path(path).is_file()
        return text

    mod.transcribe_audio = transcribe_audio
    return mod


class TestTranscribeSeam:
    def test_bytes_to_text(self, monkeypatch):
        from superapp.surfaces import voice as voice_seam

        monkeypatch.setitem(sys.modules, "voice_transcribe",
                            _fake_voice_module("log my run"))
        result = voice_seam.transcribe_upload(b"\x00" * 64, "note.webm")
        assert result == {"text": "log my run"}

    def test_empty_rejected(self):
        from superapp.surfaces import voice as voice_seam

        assert voice_seam.transcribe_upload(b"", "note.webm")[
            "unavailable"] is True

    def test_oversize_rejected(self):
        from superapp.surfaces import voice as voice_seam

        big = b"\x00" * (voice_seam.MAX_BYTES + 1)
        assert voice_seam.transcribe_upload(big, "note.webm")[
            "unavailable"] is True

    def test_bad_suffix_rejected(self):
        from superapp.surfaces import voice as voice_seam

        result = voice_seam.transcribe_upload(b"\x00" * 64, "note.exe")
        assert result["unavailable"] is True

    def test_engine_failure_honest(self, monkeypatch):
        from superapp.surfaces import voice as voice_seam

        mod = types.ModuleType("voice_transcribe")

        def boom(path, model_size=None):
            raise RuntimeError("model exploded")

        mod.transcribe_audio = boom
        monkeypatch.setitem(sys.modules, "voice_transcribe", mod)
        result = voice_seam.transcribe_upload(b"\x00" * 64, "note.webm")
        assert result["unavailable"] is True

    def test_http_roundtrip(self, monkeypatch):
        from fastapi.testclient import TestClient

        from superapp.surfaces.api import app

        monkeypatch.setitem(sys.modules, "voice_transcribe",
                            _fake_voice_module("sleep was short"))
        c = TestClient(app)
        r = c.post("/api/v1/voice/transcribe",
                   files={"audio": ("note.webm", io.BytesIO(b"\x00" * 128),
                                    "audio/webm")})
        assert r.status_code == 200
        assert r.json() == {"text": "sleep was short"}

    def test_http_missing_file(self):
        from fastapi.testclient import TestClient

        from superapp.surfaces.api import app

        c = TestClient(app)
        assert c.post("/api/v1/voice/transcribe").status_code in (400, 422)
