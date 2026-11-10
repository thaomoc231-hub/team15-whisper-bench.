# Upstream speech sample

jfk.flac is the English speech fixture from OpenAI Whisper's tests. Source, SHA-256 and download date
are in source.json. The upstream MIT notice is preserved in WHISPER_LICENSE.txt.
Use --language en for this sample. It is a technical smoke-test input, not the team's lecture dataset.
No pretrained transcription is supplied or claimed. The source URL tracks main; the bundled file is
identified by its SHA-256. To run after downloading tiny:

```bash
python scripts/acceptance.py --model models/tiny.pt --output results/local/acceptance-01
```
