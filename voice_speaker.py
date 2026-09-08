"""
========================================================================================
[안티그래비티 음성 안내 시스템 - Voice Speaker Engine]
========================================================================================
이 모듈은 Microsoft Edge-TTS(신경망 인공지능 음성) 기술을 활용하여
원하는 텍스트를 아주 자연스럽고 유창한 한국어 목소리로 변환하고,
컴퓨터 스피커를 통해 즉시 재생해 주는 음성 합성 및 재생 엔진입니다.

★ 초보자를 위한 핵심 특징:
1. 무료 & 무제한: 별도의 유료 API 키 등록 없이 즉시 사용 가능합니다.
2. 초고음질 신경망 보이스: 기계적인 로봇 목소리가 아닌 실제 아나운서/성우 느낌의 자연스러운 음성을 제공합니다.
3. 윈도우 기본 사운드 엔진 연동: 무거운 외부 라이브러리 설치 없이 윈도우 시스템 자체 오디오 API로 안정적으로 재생합니다.
========================================================================================
"""

import asyncio
import ctypes
import os
import sys
import tempfile
import time
from typing import Optional

# 윈도우 터미널 한글/특수문자 인코딩 안전 설정
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    import edge_tts
except ImportError:
    print("[오류] edge-tts 패키지가 설치되어 있지 않습니다. 'pip install edge-tts'를 실행해 주세요.")
    sys.exit(1)


# ======================================================================================
# 1. 추천 목소리 목록 (한국어 대표 보이스)
# ======================================================================================
VOICES = {
    # 1) 선희 (Sun-Hi): 가장 인기 있는 여성 음성 (밝고 또렷하며 친절한 안내 톤)
    "선희": "ko-KR-SunHiNeural",
    "sunhi": "ko-KR-SunHiNeural",
    "female": "ko-KR-SunHiNeural",

    # 2) 인준 (In-Joon): 대표 남성 음성 (신뢰감 있고 차분한 톤)
    "인준": "ko-KR-InJoonNeural",
    "injoon": "ko-KR-InJoonNeural",
    "male": "ko-KR-InJoonNeural",

    # 3) 현수 (Hyun-su): 캐주얼하고 자연스러운 남성 대화 톤
    "현수": "ko-KR-HyunsuMultilingualNeural",
    "hyunsu": "ko-KR-HyunsuMultilingualNeural",
}

# 기본으로 사용할 대표 목소리 (선희)
DEFAULT_VOICE = "ko-KR-SunHiNeural"


# ======================================================================================
# 2. 윈도우 멀티미디어 사운드 재생 클래스 (Windows MCI Player)
# ======================================================================================
class WindowsAudioPlayer:
    """
    윈도우 내장 멀티미디어 API(winmm.dll)를 사용하여
    MP3 오디오 파일을 스피커로 지연 없이 깔끔하게 재생하는 플레이어입니다.
    """

    def __init__(self):
        # 윈도우 기본 멀티미디어 DLL 로드
        self.winmm = ctypes.windll.winmm

    def _send_command(self, command: str) -> int:
        """MCI 사운드 명령어를 윈도우 시스템으로 전송합니다."""
        buffer = ctypes.create_unicode_buffer(256)
        return self.winmm.mciSendStringW(command, buffer, len(buffer), None)

    def play_mp3(self, file_path: str, blocking: bool = True) -> bool:
        """
        MP3 오디오 파일을 재생합니다.

        :param file_path: 재생할 MP3 파일의 절대 경로
        :param blocking: True면 음성이 끝날 때까지 기다리고, False면 백그라운드에서 재생합니다.
        :return: 재생 성공 여부 (True/False)
        """
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            print(f"[경고] 오디오 파일을 찾을 수 없습니다: {abs_path}")
            return False

        # 고유한 오디오 별칭(alias) 생성 (동시 재생 충돌 방지)
        alias = f"ag_voice_{int(time.time() * 1000)}"

        try:
            # 1) 오디오 파일 열기
            open_cmd = f'open "{abs_path}" type mpegvideo alias {alias}'
            ret = self._send_command(open_cmd)
            if ret != 0:
                # mpegvideo 타입 실패 시 기본 자동 감지로 재시도
                ret = self._send_command(f'open "{abs_path}" alias {alias}')

            # 2) 오디오 재생 시작
            wait_flag = " wait" if blocking else ""
            play_cmd = f"play {alias}{wait_flag}"
            self._send_command(play_cmd)

            # 3) 재생이 끝났으면 리소스 닫기
            if blocking:
                self._send_command(f"close {alias}")

            return True
        except Exception as e:
            print(f"[오류] 오디오 재생 중 문제가 발생했습니다: {e}")
            try:
                self._send_command(f"close {alias}")
            except Exception:
                pass
            return False


# 플레이어 인스턴스 전역 생성
_player = WindowsAudioPlayer()


