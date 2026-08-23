"""
Windows 작업 스케줄러에 30분 주기 인스타그램 DM 모니터링 태스크 등록
"""
import subprocess
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

TASK_NAME = "MoveCounter_Instagram_DMMonitor"
BAT_PATH  = r"e:\아린인스타그램에이전트\dm_manager\run_dm_check.bat"

print("=" * 60)
print("📅 Windows 작업 스케줄러에 DM 모니터링 자동 등록 중...")
print("=" * 60)

# 매 30분마다 반복 실행하도록 등록 (/SC MINUTE /MO 30)
cmd = [
    "schtasks", "/Create",
    "/TN", TASK_NAME,
    "/TR", BAT_PATH,
    "/SC", "MINUTE",
    "/MO", "30",
    "/F"  # 이미 존재하는 경우 덮어쓰기
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"🎉 [성공] Task Scheduler 등록 완료!")
        print(f"  - 태스크명: {TASK_NAME}")
        print(f"  - 실행 주기: 매 30분마다 자동 실행")
        print(f"  - 실행 파일: {BAT_PATH}")
    else:
        print(f"❌ [에러] {result.stderr}")
except Exception as e:
    print(f"❌ [오류 발생] {e}")
