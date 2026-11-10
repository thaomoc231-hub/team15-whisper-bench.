"""Whisper CPU runner. Completes TXT/SRT export before returning success."""

import os
import shutil
import tempfile
from pathlib import Path

from . import __version__
from .core import export_segments, result_manifest, sha256, wav_duration


def transcribe(audio, model, language, threads, beam_size, output):
    audio, model, output = Path(audio).resolve(), Path(model).resolve(), Path(output).resolve()
    duration = wav_duration(audio)
    if not model.is_file() or model.suffix != ".pt":
        raise ValueError(f"Expected an existing local Whisper .pt checkpoint: {model}")
    if output.exists():
        raise ValueError(f"Output already exists: {output}. Choose a new directory.")
    if threads < 1 or beam_size < 1:
        raise ValueError("threads and beam-size must be positive")
    # Set before importing the inference runtime. No downloads in this runner.
    os.environ.update({"OMP_NUM_THREADS": str(threads), "MKL_NUM_THREADS": str(threads),
                       "OPENBLAS_NUM_THREADS": str(threads)})
    import torch
    import whisper

    if language not in whisper.tokenizer.LANGUAGES:
        raise ValueError(f"Unsupported language code: {language}")
    torch.set_num_threads(threads)
    # Fresh CLI processes are preferred. Repeated library calls may already have
    # initialized the interop pool, in which case PyTorch disallows changing it.
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    recognizer = whisper.load_model(str(model), device="cpu")
    result = recognizer.transcribe(
        str(audio), language=language, task="transcribe", fp16=False,
        temperature=0.0, beam_size=beam_size, condition_on_previous_text=False,
        verbose=None,
    )
    # Stage output so a failed export cannot look like a completed result.
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".transcribing-", dir=output.parent))
    try:
        metadata = {
            "integration_version": __version__,
            "engine": "whisper", "model_path": str(model), "audio_path": str(audio),
            "language": language, "threads": threads, "beam_size": beam_size,
            "device": "cpu", "precision": "float32", "temperature": 0.0,
            "condition_on_previous_text": False, "task": "transcribe",
            "audio_sha256": sha256(audio), "model_sha256": sha256(model),
        }
        export_segments(temporary, result["segments"], metadata)
        result_manifest(temporary, metadata, duration)
        if output.exists():
            raise ValueError(f"Output was created by another process: {output}")
        temporary.rename(output)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return output
