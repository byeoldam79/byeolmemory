"""
========================================================================================
[안티그래비티 원클릭 음성 실행 도구 - speak.py]
========================================================================================
터미널이나 명령 프롬프트(CMD, PowerShell)에서 원하는 문장을 입력하면
즉시 한국어 AI 음성으로 읽어주거나 파일로 저장해 주는 간편 실행 스크립트입니다.

★ 사용 예시:
  1) 기본 실행 (여성 목소리 선희):
     python speak.py "안녕하세요! 반갑습니다."

  2) 남성 목소리(인준)로 실행:
     python speak.py "반갑습니다." --voice 인준

  3) 속도를 10퍼센트 빠르게 읽기:
     python speak.py "빠르게 읽어드립니다." --rate +10%

  4) MP3 음성 파일로 저장하기:
     python speak.py "인스타그램 릴스 나레이션입니다." --save assets/narration.mp3
========================================================================================
"""

import argparse
import sys

# 윈도우 터미널 인코딩 설정
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from voice_speaker import speak, save_voice_file, show_available_voices


def main():
    # 명령행 인자(Argument) 파서 구성
    parser = argparse.ArgumentParser(
        description="안티그래비티 고품질 한국어 AI 음성(TTS) 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python speak.py "오늘도 좋은 하루 보내세요!"
  python speak.py "차분한 남성 목소리입니다." --voice 인준
  python speak.py "인스타그램 릴스 음성" --save assets/my_voice.mp3
        """
    )

    # 읽을 텍스트 (위치 인자)
    parser.add_argument(
        "text",
        nargs="?",
        default="",
        help="음성으로 읽어줄 텍스트 내용"
    )

    # 목소리 선택
    parser.add_argument(
        "--voice", "-v",
        default="선희",
        help="목소리 선택: '선희'(기본/여성), '인준'(남성), '현수'(남성)"
    )

    # 말하기 속도 (argparse에서 %는 %%로 이스케이프)
    parser.add_argument(
        "--rate", "-r",
        default="+0%",
        help="말하기 속도 조절 (예: +10%%, +20%%, -10%%, 기본값: +0%%)"
    )

    # 음조 (피치)
    parser.add_argument(
        "--pitch", "-p",
        default="+0Hz",
        help="음조 높낮이 조절 (예: +5Hz, -5Hz, 기본값: +0Hz)"
    )

    # 파일 저장 옵션
    parser.add_argument(
        "--save", "-s",
        metavar="FILE_PATH",
        help="음성을 재생하지 않고 지정한 MP3 파일 경로로 저장"
    )

    # 지원 음성 목록 보기 옵션
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="사용 가능한 지원 목소리 목록 출력"
    )

    args = parser.parse_args()

    # 지원 목소리 목록 조회 요청 시
    if args.list_voices:
        show_available_voices()
        return

    # 텍스트가 없는 경우 안내 후 종료
    if not args.text.strip():
        print("[안내] 읽을 텍스트를 입력해 주세요.")
        print("사용법: python speak.py \"읽고 싶은 문장\"")
        print("도움말: python speak.py --help")
        return

    # 파일 저장 모드인 경우
    if args.save:
        print(f"[진행] 음성을 '{args.save}' 파일로 생성 중...")
        saved_path = save_voice_file(
            text=args.text,
            output_filename=args.save,
            voice=args.voice,
            rate=args.rate,
            pitch=args.pitch
        )
        if saved_path:
            print(f"[완료] 성공적으로 파일이 생성되었습니다 -> {saved_path}")
        else:
            print("[실패] 파일 생성에 실패했습니다.")
    # 기본 스피커 재생 모드인 경우
    else:
        print(f"[음성 출력 ({args.voice})] \"{args.text}\"")
        success = speak(
            text=args.text,
            voice=args.voice,
            rate=args.rate,
            pitch=args.pitch,
            blocking=True
        )
        if success:
            print("[완료] 음성 출력이 완료되었습니다.")
        else:
            print("[오류] 음성 출력 중 문제가 발생했습니다.")


if __name__ == "__main__":
    main()
