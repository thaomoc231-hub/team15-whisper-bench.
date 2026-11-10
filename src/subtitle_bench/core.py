"""FFmpeg audio preparation, provenance, and Unicode subtitle output."""

import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import wave
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def wav_duration(path):
    try:
        with wave.open(str(path), "rb") as audio:
            if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, 16000):
                raise ValueError("Audio must be mono, signed 16-bit PCM, 16000 Hz; use prepare first")
            frames = audio.getnframes()
            duration = frames / audio.getframerate()
            # Reject truncated files, rather than trusting only the WAV header.
            count = 0
            while block := audio.readframes(65536):
                count += len(block)
            if count != frames * 2:
                raise ValueError("WAV payload is truncated")
    except (wave.Error, EOFError) as exc:
        raise ValueError(f"Invalid WAV audio: {path}") from exc
    if duration <= 0:
        raise ValueError("Audio is empty")
    return duration


def prepare(source, target):
    source, target = Path(source).resolve(), Path(target).resolve()
    if not source.is_file():
        raise ValueError(f"Input not found: {source}")
    provenance = target.with_suffix(".prepare.json")
    if source == target or target.exists() or provenance.exists():
        raise ValueError("Choose a new output WAV path; existing files are preserved")
    if not shutil.which("ffmpeg"):
        raise ValueError("FFmpeg is missing; install ffmpeg first")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Stage beside the destination and publish without overwriting another run.
    handle, temporary_name = tempfile.mkstemp(prefix=".preparing-", suffix=".wav", dir=target.parent)
    os.close(handle)
    temporary = Path(temporary_name)
    command = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(source),
               "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000",
               "-c:a", "pcm_s16le", "-f", "wav", str(temporary)]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        duration = wav_duration(temporary)
        source_hash, audio_hash = sha256(source), sha256(temporary)
        os.link(temporary, target)
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"FFmpeg failed: {exc.stderr.strip()}") from exc
    finally:
        temporary.unlink(missing_ok=True)
    write_json(provenance, {
        "source": str(source), "source_sha256": source_hash,
        "audio": str(target), "audio_sha256": audio_hash,
        "duration_seconds": duration, "command": command,
        "note": "FFmpeg wrote a temporary WAV; the validated file was published at audio path",
    })
    return target


def timestamp(seconds):
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError("Invalid subtitle timestamp")
    milliseconds = round(seconds * 1000)
    seconds, ms = divmod(milliseconds, 1000)
    minutes, sec = divmod(seconds, 60)
    hours, minute = divmod(minutes, 60)
    return f"{hours:02d}:{minute:02d}:{sec:02d},{ms:03d}"


def export_segments(directory, segments, metadata):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    cleaned = []
    for segment in segments:
        text = " ".join(segment["text"].split())
        start, end = float(segment["start"]), float(segment["end"])
        if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end < start:
            raise ValueError("Invalid segment interval")
        if text:
            cleaned.append({"start": start, "end": end, "text": text})
    (directory / "transcript.txt").write_text(
        " ".join(s["text"] for s in cleaned) + "\n", encoding="utf-8")
    srt = "\n\n".join(
        f"{i}\n{timestamp(s['start'])} --> {timestamp(s['end'])}\n{s['text']}"
        for i, s in enumerate(cleaned, 1))
    (directory / "subtitles.srt").write_text(srt + ("\n" if srt else ""), encoding="utf-8")
    write_json(directory / "segments.json", {"metadata": metadata, "segments": cleaned})


def result_manifest(directory, metadata, duration):
    """Completion record consumed by the partner, written after every output exists."""
    directory = Path(directory)
    outputs = {name: {"path": name, "sha256": sha256(directory / name),
                      "bytes": (directory / name).stat().st_size}
               for name in ["transcript.txt", "subtitles.srt", "segments.json"]}
    manifest = {"schema_version": "1.0", "status": "complete", "engine": "whisper",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "audio_seconds": duration, "settings": metadata, "outputs": outputs}
    write_json(directory / "result.json", manifest)
    return manifest


def verify_result(directory):
    directory = Path(directory).resolve()
    result = json.loads((directory / "result.json").read_text(encoding="utf-8"))
    if result.get("schema_version") != "1.0" or result.get("status") != "complete":
        raise ValueError("Unsupported or incomplete result manifest")
    for name in ["transcript.txt", "subtitles.srt", "segments.json"]:
        record = result["outputs"][name]
        if record["path"] != name:
            raise ValueError(f"Unexpected output path for {name}")
        path = directory / name
        if path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
            raise ValueError(f"Result integrity check failed: {name}")
    return result


def environment():
    packages = {}
    for name in ["openai-whisper", "torch", "numpy"]:
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    cpu_info = Path("/proc/cpuinfo")
    model = next((line.split(":", 1)[1].strip() for line in cpu_info.read_text().splitlines()
                  if line.startswith("model name")), "unknown") if cpu_info.exists() else platform.processor()
    return {"platform": platform.platform(), "python": sys.version, "cpu": model,
            "os_release": Path("/etc/os-release").read_text() if Path("/etc/os-release").exists() else "unknown",
            "memory": Path("/proc/meminfo").read_text() if Path("/proc/meminfo").exists() else "unknown",
            "packages": packages,
            "ffmpeg": subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.splitlines()[0]
            if shutil.which("ffmpeg") else None}
