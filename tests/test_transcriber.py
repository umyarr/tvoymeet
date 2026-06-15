import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from transcriber import _srt_t, _vtt_t, build_ffmpeg_cmd, build_md_text


# ── _srt_t ───────────────────────────────────────────────────────────────────

def test_srt_zero():
    assert _srt_t(0.0) == "00:00:00,000"

def test_srt_seconds():
    assert _srt_t(5.5) == "00:00:05,500"

def test_srt_minutes():
    assert _srt_t(90.0) == "00:01:30,000"

def test_srt_hours():
    assert _srt_t(3661.25) == "01:01:01,250"

def test_srt_milliseconds():
    assert _srt_t(1.001) == "00:00:01,001"


# ── _vtt_t ───────────────────────────────────────────────────────────────────

def test_vtt_uses_dot():
    assert "," not in _vtt_t(5.5)
    assert _vtt_t(5.5) == "00:00:05.500"

def test_vtt_matches_srt_except_comma():
    assert _vtt_t(90.123) == _srt_t(90.123).replace(",", ".")


# ── build_ffmpeg_cmd ─────────────────────────────────────────────────────────

def test_ffmpeg_full_mp3():
    cmd = build_ffmpeg_cmd("C:/audio/source.mp3", "mp3", "64k", False, "", "")
    assert "ffmpeg" in cmd[0]
    assert "-ss" not in cmd
    assert "-c:a" in cmd
    assert "libmp3lame" in cmd
    assert "64k" in cmd
    assert cmd[-1].endswith("_audio.mp3")

def test_ffmpeg_fragment_with_end():
    cmd = build_ffmpeg_cmd("C:/audio/source.mp3", "mp3", "64k", True, "00:01:00", "00:10:00")
    assert "-ss" in cmd
    assert "00:01:00" in cmd
    assert "-to" in cmd
    assert "00:10:00" in cmd

def test_ffmpeg_fragment_no_end():
    cmd = build_ffmpeg_cmd("C:/audio/source.mp3", "mp3", "64k", True, "00:01:00", "")
    assert "-ss" in cmd
    assert "-to" not in cmd

def test_ffmpeg_wav():
    cmd = build_ffmpeg_cmd("C:/audio/source.mp4", "wav", "64k", False, "", "")
    assert "pcm_s16le" in cmd
    assert "libmp3lame" not in cmd
    assert cmd[-1].endswith("_audio.wav")

def test_ffmpeg_output_path():
    cmd = build_ffmpeg_cmd("C:/work/meeting.mp4", "mp3", "96k", False, "", "")
    assert cmd[-1] == str(Path("C:/work/meeting_audio.mp3"))


# ── build_md_text ────────────────────────────────────────────────────────────

def test_md_contains_transcript():
    data = {"text": "Привет мир", "language": "ru", "duration": 120.0}
    md = build_md_text(data, "test_file")
    assert "Привет мир" in md
    assert "test_file" in md
    assert "ru" in md
    assert "2.0 мин" in md

def test_md_has_llm_prompt():
    data = {"text": "текст", "language": "en", "duration": 60.0}
    md = build_md_text(data, "x")
    assert "Prompt для LLM" in md
    assert "Ключевые идеи" in md
    assert "инфографики" in md

def test_md_empty_text():
    data = {"text": "", "language": "ru", "duration": 0.0}
    md = build_md_text(data, "empty")
    assert "Транскрипт: empty" in md
    assert "0.0 мин" in md

def test_md_missing_fields():
    md = build_md_text({}, "no_fields")
    assert "Транскрипт: no_fields" in md
    assert "?" in md  # language fallback
