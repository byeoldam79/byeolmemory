---
name: voice-speaker
description: 안티그래비티 고품질 한국어 AI 음성(TTS) 연동 스킬. 에이전트의 답변을 스피커로 읽어주거나 인스타그램 영상용 나레이션 MP3 음성 파일을 생성할 때 사용합니다.
---

# 안티그래비티 고품질 한국어 AI 음성(TTS) 스킬

이 스킬은 Microsoft Edge-TTS(신경망 AI 보이스)를 사용하여 에이전트의 답변을 고품질 한국어 음성으로 출력하거나 MP3 파일로 생성합니다.

---

## 1. 지원 파일 및 모듈

- [`voice_speaker.py`](file:///e:/아린인스타그램에이전트/voice_speaker.py): 음성 합성 및 윈도우 스피커 재생 엔진
- [`speak.py`](file:///e:/아린인스타그램에이전트/speak.py): 한 줄 음성 출력 및 MP3 저장 CLI 도구

---

## 2. 주요 사용 방법

### 1) 한 줄 텍스트 스피커로 듣기
```bash
python speak.py "안녕하세요! 안티그래비티 음성 안내입니다."
```

### 2) 인스타그램 릴스/영상용 MP3 음성 파일 저장
```bash
python speak.py "인스타그램 릴스 나레이션 음성입니다." --save assets/narration.mp3
```
