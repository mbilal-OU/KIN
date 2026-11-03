"""Offline tests for local speech I/O and voice-directed conflict advice.

Models and OS speech binaries are simulated: no API calls, audio uploads,
model downloads or actual system TTS are required by CI.
"""
from copy import deepcopy
from datetime import datetime
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import wave

import pytest

from kin_models import make_commitment
from kin_voice import (
    VoiceUnavailable, _check_audio, local_voice_answer,
    synthesize_local, transcribe_local,
)


def wav_seconds(duration=1, sample_rate=16000):
    data = BytesIO()
    with wave.open(data, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\0\0" * int(sample_rate * duration))
    return data.getvalue()


def event(title, start, end, *, ws, mode="fixed", status="planned"):
    record = make_commitment(
        title, start, end, workspace_id=ws,
        status=status, event_type="personal")
    record["scheduling_mode"] = mode
    return record


class FakeWhisper:
    def __init__(self, result="How do I resolve my schedule conflict?"):
        self.result = result
        self.temporary = None

    def transcribe(self, filename, **kwargs):
        self.temporary = filename
        assert Path(filename).exists()
        assert Path(filename).read_bytes().startswith(b"RIFF")
        assert kwargs["language"] == "en"
        return iter([SimpleNamespace(text=self.result)]), None


def test_voice_transcribes_locally_and_deletes_temp_audio():
    fake = FakeWhisper()
    assert transcribe_local(wav_seconds(), model=fake) == fake.result
    assert not Path(fake.temporary).exists()


def test_voice_rejects_broken_empty_and_oversized_audio():
    for payload in (b"", b"not a wav", b"n" * 3_000_001):
        with pytest.raises(ValueError):
            transcribe_local(payload, model=FakeWhisper())


def test_voice_rejects_long_recordings():
    with pytest.raises(ValueError, match="30 seconds"):
        _check_audio(wav_seconds(31))


def test_voice_rejects_no_recognized_speech():
    with pytest.raises(ValueError, match="clear speech"):
        transcribe_local(wav_seconds(), model=FakeWhisper(result=""))


def test_tts_requires_local_engine(monkeypatch):
    import kin_voice
    monkeypatch.setattr(kin_voice.shutil, "which", lambda path: None)
    with pytest.raises(VoiceUnavailable, match="eSpeak NG"):
        synthesize_local("Hello, this is KIN")


def test_tts_creates_ephemeral_wav_without_using_shell(monkeypatch):
    import kin_voice

    inspected = {"path": None, "stdin": None}

    def fake_run(command, **kwargs):
        assert command[0] == "/mock/espeak-ng"
        assert kwargs["timeout"] == 15 and kwargs["check"]
        assert command[-1] == "--stdin"
        inspected["stdin"] = kwargs["input"]
        out = Path(command[command.index("-w") + 1])
        inspected["path"] = out
        out.write_bytes(wav_seconds())
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(kin_voice.subprocess, "run", fake_run)
    audio = synthesize_local("KIN is speaking now.", executable="/mock/espeak-ng")
    assert audio.startswith(b"RIFF")
    assert inspected["stdin"] == b"KIN is speaking now."
    assert not inspected["path"].exists()


def test_voice_proposes_alternatives_across_workspaces_without_changes():
    gym = event("Gym", "2026-11-04T10:00:00-05:00",
                "2026-11-04T11:00:00-05:00", ws="Personal", mode="flexible")
    lab = event("University lab", "2026-11-04T10:30:00-05:00",
                "2026-11-04T12:00:00-05:00", ws="University")
    records = [gym, lab]
    original = deepcopy(records)
    response = local_voice_answer(
        "Help me resolve my gym conflict", [gym], records,
        now=datetime.fromisoformat("2026-11-03T08:00:00-05:00"))
    assert response["target_id"] == gym["id"]
    assert response["suggestions"]
    assert "Gym" in response["answer"]
    assert "haven't changed anything" in response["answer"]
    assert records == original
    assert not (response["suggestions"][0]["start"] == gym["start"])


def test_conflicts_include_events_from_other_kin_workspace():
    a = event("Class", "2026-11-04T10:00:00-05:00",
              "2026-11-04T11:00:00-05:00", ws="University")
    b = event("Shift", "2026-11-04T10:30:00-05:00",
              "2026-11-04T11:30:00-05:00", ws="Work")
    reply = local_voice_answer(
        "Do I have any conflicts?", [a], [a, b],
        now=datetime.fromisoformat("2026-11-03T08:00:00-05:00"))
    assert "Class overlaps Shift" in reply["answer"]
    assert reply["suggestions"] == []


def test_fixed_events_are_not_rescheduled_by_voice():
    a = event("Exam", "2026-11-04T10:00:00-05:00",
              "2026-11-04T11:00:00-05:00", ws="University")
    b = event("Shift", "2026-11-04T10:30:00-05:00",
              "2026-11-04T11:30:00-05:00", ws="Work")
    result = local_voice_answer(
        "Please reschedule my exam", [a], [a, b],
        now=datetime.fromisoformat("2026-11-03T08:00:00-05:00"))
    assert not result["suggestions"]
    assert result["target_id"] is None
    assert "fixed or protected" in result["answer"]
    assert "haven't changed anything" in result["answer"]


def test_open_ended_questions_fall_back_to_local_rules():
    tomorrow = event("Study group", "2026-11-04T12:00:00-05:00",
                     "2026-11-04T13:00:00-05:00", ws="Study")
    result = local_voice_answer(
        "What's on my schedule tomorrow?", [tomorrow], [tomorrow],
        now=datetime.fromisoformat("2026-11-03T08:00:00-05:00"))
    assert "Study group" in result["answer"]
    assert result["target_id"] is None


def test_voice_rejects_empty_command():
    with pytest.raises(ValueError):
        local_voice_answer("", [], [])


def test_named_fixed_event_is_not_substituted_with_other_flexible_event():
    exam = event("Exam", "2026-11-04T10:00:00-05:00",
                 "2026-11-04T11:00:00-05:00", ws="School")
    gym = event("Gym", "2026-11-04T10:30:00-05:00",
                "2026-11-04T11:30:00-05:00", ws="School", mode="flexible")
    reply = local_voice_answer(
        "Please move my exam", [exam, gym], [exam, gym],
        now=datetime.fromisoformat("2026-11-03T08:00:00-05:00"))
    assert reply["suggestions"] == []
    assert reply["target_id"] is None
    assert "Exam" in reply["answer"] and "fixed or protected" in reply["answer"]


def test_voice_asks_which_flexible_event_when_multiple_are_possible():
    gym = event("Gym", "2026-11-04T10:00:00-05:00",
                "2026-11-04T11:00:00-05:00", ws="Personal", mode="flexible")
    study = event("Study", "2026-11-04T11:00:00-05:00",
                  "2026-11-04T12:00:00-05:00", ws="Personal", mode="flexible")
    lab = event("Lab", "2026-11-04T10:30:00-05:00",
                "2026-11-04T11:30:00-05:00", ws="University")
    answer = local_voice_answer(
        "Resolve my conflicts", [gym, study], [gym, study, lab],
        now=datetime.fromisoformat("2026-11-03T08:00:00-05:00"))
    assert answer["suggestions"] == []
    assert answer["target_id"] is None
    assert "Please name the specific one" in answer["answer"]
