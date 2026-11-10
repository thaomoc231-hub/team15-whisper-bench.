# Integration Contract v1.0 — Hung and Hue

## Scope

Hung's component provides audio normalization and CPU Whisper transcription. Hue's measurement program invokes the transcription process, measures its execution, calculates WER, and saves CSV results. The measurement program is outside the scope of this component.

## Inputs

- `prepare`: a video or audio file with an audio track, and a new output WAV path. The first audio track is selected.
- `transcribe`: a nonempty, untruncated mono WAV file containing signed 16-bit PCM audio at 16000 Hz; a previously downloaded local Whisper `.pt` checkpoint; a language code such as `ko`, `vi`, or `en`; and positive `threads` and `beam-size` values.
- Initial model baseline: **multilingual tiny**. Default settings are CPU, fp32, `threads=4`, `beam_size=5`, `temperature=0`, `task=transcribe`, and `condition_on_previous_text=False`. Keep the agreed settings fixed across comparison runs.
- The transcription worker does not download models. Each invocation requires an output directory that does not already exist.

## Process Contract

```bash
python -m subtitle_bench.cli transcribe --audio AUDIO.wav --model TINY.pt --language ko --threads 4 --beam-size 5 --output NEW_RESULT_DIR
```

- Exit code `0`: all output files have been written, and `result.json` contains `status=complete`.
- Exit code `1`: a handled installation, input, or runtime error.
- Exit code `2`: an argument parsing error. Signals and unexpected runtime failures may also produce other nonzero exit codes.

The caller must treat **every nonzero exit code as a failed run**, preserve stdout and stderr, and exclude that run from successful-run statistics.

On success, stdout contains the output directory path. Error messages are written to stderr. Use a fresh Python process for each measurement. Do not benchmark multiple engines concurrently on the same machine.

## Outputs

| File | Contents |
|---|---|
| `transcript.txt` | UTF-8 segment text joined with spaces, preserving case and punctuation; WER normalization is not applied automatically |
| `subtitles.srt` | Subtitles based on Whisper segments, with timestamps formatted as `HH:MM:SS,mmm` |
| `segments.json` | Metadata and a list of `{start, end, text}` records; times are in seconds |
| `result.json` | `schema_version=1.0`, `status=complete`, `audio_seconds`, `settings`, and `outputs` |

`settings` includes audio and model paths and their SHA-256 hashes, device, precision, language, thread count, beam size, and the integration version.

`outputs` records the **relative** path, byte count, and SHA-256 hash of each of the three output files. Call `verify_result(output)` or run `lecture-subtitles verify OUTPUT` before consuming the result. Hash verification detects modified files; it does not replace listening to the audio and checking transcript accuracy or subtitle timing.

For audio without speech, a complete manifest with empty TXT/SRT output can be a valid technical result. The acceptance script requires nonempty output when testing a sample that contains speech.

## Measurement Boundary

See `examples/partner_adapter.py`. Measure around the subprocess that runs `transcribe`; perform result verification and WER calculation afterward.

This interval includes Python startup, imports, WAV validation and reading, model loading, recognition, hashing, and output writing. It is **whole-process execution time**, not inference-only time. It excludes model downloading, FFmpeg preparation, and WER calculation.

If the team wants to exclude hashing or output I/O, or measure inference only, it must agree on a different measurement interface for both engines.

Record the machine, model family, audio input, language, thread count, and decoding settings alongside Hue's CSV results. Matching settings does not guarantee identical decoder internals or identical transcripts across engines.

## Decisions Still Required from the Team

- Assign responsibility for implementing the faster-whisper runner.
- Select the final model size and evaluation clips.
- Prepare reference transcripts reviewed by both members.
- Agree on WER normalization, repetition count, warmup policy, and RAM measurement method.

Do not use Whisper-generated subtitles as the ground-truth reference.
