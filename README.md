# Linux CPU 환경에서의 Whisper vs faster-whisper 성능 비교 및 자동 자막 생성 도구

##  프로젝트 소개 (Project Overview)
본 프로젝트는 GPU가 없는 일반 PC(Linux CPU 환경)에서 강의 영상의 자동 자막 생성 도구인 **OpenAI Whisper**와 **faster-whisper**의 성능을 비교 분석하는 벤치마크 도구입니다.

동일한 강의 음성 데이터 및 조건에서 두 도구의 **처리 시간(Execution Time)**, **최대 RAM 사용량(Peak RAM)**, **단어 오류율(WER, Word Error Rate)**을 측정하고 결과를 CSV 파일로 저장합니다.

---

##  팀원 및 역할 (Team Members)
- **과목**: 오픈소스기초설계 (03분반) - 15조
- **팀원**:
  - **응웬 티 후에**: 측정 프로그램 및 CSV 저장 개발, WER 계산(Ground Truth 작성), README 작성
  - **레꽝흥**: FFmpeg 음성 추출 및 Whisper 실행 스크립트 작성

---

##  주요 기능 (Key Features)
1. **FFmpeg 음성 추출**: 강의 영상(MP4)에서 동일한 오디오(WAV/MP3) 추출
2. **STT 자막 생성**: Whisper 및 faster-whisper(CTranslate2) 기반 자막 추출
3. **성능 측정 (Benchmark)**:
   - 처리 시간 (Execution Time) 측정
   - Peak RAM 사용량 측정 (`psutil` / `/usr/bin/time -v`)
   - 정답 문장과 비교하여 WER (Word Error Rate) 계산 (`jiwer`)
4. **결과 저장**: 측정 데이터 `results.csv` 자동 저장

---

##  (Getting Started)

### 1. Prerequisites 
- OS: Ubuntu Linux (64-bit)
- Python 3.10+
- FFmpeg

```bash
sudo apt update
sudo apt install ffmpeg# team15-whisper-bench.
