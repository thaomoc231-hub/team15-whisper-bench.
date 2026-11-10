"""Local acceptance run with REAL pretrained weights; does not fabricate results.

python scripts/acceptance.py --model models/tiny.pt --output results/acceptance-01
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from subtitle_bench.core import verify_result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--input", default=str(Path(__file__).resolve().parents[1] / "examples/sample/jfk.flac"))
    parser.add_argument("--language", default="en")
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    command = [sys.executable, "-m", "subtitle_bench.cli", "run", "--input", args.input,
               "--model", args.model, "--language", args.language, "--threads", str(args.threads),
               "--output", str(output)]
    # Avoid output-directory reuse, including failed attempts. Keep logs beside it.
    if output.exists():
        parser.error("Output already exists; select a new name")
    output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(command, capture_output=True, text=True)
    output.with_name(output.name + ".stdout.log").write_text(completed.stdout, encoding="utf-8")
    output.with_name(output.name + ".stderr.log").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode:
        print(completed.stderr, file=sys.stderr)
        return 1
    manifest = verify_result(output / "whisper")
    transcript = (output / "whisper/transcript.txt").read_text(encoding="utf-8").strip()
    # This sample contains speech: an empty transcript cannot pass acceptance.
    if not transcript or not (output / "whisper/subtitles.srt").stat().st_size:
        print("FAIL: Empty transcript/subtitles for speech input", file=sys.stderr)
        return 1
    report = {"status": "technical_acceptance_passed", "transcript": transcript,
              "output": str(output), "audio_seconds": manifest["audio_seconds"],
              "manual_review_required": "Listen to audio; check transcript and subtitle timing. This is not a WER/benchmark result."}
    (output / "acceptance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
