#!/usr/bin/env python3
"""Procedural Broadcast Foley & Viral Shorts SFX Mixer (NumPy/SciPy, $0).

Generates punchy, rhythm-synced viral Shorts audio layers:
- Sub-bass impact booms (hook + reveal hits)
- Whip-pan filtered whooshes (every rapid cut)
- Crisp UI pop/tick SFX (animated counters, badges, callouts)
- Cinematic tension risers leading into payoffs
- Pulsing rhythmic dark underscore, sidechain-ducked under voiceover & mastered to -14 LUFS.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from scipy.signal import butter, lfilter

SR = 44100


def _bandpass(sig: np.ndarray, low: float, high: float, sr: int = SR) -> np.ndarray:
    nyq = 0.5 * sr
    b, a = butter(3, [max(0.001, low / nyq), min(0.99, high / nyq)], btype="band")
    return lfilter(b, a, sig)


def _lowpass(sig: np.ndarray, cutoff: float, sr: int = SR) -> np.ndarray:
    nyq = 0.5 * sr
    b, a = butter(3, min(0.99, cutoff / nyq), btype="low")
    return lfilter(b, a, sig)


def synth_boom(dur: float = 0.55) -> np.ndarray:
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    freq = 115.0 * np.exp(-t * 5.8) + 34.0
    phase = 2.0 * np.pi * np.cumsum(freq) / SR
    sub = np.sin(phase) * np.exp(-t * 4.5)
    click = np.random.randn(n) * np.exp(-t * 95.0) * 0.35
    sig = np.tanh((sub * 1.4 + click) * 1.2) * 0.55
    return sig


def synth_whoosh(dur: float = 0.24) -> np.ndarray:
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    env = np.sin(np.pi * t / dur) ** 1.6
    noise = np.random.randn(n)
    low_band = _bandpass(noise, 260, 1400) * (1.0 - t / dur)
    high_band = _bandpass(noise, 1100, 4200) * (t / dur)
    return (low_band * 0.65 + high_band * 0.55) * env * 0.42


def synth_pop(freq: float = 780.0, dur: float = 0.065) -> np.ndarray:
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    f = freq * np.exp(-t * 18.0) + freq * 0.45
    phase = 2.0 * np.pi * np.cumsum(f) / SR
    return np.sin(phase) * np.exp(-t * 48.0) * 0.38


def synth_riser(dur: float = 1.6) -> np.ndarray:
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    prog = t / dur
    freq = 140.0 * (4.2 ** prog)
    phase = 2.0 * np.pi * np.cumsum(freq) / SR
    tone = (np.sin(phase) + 0.35 * np.sin(2 * phase)) * (prog ** 2.2)
    air = _bandpass(np.random.randn(n), 800, 5000) * (prog ** 2.6) * 0.35
    fade_out = np.ones(n)
    tail = min(n, int(0.06 * SR))
    fade_out[-tail:] = np.linspace(1.0, 0.0, tail)
    return (tone * 0.16 + air * 0.28) * fade_out


def synth_bed(dur: float, mood: str = "thriller") -> np.ndarray:
    """Rhythmic pulsing modern Shorts underscore (no flat sine hum!)."""
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)

    if mood == "explainer":
        bpm = 118.0
        chord = [130.81, 196.00, 246.94, 293.66]  # Cmaj9 bright curious
    elif mood == "psychology":
        bpm = 104.0
        chord = [110.00, 130.81, 164.81, 196.00]  # Am7 hypnotic dark
    elif mood == "scale":
        bpm = 122.0
        chord = [98.00, 146.83, 196.00, 233.08]   # Gm propulsive
    else:  # thriller / dark history
        bpm = 108.0
        chord = [82.41, 123.47, 155.56, 196.00]   # Em dark cinematic

    beat_len = 60.0 / bpm
    beat_pos = (t % beat_len) / beat_len

    # Warm analog-like pad with slow breath LFO
    pad = np.zeros(n, dtype=np.float64)
    for idx, f in enumerate(chord):
        lfo = 0.72 + 0.28 * np.sin(2 * np.pi * (0.14 + idx * 0.05) * t)
        pad += np.sin(2 * np.pi * f * t) * lfo * (0.24 / len(chord))
    pad = _lowpass(pad, 780)

    # Subtle rhythmic low-end pulse kick on beats 1 and 3 + crisp tick on off-beats
    pulse_freq = 78.0 * np.exp(-beat_pos * 14.0) + 42.0
    kick = np.sin(2 * np.pi * np.cumsum(pulse_freq) / SR) * np.exp(-beat_pos * 12.0) * 0.14
    hat_pos = ((t + beat_len * 0.5) % beat_len) / beat_len
    hat = _bandpass(np.random.randn(n), 4500, 9500) * np.exp(-hat_pos * 55.0) * 0.032

    bed = pad + kick + hat
    return np.clip(bed, -0.8, 0.8)


def _overlay(buf: np.ndarray, clip: np.ndarray, start_sec: float, gain: float = 1.0) -> None:
    i0 = max(0, int(round(start_sec * SR)))
    if i0 >= len(buf):
        return
    i1 = min(len(buf), i0 + len(clip))
    buf[i0:i1] += clip[: i1 - i0] * gain


def build_viral_master_audio(
    *,
    voice_wav: Path,
    out_m4a: Path,
    events: list[dict[str, Any]],
    mood: str = "thriller",
) -> float:
    """Mix voiceover + sidechain-ducked pulsing bed + cut whooshes/booms/pops -> -14 LUFS M4A."""
    voice, sr = sf.read(str(voice_wav), always_2d=False)
    if voice.ndim > 1:
        voice = voice.mean(axis=1)
    if sr != SR:
        with tempfile.TemporaryDirectory() as td:
            resamp = Path(td) / "v44.wav"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(voice_wav), "-ar", str(SR), "-ac", "1", str(resamp)], check=True)
            voice, _ = sf.read(str(resamp), always_2d=False)

    dur = len(voice) / SR
    bed = synth_bed(dur, mood=mood)
    sfx = np.zeros(len(voice), dtype=np.float64)

    boom = synth_boom()
    whoosh = synth_whoosh()
    pop_hi = synth_pop(880.0)
    pop_lo = synth_pop(620.0)
    riser = synth_riser(1.5)

    for ev in events:
        t = float(ev.get("t", 0.0))
        kind = ev.get("kind", "whoosh")
        gain = float(ev.get("gain", 1.0))
        if kind == "boom":
            _overlay(sfx, boom, t, gain * 0.85)
        elif kind == "whoosh":
            _overlay(sfx, whoosh, max(0.0, t - 0.10), gain * 0.72)
        elif kind == "pop":
            _overlay(sfx, pop_hi, t, gain * 0.65)
        elif kind == "tick":
            _overlay(sfx, pop_lo, t, gain * 0.55)
        elif kind == "riser":
            _overlay(sfx, riser, max(0.0, t - 1.5), gain * 0.8)

    # Smooth RMS envelope of voice for musical sidechain ducking
    win = int(0.12 * SR)
    env = np.sqrt(np.convolve(voice ** 2, np.ones(win) / win, mode="same") + 1e-8)
    duck = np.clip(1.0 - env * 2.6, 0.30, 1.0)
    bed_ducked = bed * duck * 0.55

    # Stereo subtle width: voice centered, bed/sfx slightly wider
    left = voice * 0.96 + bed_ducked * 0.95 + sfx * 0.88
    right = voice * 0.96 + np.roll(bed_ducked, 14) * 0.95 + np.roll(sfx, 8) * 0.88
    stereo = np.stack([left, right], axis=1)
    peak = float(np.max(np.abs(stereo)) + 1e-6)
    if peak > 0.92:
        stereo = stereo * (0.92 / peak)

    with tempfile.TemporaryDirectory() as td:
        raw_mix = Path(td) / "mix.wav"
        sf.write(str(raw_mix), stereo, SR)
        out_m4a.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error",
                "-i", str(raw_mix),
                "-af", "highpass=f=32,loudnorm=I=-14:TP=-1.2:LRA=8",
                "-c:a", "aac", "-b:a", "192k",
                str(out_m4a),
            ],
            check=True,
        )
    return round(dur, 2)
