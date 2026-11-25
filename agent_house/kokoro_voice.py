"""Batch Apple Silicon MLX Kokoro-82M-bf16 human documentary voice synthesizer.

Loads Kokoro-82M-bf16 ONCE on Apple Silicon GPU and synthesizes a list of scene
narrations into crisp 24kHz WAV files ($0 cost, zero API keys, natural human prosody).

Usage (invoked automatically by agent_house/cinema_shorts.py via mlx-audio venv):
    /Users/mdgolamrabbani/mcp-servers/mlx-audio/.venv/bin/python -m agent_house.kokoro_voice <jobs.json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def run_batch(jobs_path: Path) -> None:
    import numpy as np
    import soundfile as sf
    from mlx_audio.tts.utils import load_model

    spec = json.loads(jobs_path.read_text(encoding="utf-8"))
    model_id = spec.get("model_id", "mlx-community/Kokoro-82M-bf16")
    voice = spec.get("voice", "am_fenrir")
    speed = float(spec.get("speed", 0.96))
    lang_code = spec.get("lang_code", "a")

    model = load_model(model_id)
    results = []
    for item in spec["items"]:
        chunks = []
        for res in model.generate(
            text=item["text"],
            voice=voice,
            speed=speed,
            lang_code=lang_code,
        ):
            arr = np.asarray(res.audio, dtype=np.float32).reshape(-1)
            if arr.size > 0:
                chunks.append(arr)
        audio = np.concatenate(chunks) if chunks else np.zeros(2400, dtype=np.float32)
        out_wav = Path(item["out_wav"])
        out_wav.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(out_wav), audio, 24000)
        results.append({"out_wav": str(out_wav), "duration_sec": round(len(audio) / 24000.0, 3)})

    print(json.dumps({"engine": f"kokoro_mlx:{voice}", "items": results}))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: kokoro_voice.py <jobs.json>")
    run_batch(Path(sys.argv[1]))