# ======================================================================================
# 3. 비동기 음성 생성 함수 (Edge-TTS)
# ======================================================================================
async def _generate_audio_async(
    text: str,
    output_path: str,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    pitch: str = "+0Hz"
) -> str:
    """
    Edge-TTS를 사용하여 텍스트를 오디오 파일로 저장하는 비동기 함수입니다.
    """
    # 사용자가 '선희', '인준' 등의 한글 별칭을 입력한 경우 정식 보이스 코드로 변환
    selected_voice = VOICES.get(voice.lower(), voice)

    # Edge-TTS 통신 객체 생성
    communicate = edge_tts.Communicate(
        text=text,
        voice=selected_voice,
        rate=rate,
        pitch=pitch
    )

    # 오디오 파일로 저장
    await communicate.save(output_path)
    return output_path


# ======================================================================================
# 4. 사용자가 직접 호출하는 메인 기능 함수들
# ======================================================================================
def speak(
    text: str,
    voice: str = "선희",
    rate: str = "+0%",
    pitch: str = "+0Hz",
    blocking: bool = True
) -> bool:
    """
    [핵심 기능] 전달받은 텍스트를 즉시 한국어 AI 음성으로 변환하여 스피커로 들려줍니다!

    :param text: 읽어줄 텍스트 내용 (예: "안녕하세요! 안티그래비티입니다.")
    :param voice: 목소리 종류 ('선희'(기본), '인준', '현수' 또는 'ko-KR-SunHiNeural' 등)
    :param rate: 말하는 속도 (예: "+0%", "+10%", "-10%")
    :param pitch: 음조 높낮이 (예: "+0Hz", "+5Hz", "-5Hz")
    :param blocking: 음성이 끝날 때까지 대기할지 여부 (기본값: True)
    :return: 성공 시 True, 실패 시 False
    """
    if not text or not text.strip():
        print("[안내] 읽을 텍스트가 비어 있습니다.")
        return False

    # 임시 MP3 파일 생성 경로
    temp_dir = tempfile.gettempdir()
    temp_mp3 = os.path.join(temp_dir, f"antigravity_tts_{int(time.time() * 1000)}.mp3")

    try:
        # 1) 텍스트 -> MP3 음성 파일 변환
        asyncio.run(_generate_audio_async(
            text=text,
            output_path=temp_mp3,
            voice=voice,
            rate=rate,
            pitch=pitch
        ))

        # 2) 스피커로 음성 재생
        success = _player.play_mp3(temp_mp3, blocking=blocking)
        return success

    except Exception as e:
        print(f"[오류] 음성 변환 및 재생 실패: {e}")
        return False

    finally:
        # 3) 사용이 끝난 임시 파일 안전하게 삭제
        if blocking and os.path.exists(temp_mp3):
            try:
                os.remove(temp_mp3)
            except Exception:
                pass


def save_voice_file(
    text: str,
    output_filename: str,
    voice: str = "선희",
    rate: str = "+0%",
    pitch: str = "+0Hz"
) -> Optional[str]:
    """
    전달받은 텍스트를 MP3 음성 파일로 저장합니다. (인스타그램 영상 나레이션 제작 등에 활용 가능)

    :param text: 변환할 텍스트
    :param output_filename: 저장할 파일 이름 (예: "narration.mp3")
    :param voice: 목소리 종류 ('선희', '인준' 등)
    :param rate: 속도
    :param pitch: 음조
    :return: 저장된 파일의 절대 경로
    """
    try:
        abs_output = os.path.abspath(output_filename)
        # 상위 폴더가 없으면 자동 생성
        parent_dir = os.path.dirname(abs_output)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        asyncio.run(_generate_audio_async(
            text=text,
            output_path=abs_output,
            voice=voice,
            rate=rate,
            pitch=pitch
        ))
        print(f"[성공] 음성 파일이 저장되었습니다: {abs_output}")
        return abs_output
    except Exception as e:
        print(f"[오류] 음성 파일 저장 실패: {e}")
        return None


def show_available_voices():
    """사용 가능한 대표 목소리 목록을 출력합니다."""
    print("\n=======================================================")
    print(" [안티그래비티 지원 음성(Voice) 목록]")
    print("=======================================================")
    print(" 1. '선희' (기본값) : 여성, 맑고 또렷한 표준 한국어 안내 톤")
    print(" 2. '인준'          : 남성, 차분하고 신뢰감 있는 뉴스/안내 톤")
    print(" 3. '현수'          : 남성, 부드럽고 자연스러운 대화 톤")
    print("=======================================================\n")


# 단독 실행 시 테스트
if __name__ == "__main__":
    print("[테스트] 안티그래비티 음성 안내 모듈 테스트를 시작합니다.")
    show_available_voices()

    test_text = "안녕하세요! 안티그래비티 음성 안내 시스템이 정상적으로 연결되었습니다."
    print(f"[음성 출력] '{test_text}'")
    speak(test_text, voice="선희")
    print("[완료] 테스트가 성공적으로 끝났습니다.")
