"""Opt-in, local-first KIN voice interaction.

The audio pipeline is deliberately optional: browser microphone recording,
offline Whisper speech-to-text (when installed), deterministic planning rules,
and offline eSpeak speech output. A voice utterance can NEVER approve or save a
calendar change. No recordings or synthesized WAV files are persisted by KIN.
"""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import wave
from typing import Any

from kin_core import detect_internal_conflicts, parse_dt
from kin_life import answer_with_rules, suggest_alternative_slots
from kin_models import MICHIGAN


class VoiceUnavailable(RuntimeError):
    """Optional voice dependency or a local model is not available."""


def _check_audio(wav_data: bytes) -> None:
    """Reject oversized, corrupt or unusually long audio before transcription."""
    if not isinstance(wav_data, bytes) or not 44 <= len(wav_data) <= 3_000_000:
        raise ValueError("Record a short WAV message (under 3 MB)")
    try:
        with wave.open(BytesIO(wav_data), "rb") as sample:
            seconds = sample.getnframes() / sample.getframerate()
            if not 0.1 <= seconds <= 30:
                raise ValueError("Voice recordings must be between 0.1 and 30 seconds")
            if not 8000 <= sample.getframerate() <= 48000:
                raise ValueError("Unsupported recording sample rate")
            if sample.getnchannels() not in (1, 2):
                raise ValueError("Unsupported channel count")
    except (EOFError, wave.Error, ZeroDivisionError) as exc:
        raise ValueError("A valid WAV recording is required") from exc


@lru_cache(maxsize=2)
def _whisper_model(model_name: str):
    """Lazy model loading, so normal KIN does not need an ML dependency.

    A first-time model-name lookup may download weights to the host's model
    cache; subsequent local calls use the cached weights.
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise VoiceUnavailable(
            "Offline transcription is optional. Install requirements-voice.txt "
            "to enable Whisper on this machine.") from exc
    return WhisperModel(model_name, device="cpu", compute_type="int8")


def transcribe_local(wav_data: bytes, *, model: Any = None) -> str:
    """Transcribe one explicitly submitted recording; remove its temp file.

    The injected model parameter supports offline tests without downloading any
    ML weights. No third-party transcription API is called here.
    """
    _check_audio(wav_data)
    if model is None:
        choice = os.getenv("KIN_VOICE_MODEL", "tiny.en").strip()
        if choice not in ("tiny.en", "base.en"):
            raise VoiceUnavailable("KIN_VOICE_MODEL must be tiny.en or base.en")
        try:
            model = _whisper_model(choice)
        except VoiceUnavailable:
            raise
        except Exception as exc:
            raise VoiceUnavailable(
                "The offline speech model could not load. It may need an "
                "initial model download or more CPU/RAM.") from exc
    path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", prefix="kin-voice-",
                                         delete=False) as recorded:
            recorded.write(wav_data)
            path = Path(recorded.name)
        segments, _ = model.transcribe(
            str(path), language="en", beam_size=1,
            condition_on_previous_text=False)
        words = " ".join(segment.text.strip() for segment in segments).strip()
        if not words:
            raise ValueError("No clear speech was recognized; please try again")
        return words[:500].strip()
    finally:
        if path is not None:
            path.unlink(missing_ok=True)


def synthesize_local(text: str, *, executable: str | None = None) -> bytes:
    """Render a short, spoken WAV locally with eSpeak NG, if installed."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("There is no answer to speak")
    cmd = executable or shutil.which("espeak-ng")
    if not cmd:
        raise VoiceUnavailable(
            "Offline spoken answers require eSpeak NG. On Ubuntu install "
            "it with: sudo apt install espeak-ng")
    # No shell, no arbitrary arguments; speech content travels through stdin.
    plain = re.sub(r"[*#_`>]+", "", text).replace("→", " then ")
    plain = re.sub(r"\s+", " ", plain).strip()[:650]
    with tempfile.TemporaryDirectory(prefix="kin-talk-") as temp:
        output = Path(temp) / "answer.wav"
        try:
            subprocess.run(
                [cmd, "-v", "en-us", "-s", "160", "-w", str(output), "--stdin"],
                input=plain.encode("utf-8"), capture_output=True,
                timeout=15, check=True)
            spoken = output.read_bytes()
        except (OSError, subprocess.SubprocessError) as exc:
            raise VoiceUnavailable("Local speech output failed") from exc
        if not spoken.startswith(b"RIFF") or len(spoken) <= 44:
            raise VoiceUnavailable("Speech engine did not produce a playable WAV")
        return spoken


