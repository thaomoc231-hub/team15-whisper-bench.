import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import __version__
from .core import environment, prepare, verify_result, write_json


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def main():
    parser = argparse.ArgumentParser(description="Hung / Team 15: FFmpeg + Whisper CPU subtitles")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Show environment and installed versions")
    p = sub.add_parser("prepare", help="Extract mono 16 kHz PCM WAV using FFmpeg")
    p.add_argument("input")
    p.add_argument("output")
    p = sub.add_parser("transcribe", help="Local Whisper checkpoint -> TXT/SRT/JSON on CPU")
    for name in ["audio", "model", "language", "output"]:
        p.add_argument(f"--{name}", required=True)
    p.add_argument("--threads", type=positive, default=4)
    p.add_argument("--beam-size", type=positive, default=5)
    p = sub.add_parser("run", help="Video -> standard WAV -> Whisper subtitles in a new directory")
    for name in ["input", "model", "language", "output"]:
        p.add_argument(f"--{name}", required=True)
    p.add_argument("--threads", type=positive, default=4)
    p.add_argument("--beam-size", type=positive, default=5)
    p = sub.add_parser("verify", help="Validate completed result and print manifest as JSON")
    p.add_argument("directory")
    p = sub.add_parser("fetch-model", help="Download official Whisper weights before use/measurement")
    p.add_argument("--model", choices=["tiny", "base", "small"], default="tiny")
    p.add_argument("--directory", default="models")
    args = parser.parse_args()
    try:
        if args.command == "doctor":
            print(json.dumps(environment(), ensure_ascii=False, indent=2))
        elif args.command == "prepare":
            print(prepare(args.input, args.output))
        elif args.command == "transcribe":
            from .worker import transcribe
            print(transcribe(**{k: v for k, v in vars(args).items() if k != "command"}))
        elif args.command == "run":
            from .worker import transcribe
            output = Path(args.output).resolve()
            if not Path(args.model).is_file():
                raise ValueError("Local model missing; run fetch-model first")
            if not Path(args.input).is_file():
                raise ValueError("Input video missing")
            output.mkdir(parents=True, exist_ok=False)
            write_json(output / "environment.json", environment())
            audio = prepare(args.input, output / "audio.wav")
            print(transcribe(audio, args.model, args.language, args.threads, args.beam_size,
                             output / "whisper"))
        elif args.command == "verify":
            print(json.dumps(verify_result(args.directory), ensure_ascii=False, indent=2))
        elif args.command == "fetch-model":
            import whisper
            from .core import sha256
            directory = Path(args.directory).resolve()
            directory.mkdir(parents=True, exist_ok=True)
            url = whisper._MODELS[args.model]
            model = whisper._download(url, str(directory), False)
            write_json(directory / f"{args.model}.provenance.json", {
                "model": args.model, "source": url, "sha256": sha256(model),
                "whisper_version": environment()["packages"]["openai-whisper"],
            })
            print(model)
    except (ValueError, OSError, ImportError, RuntimeError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
