# Third-Party Sources and Licenses

This document covers the dependencies and sample asset used by Hung's FFmpeg and CPU Whisper component.

| Component | Purpose | License / Source |
|---|---|---|
| Whisper | Speech recognition | MIT — https://github.com/openai/whisper |
| FFmpeg | Audio extraction and conversion | LGPL/GPL, depending on the build — https://ffmpeg.org/legal.html |
| PyTorch | Runtime used by Whisper | BSD-style — https://github.com/pytorch/pytorch/blob/main/LICENSE |

The integration scripts use the upstream speech recognition implementation. Model weights are not included in this handoff.

The sample `jfk.flac` comes from the `tests/` directory of the official Whisper repository. The complete OpenAI MIT notice is retained in `examples/sample/WHISPER_LICENSE.txt`. The sample's source URL and SHA-256 hash are recorded in `examples/sample/source.json`.

Retain the applicable third-party licenses and notices when redistributing dependencies or assets. Run `ffmpeg -version` to inspect the installed build and its configuration. Transitive dependencies can be recorded in an environment lock file after installation.

The repository's MIT license in `LICENSE` applies to the integration code. Third-party components remain subject to their respective licenses.

## Reference

Radford et al., *Robust Speech Recognition via Large-Scale Weak Supervision*, ICML 2023.  
https://proceedings.mlr.press/v202/radford23a.html
