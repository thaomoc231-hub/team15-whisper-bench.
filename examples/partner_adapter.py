"""Copy this invocation into Hue's measurement tool. No benchmark math here.

Run AFTER installing the project: python examples/partner_adapter.py --help
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from subtitle_bench.core import verify_result


def invoke_whisper(audio, model, language, output, threads=4, beam_size=5):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Each run requires a NEW output directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "subtitle_bench.cli", "transcribe",
               "--audio", str(Path(audio).resolve()), "--model", str(Path(model).resolve()),
               "--language", language, "--threads", str(threads),
               "--beam-size", str(beam_size), "--output", str(output)]
    # Hue can place the timing/RAM measurement around THIS subprocess.
    # Do not include model download, FFmpeg, or result verification in that timer.
    completed = subprocess.run(command, capture_output=True, text=True)
    output.with_name(output.name + ".stdout.log").write_text(completed.stdout, encoding="utf-8")
    output.with_name(output.name + ".stderr.log").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode:
        raise RuntimeError(f"Whisper failed (exit {completed.returncode}); see {output}.stderr.log")
    manifest = verify_result(output)
    return {
        "transcript_path": str(output / "transcript.txt"),
        "subtitle_path": str(output / "subtitles.srt"),
        "audio_seconds": manifest["audio_seconds"],
        "settings": manifest["settings"],
        "manifest_path": str(output / "result.json"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ["audio", "model", "language", "output"]:
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--beam-size", type=int, default=5)
    try:
        print(json.dumps(invoke_whisper(**vars(parser.parse_args())), ensure_ascii=False, indent=2))
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        print(f"Adapter error: {exc}", file=sys.stderr)
        raise SystemExit(1)
