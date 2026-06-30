"""Voice transcription (TZ §9). Real, with graceful degradation.

Order of preference:
  1. faster-whisper running locally on the server (keyless, real).
  2. An OpenAI-compatible Whisper API if WHISPER_API_KEY is set.
  3. Otherwise None -> the bot asks the user to type instead (never nonsense).
"""
from __future__ import annotations

import httpx

from app.config import settings

_model = None
_model_failed = False


def _load_local():
    global _model, _model_failed
    if _model is not None or _model_failed:
        return _model
    try:
        from faster_whisper import WhisperModel  # type: ignore

        _model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")
    except Exception:
        _model_failed = True
        _model = None
    return _model


async def transcribe(audio: bytes, lang: str) -> str | None:
    lang = "ru" if lang == "ru" else "en"

    if settings.voice_provider == "whisper_api" and settings.whisper_api_key:
        try:
            async with httpx.AsyncClient(timeout=60.0) as c:
                r = await c.post(
                    f"{settings.whisper_api_base}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {settings.whisper_api_key}"},
                    files={"file": ("audio.ogg", audio, "audio/ogg")},
                    data={"model": "whisper-1", "language": lang},
                )
                r.raise_for_status()
                return (r.json().get("text") or "").strip() or None
        except Exception:
            return None

    model = _load_local()
    if model is None:
        return None
    try:
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=True) as f:
            f.write(audio)
            f.flush()
            segments, _ = model.transcribe(f.name, language=lang, vad_filter=True)
            return " ".join(s.text for s in segments).strip() or None
    except Exception:
        return None
