"""
Windows 작업 스케줄러에 매일 오후 7시 자동 포스팅 등록
post_setup.py
"""
import subprocess
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_PATH = r"e:\\아린인스타그램에이전트\\auto_post\\run_post.bat"
TASK_NAME = "MoveCounter_Instagram_AutoPost"

# .env 파일에서 토큰 로드
ENV_FILE = r"e:\\아린인스타그램에이전트\\.env"

def load_env():
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()
    return env

env = load_env()
token = env.get('INSTAGRAM_ACCESS_TOKEN', '')
account_id = env.get('INSTAGRAM_ACCOUNT_ID', '')

# run_post.bat 생성 (Task Scheduler가 실행할 bat 파일)
bat_content = f"""@echo off
cd /d e:\\아린인스타그램에이전트
set INSTAGRAM_ACCOUNT_ID={account_id}
set INSTAGRAM_ACCESS_TOKEN={token}
set GOOGLE_CALENDAR_ID=primary
python auto_post\\post_daily.py >> auto_post\\post_log.txt 2>&1
"""

bat_path = r"e:\\아린인스타그램에이전트\\auto_post\\run_post.bat"
with open(bat_path, 'w', encoding='utf-8') as f:
    f.write(bat_content)
print(f"[OK] run_post.bat 생성 완료: {bat_path}")

# Windows Task Scheduler 등록 (schtasks 명령어 사용)
# 매일 19:00 KST 실행
print("\n[*] Task Scheduler 등록 중...")

cmd = [
    "schtasks", "/Create",
    "/TN", TASK_NAME,
    "/TR", bat_path,
    "/SC", "DAILY",
    "/ST", "19:00",
    "/F"  # 동일한 이름 존재 시 덮어쓰기
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[SUCCESS] Task Scheduler 등록 완료!")
        print(f"  태스크명: {TASK_NAME}")
        print(f"  실행 시간: 매일 19:00")
        print(f"  실행 파일: {bat_path}")
    else:
        print(f"[ERROR] {result.stderr}")
except Exception as e:
    print(f"[ERROR] {e}")

# 등록된 태스크 확인
print("\n[*] 등록된 태스크 확인 중...")
check = subprocess.run(
    ["schtasks", "/Query", "/TN", TASK_NAME, "/FO", "LIST"],
    capture_output=True, text=True, encoding='cp949'
)
print(check.stdout)

print("\n[DONE] 설정 완료!")
print(f"  내일부터 매일 오후 7시에 @bdai_79 인스타그램에 자동으로 포스팅됩니다!")