def _is_resolution_request(question: str) -> bool:
    q = question.lower()
    return any(token in q for token in (
        "resolve", "fix my conflict", "fix this conflict", "fix the conflict",
        "solve my conflict", "move ", "reschedule", "rearrange", "another time",
        "different time", "change the time",
    ))


def local_voice_answer(
    question: str,
    workspace_commitments: list[dict[str, Any]],
    all_kin_commitments: list[dict[str, Any]],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Explain scheduling issues and propose times using only KIN local rules.

    Always returns advice, never an action or approval. Proposals use all the
    user's supplied KIN workspaces to avoid a false 'free' slot.
    """
    q = (question or "").strip()
    if not 3 <= len(q) <= 500:
        raise ValueError("Use a question between 3 and 500 characters")
    clock = (now or datetime.now(MICHIGAN)).astimezone(MICHIGAN)
    if not _is_resolution_request(q):
        context = (all_kin_commitments if any(
            token in q.lower() for token in ("conflict", "clash", "overlap"))
                   else workspace_commitments)
        return {
            "answer": answer_with_rules(q, context, now=clock),
            "suggestions": [], "target_id": None,
        }

    active = [
        item for item in workspace_commitments
        if item.get("scheduling_mode", "fixed") == "flexible"
        and item.get("status") not in ("canceled", "completed")
        and parse_dt(item["end"]).astimezone(MICHIGAN) >= clock
    ]
    pairs = detect_internal_conflicts(all_kin_commitments)
    conflicted_ids = {p["a_id"] for p in pairs} | {p["b_id"] for p in pairs}
    possible = [c for c in active if c["id"] in conflicted_ids]
    matching = [
        c for c in active if c.get("title", "").strip().lower()
        and c["title"].strip().lower() in q.lower()
    ]
    if matching:
        preferred = matching
    elif possible:
        preferred = possible
    else:
        preferred = active
    if not preferred:
        return {
            "answer": (
                "I can't move a fixed class, work shift or protected commitment. "
                "In Planner, mark something genuinely movable as Flexible and "
                "open Resolve conflicts. I haven't changed anything."
            ), "suggestions": [], "target_id": None,
        }

    selected = sorted(preferred, key=lambda c: parse_dt(c["start"]))[0]
    slots = suggest_alternative_slots(
        all_kin_commitments, selected["id"], days_ahead=7,
        max_results=3, not_before=clock)
    if not slots:
        return {
            "answer": (
                f"I found {selected['title']}, but no alternative free slots "
                "in the searched time window. Try the wider planning options "
                "in Planner. Nothing was changed."
            ), "suggestions": [], "target_id": selected["id"],
        }
    choices = []
    for slot in slots:
        stamp = parse_dt(slot["start"]).astimezone(MICHIGAN)
        choices.append(f"{stamp:%a %b %d at %I:%M %p}")
    answer = (
        f"I can suggest moving {selected['title']}. Available options in your "
        f"stored KIN workspaces include {', '.join(choices)}. "
        "These are not verified commute times or checks against external calendars. "
        "Open Planner, then Resolve conflicts to review and approve a move. "
        "I haven't changed anything."
    )
    return {"answer": answer, "suggestions": slots, "target_id": selected["id"]}
