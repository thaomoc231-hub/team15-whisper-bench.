"""FFmpeg integration and Whisper call-contract tests; no pretrained ASR claims."""

import json
import subprocess
import sys
import tempfile
import types
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from subtitle_bench.core import export_segments, prepare, result_manifest, timestamp, verify_result, wav_duration
from subtitle_bench.worker import transcribe


def wav(path, rate=16000, channels=1):
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(channels)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(b"\0\0" * rate * channels)


class ProjectTests(unittest.TestCase):
    def test_srt_rollover_and_unicode(self):
        self.assertEqual(timestamp(59.9996), "00:01:00,000")
        with tempfile.TemporaryDirectory() as temp:
            export_segments(temp, [{"start": 0, "end": 1.25, "text": "안녕하세요 Việt Nam"}], {})
            self.assertEqual((Path(temp) / "subtitles.srt").read_text(),
                             "1\n00:00:00,000 --> 00:00:01,250\n안녕하세요 Việt Nam\n")
            self.assertEqual((Path(temp) / "transcript.txt").read_text().strip(), "안녕하세요 Việt Nam")

    def test_real_ffmpeg_stereo_resampling_and_preservation(self):
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp) / "source with spaces.wav", Path(temp) / "audio.wav"
            wav(source, rate=44100, channels=2)
            prepare(source, target)
            self.assertAlmostEqual(wav_duration(target), 1, places=2)
            metadata = json.loads(target.with_suffix(".prepare.json").read_text())
            self.assertEqual(len(metadata["audio_sha256"]), 64)
            before = target.read_bytes()
            with self.assertRaises(ValueError):
                prepare(source, target)
            self.assertEqual(target.read_bytes(), before)

    def test_real_video_audio_extraction(self):
        with tempfile.TemporaryDirectory() as temp:
            video, target = Path(temp) / "clip.mkv", Path(temp) / "clip.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "color=c=black:s=64x64:d=1", "-f", "lavfi", "-i",
                            "sine=frequency=440:duration=1", "-c:v", "ffv1",
                            "-c:a", "pcm_s16le", "-shortest", str(video)], check=True)
            prepare(video, target)
            self.assertAlmostEqual(wav_duration(target), 1, places=1)

    def test_bad_input_and_wrong_wav_format(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wav(root / "wrong.wav", 44100)
            with self.assertRaises(ValueError):
                wav_duration(root / "wrong.wav")
            (root / "bad.mp4").write_bytes(b"not a video")
            with self.assertRaisesRegex(ValueError, "FFmpeg failed"):
                prepare(root / "bad.mp4", root / "out.wav")
            self.assertFalse((root / "out.wav").exists())

    def test_whisper_call_contract_cpu_and_export(self):
        calls = {}
        class FakeModel:
            def transcribe(self, path, **kwargs):
                calls.update(kwargs)
                return {"segments": [{"start": 0, "end": 1, "text": "Xin chào"}]}
        def load_model(path, device):
            calls["device"] = device
            return FakeModel()
        fake_torch = types.SimpleNamespace(set_num_threads=lambda n: None,
                                           set_num_interop_threads=lambda n: None)
        fake_whisper = types.SimpleNamespace(load_model=load_model,
                                             tokenizer=types.SimpleNamespace(LANGUAGES={"vi": "vietnamese"}))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wav(root / "audio.wav")
            (root / "tiny.pt").touch()
            with patch.dict(sys.modules, {"torch": fake_torch, "whisper": fake_whisper}):
                transcribe(root / "audio.wav", root / "tiny.pt", "vi", 2, 5, root / "out")
            self.assertEqual(calls["device"], "cpu")
            self.assertFalse(calls["fp16"])
            self.assertEqual(calls["task"], "transcribe")
            self.assertEqual((root / "out/transcript.txt").read_text().strip(), "Xin chào")
            self.assertFalse(list(root.glob(".transcribing-*")))
            with self.assertRaises(ValueError):
                transcribe(root / "audio.wav", root / "tiny.pt", "vi", 2, 5, root / "out")

    def test_cli_failure_exit_code(self):
        result = subprocess.run([sys.executable, "-m", "subtitle_bench.cli", "prepare",
                                 "/tmp/no-such-lecture-input.mp4", "/tmp/no-such-output.wav"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Input not found", result.stderr)

    def test_completion_manifest_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            export_segments(root, [{"start": 0, "end": 1, "text": "Hello"}], {})
            result_manifest(root, {"device": "cpu"}, 1)
            self.assertEqual(verify_result(root)["audio_seconds"], 1)
            (root / "transcript.txt").write_text("changed")
            with self.assertRaisesRegex(ValueError, "integrity"):
                verify_result(root)

    def test_no_audio_video_fails_without_partial_wav(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "color=c=black:s=64x64:d=1", "-c:v", "ffv1", str(root / "silent.mkv")], check=True)
            with self.assertRaisesRegex(ValueError, "FFmpeg failed"):
                prepare(root / "silent.mkv", root / "out.wav")
            self.assertFalse((root / "out.wav").exists())
            self.assertFalse(list(root.glob(".preparing-*")))

    def test_cli_invalid_audio_is_clean_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "fake.wav").write_bytes(b"not wave")
            result = subprocess.run([sys.executable, "-m", "subtitle_bench.cli", "transcribe",
                                     "--audio", str(root / "fake.wav"), "--model", str(root / "tiny.pt"),
                                     "--language", "ko", "--output", str(root / "out")],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stderr)

    def test_truncated_wav_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "truncated.wav"
            wav(path)
            path.write_bytes(path.read_bytes()[:-100])
            with self.assertRaisesRegex(ValueError, "truncated"):
                wav_duration(path)

    def test_sidecar_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wav(root / "source.wav")
            (root / "out.prepare.json").write_text("existing")
            with self.assertRaises(ValueError):
                prepare(root / "source.wav", root / "out.wav")
            self.assertEqual((root / "out.prepare.json").read_text(), "existing")

    def test_export_failure_does_not_publish_completed_directory(self):
        class BadModel:
            def transcribe(self, *args, **kwargs):
                return {"segments": [{"start": 1, "end": -1, "text": "invalid"}]}
        torch = types.SimpleNamespace(set_num_threads=lambda n: None, set_num_interop_threads=lambda n: None)
        whisper = types.SimpleNamespace(load_model=lambda *a, **kw: BadModel(),
                                        tokenizer=types.SimpleNamespace(LANGUAGES={"en": "english"}))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wav(root / "audio.wav")
            (root / "tiny.pt").touch()
            with patch.dict(sys.modules, {"torch": torch, "whisper": whisper}):
                with self.assertRaises(ValueError):
                    transcribe(root / "audio.wav", root / "tiny.pt", "en", 2, 5, root / "out")
            self.assertFalse((root / "out").exists())
            self.assertFalse(list(root.glob(".transcribing-*")))

    def test_pipeline_cli_joins_real_ffmpeg_and_mock_whisper(self):
        from subtitle_bench.cli import main
        class Model:
            def transcribe(self, *args, **kwargs):
                return {"segments": [{"start": 0, "end": 1, "text": "integration speech"}]}
        torch = types.SimpleNamespace(set_num_threads=lambda n: None, set_num_interop_threads=lambda n: None)
        whisper = types.SimpleNamespace(load_model=lambda *a, **kw: Model(),
                                        tokenizer=types.SimpleNamespace(LANGUAGES={"en": "english"}))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wav(root / "source with spaces.wav", 44100, 2)
            (root / "tiny.pt").touch()
            argv = ["lecture-subtitles", "run", "--input", str(root / "source with spaces.wav"),
                    "--model", str(root / "tiny.pt"), "--language", "en", "--output", str(root / "run")]
            with patch.dict(sys.modules, {"torch": torch, "whisper": whisper}), patch.object(sys, "argv", argv):
                self.assertEqual(main(), 0)
            self.assertAlmostEqual(wav_duration(root / "run/audio.wav"), 1, places=2)
            self.assertEqual(verify_result(root / "run/whisper")["status"], "complete")
            self.assertTrue((root / "run/environment.json").exists())


if __name__ == "__main__":
    unittest.main()
