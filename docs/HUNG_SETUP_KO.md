# 레꽝흥 담당 부분: FFmpeg + Whisper CPU

이 문서는 팀 저장소에 추가되는 개인 구성요소의 설치/실행 방법이다.
기존 benchmark.py와 requirements.txt는 이 변경에서 수정하지 않는다.
측정/WER/CSV는 팀원과 별도 통합한다. 모델 가중치는 Git에 포함하지 않는다.

## Ubuntu / WSL Ubuntu 설치

저장소 최상위에서 실행한다. Python 3.11 또는 3.12를 권장한다.

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e .
python -m unittest discover -s tests -v
```

위 명령은 Whisper 구성요소 설치용이다. 전체 프로젝트 requirements는 팀원이 검토 후 통합한다.
Windows VS Code는 코드 편집/commit에 사용할 수 있으나 Linux 실행 검증에는 WSL Ubuntu를 사용한다.

## 실제 모델 확인

```bash
lecture-subtitles fetch-model --model tiny --directory models
python scripts/acceptance.py --model models/tiny.pt --output results/local/acceptance-01
```

examples/sample/jfk.flac는 upstream Whisper의 영어 테스트 음성이다. source.json과 MIT notice를 포함한다.
이 명령은 실제 checkpoint를 사용하며, 출력과 hash를 확인하고 빈 transcript를 실패로 처리한다.
기술 acceptance 외에 음성 내용과 자막 시간은 사람이 직접 확인해야 한다. 실행마다 새 output 경로를 사용한다.

## 본인 영상으로 실행

```bash
lecture-subtitles run --input data/lecture01.mp4 --model models/tiny.pt --language ko --threads 4 --beam-size 5 --output results/local/lecture01
lecture-subtitles verify results/local/lecture01/whisper
```

`data/lecture01.mp4`는 직접 준비한 사용 가능한 강의 영상이다. 처음에는 짧은 구간으로 시험한다.
`ko`는 한국어, `vi`는 베트남어, `en`은 영어이다.
결과 폴더에는 audio.wav와 환경 정보, whisper/ 안에 TXT/SRT/JSON/result.json이 생성된다.

## 측정 프로그램 연결

```bash
lecture-subtitles prepare data/lecture01.mp4 data/lecture01.wav
python examples/partner_adapter.py --audio data/lecture01.wav --model models/tiny.pt --language ko --threads 4 --beam-size 5 --output results/local/whisper-run01
```

partner_adapter.py의 subprocess 실행 부분 주위에서 측정한 뒤 transcript.txt로 WER을 계산한다.
새 프로세스의 시작/import/검증/모델 로드/인식/hash/출력을 포함하므로 순수 inference 시간은 아니다.
모델 다운로드와 FFmpeg를 측정에 포함하지 않는다. 자세한 입력/출력 규약은 HUNG_CONTRACT.md를 참조한다.

## 확인된 것과 아직 확인하지 못한 것

2026-11-10 준비 환경(Debian Linux)에서 13개 기술 테스트가 통과하였다.
FFmpeg는 실제로 실행하였으며, Whisper 호출은 테스트에서 모의 객체를 사용하였다.
공식 checkpoint 다운로드는 준비 환경 proxy가 HTTP 403으로 차단하여 pretrained 인식은 아직 미검증이다.
모델을 받을 수 있는 팀 환경에서 acceptance를 실행한 후 실제 인식 성공을 보고한다.
이 구성요소는 AI 지원으로 준비되었다. 각자 코드 이해, 실행 및 수정 이력을 실제 활동대로 남긴다.
