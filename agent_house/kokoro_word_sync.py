#!/usr/bin/env python3
"""Kokoro-82M GPU Voice Synthesis + Silence Trimmer + mlx_whisper Word-Level Forced Timestamps.

Run under `/Users/mdgolamrabbani/mcp-servers/mlx-audio/.venv/bin/python`.
Produces:
- Broadcast-EQ, tight-paced voiceover WAV (zero awkward dead-air gaps)
- Exact millisecond word timestamps [{"word": "...", "start": 0.14, "end": 0.36}, ...]
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf


def synthesize_with_word_timestamps(
    *,
    script_text: str,
    out_wav: Path,
    out_words_json: Path,
    voice: str = "am_fenrir",
    speed: float = 1.12,
) -> dict[str, Any]:
    from mlx_audio.tts.utils import load_model  # type: ignore
    import mlx_whisper  # type: ignore

    model = load_model("mlx-community/Kokoro-82M-bf16")
    chunks: list[np.ndarray] = []
    sr = 24000
    for res in model.generate(text=script_text, voice=voice, speed=speed, lang_code="a"):
        audio = np.asarray(res.audio, dtype=np.float32).reshape(-1)
        sr = int(getattr(res, "sample_rate", 24000))
        chunks.append(audio)
    if not chunks:
        raise RuntimeError("Kokoro generated empty audio")

    full_audio = np.concatenate(chunks)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        raw_wav = Path(td) / "raw.wav"
        sf.write(str(raw_wav), full_audio, sr)
        # Tight broadcast vocal chain: remove awkward silences > 0.24s, warm condenser EQ, smooth compression
        af = (
            "silenceremove=stop_periods=-1:stop_duration=0.22:stop_threshold=-42dB,"
            "highpass=f=78,"
            "equalizer=f=185:t=q:w=1.2:g=3.0,"
            "equalizer=f=3200:t=q:w=1.5:g=-1.6,"
            "acompressor=threshold=-17dB:ratio=2.8:attack=8:release=110,"
            "apad=pad_dur=0.35"
        )
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(raw_wav), "-af", af, "-ar", "44100", "-ac", "1", str(out_wav)],
            check=True,
        )

    # Run Apple Silicon mlx_whisper for exact millisecond word timestamps
    w_res = mlx_whisper.transcribe(
        str(out_wav),
        path_or_hf_repo="mlx-community/whisper-small-mlx",
        word_timestamps=True,
    )
    words: list[dict[str, Any]] = []
    for seg in w_res.get("segments", []):
        for w in seg.get("words", []):
            txt = str(w.get("word", "")).strip()
            if not txt:
                continue
            words.append(
                {
                    "word": txt,
                    "start": round(float(w.get("start", 0.0)), 3),
                    "end": round(float(w.get("end", 0.0)), 3),
                }
            )

    data_probe, sr_out = sf.read(str(out_wav), always_2d=False)
    duration = round(len(data_probe) / sr_out, 3)
    payload = {
        "voice": f"kokoro_mlx:{voice}",
        "speed": speed,
        "duration_sec": duration,
        "word_count": len(words),
        "wpm": round((len(words) / max(1.0, duration)) * 60.0, 1),
        "words": words,
    }
    out_words_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    res = synthesize_with_word_timestamps(
        script_text=cfg["script_text"],
        out_wav=Path(cfg["out_wav"]),
        out_words_json=Path(cfg["out_words_json"]),
        voice=cfg.get("voice", "am_fenrir"),
        speed=float(cfg.get("speed", 1.12)),
    )
    print(json.dumps({k: v for k, v in res.items() if k != "words"}, indent=2))
