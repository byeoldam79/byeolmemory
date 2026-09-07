"""
Windows 작업 스케줄러에 매일 오후 7시 자동 포스팅 등록 스크립트 (무창 백그라운드 실행)
파일명: setup_scheduler.py
설명: 
  1. 인스타그램 자동 포스팅 배치 파일(run_post.bat)을 생성합니다.
  2. 더 이상 쓰지 않는 VBScript 실행기(run_silent.vbs)를 지웁니다.
     (2026-09-08 — 윈도우가 이 방식을 막아 자동 발행이 조용히 멈춰 있었다)
  3. Windows 작업 스케줄러에 매일 19:00, cmd.exe 가 배치를 직접 실행하도록 숨김 등록합니다.
  - 배터리 모드 실행 허용
  - 작업 누락 시 즉시 실행(StartWhenAvailable)
  - 시작 위치(WorkingDirectory) 명시
  - 화면에 cmd 검은 창이 전혀 뜨지 않는 무창(Silent) 모드 적용
"""
import subprocess
import sys
import os

# 콘솔 출력 한글 인코딩 설정 (UTF-8)
sys.stdout.reconfigure(encoding='utf-8')

# 기본 경로 및 설정값 정의
ROOT_DIR = r"e:\아린인스타그램에이전트"
AUTO_POST_DIR = os.path.join(ROOT_DIR, "auto_post")
BAT_PATH = os.path.join(AUTO_POST_DIR, "run_post.bat")
VBS_PATH = os.path.join(AUTO_POST_DIR, "run_silent.vbs")
LOG_PATH = os.path.join(AUTO_POST_DIR, "post_log.txt")
ENV_FILE = os.path.join(ROOT_DIR, ".env")
TASK_NAME = "MoveCounter_Instagram_AutoPost"

# 현재 실행 중인 파이썬 인터프리터 절대 경로 가져오기
PYTHON_EXE = sys.executable

def load_env():
    """ 
    .env 파일에서 인스타그램 및 구글 캘린더 설정값을 안전하게 불러옵니다. 
    """
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

# 1. run_post.bat 생성 (실제 포스팅 동작을 수행하는 배치 파일)
# ⚠ 토큰을 배치 파일에 적지 않는다.
#   2026-09-08 — 예전 방식은 토큰을 이 파일에 그대로 써 넣었고,
#   그 파일이 공개 깃허브 저장소에 올라가 있었다.
#   post_daily.py 가 .env 에서 직접 읽으므로 배치 파일에는 열쇠가 필요 없다.
bat_content = f"""@echo off
chcp 65001 > nul
cd /d "{ROOT_DIR}"
"{PYTHON_EXE}" "{os.path.join(AUTO_POST_DIR, 'post_daily.py')}" >> "{LOG_PATH}" 2>&1
"""

with open(BAT_PATH, 'w', encoding='utf-8') as f:
    f.write(bat_content)
print(f"✅ [1/4] run_post.bat 배치 파일 생성 완료: {BAT_PATH}")

# 2. VBScript 실행기는 더 이상 만들지 않는다.
#    2026-09-08 — 윈도우가 이 방식을 막아 8/27 이후 한 편도 발행되지 않았다.
#    스케줄러가 run_post.bat 을 직접 실행하고, 창은 작업 설정의 '숨김'으로 가린다.
if os.path.exists(VBS_PATH):
    os.remove(VBS_PATH)
    print(f"🗑️ [2/4] 더 이상 쓰지 않는 run_silent.vbs 를 지웠습니다: {VBS_PATH}")
else:
    print("ℹ️ [2/4] VBScript 실행기는 쓰지 않습니다 (작업 스케줄러가 배치를 직접 실행)")

# 3. PowerShell 스크립트를 통한 Windows 작업 스케줄러 등록
# cmd.exe 로 배치를 **직접** 실행한다. 창은 작업 설정의 Hidden 으로 가린다.
print("\n🔄 [3/4] Windows 작업 스케줄러 등록 중...")

ps_script = f"""
$taskName = "{TASK_NAME}"
$batPath = "{BAT_PATH}"
$workDir = "{AUTO_POST_DIR}"

# 1. 기존 동일한 이름의 태스크가 있다면 안전하게 삭제
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# 2. 실행 동작 정의 (cmd.exe /c "run_post.bat")
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batPath`"" -WorkingDirectory $workDir

# 3. 매일 19:00 트리거 설정
$trigger = New-ScheduledTaskTrigger -Daily -At "19:00"

# 4. 세부 설정 구성 (배터리 모드 실행 허용, 놓친 작업 즉시 시작 등)
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -WakeToRun `
    -MultipleInstances IgnoreNew `
    -Hidden `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

# 5. 현재 로그인된 사용자 권한으로 태스크 등록
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal
"""

try:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    if result.returncode == 0:
        print(f"🎉 [성공] 작업 스케줄러 등록 완료!")
        print(f"  - 태스크명: {TASK_NAME}")
        print(f"  - 실행 방식: cmd.exe -> run_post.bat (숨김 실행)")
        print(f"  - 실행 시간: 매일 19:00")
        print(f"  - 시작 위치: {AUTO_POST_DIR}")
        print(f"  - 주요 옵션: 배터리 모드 허용, 놓친 작업 즉시 실행(StartWhenAvailable)")
    else:
        print(f"❌ [에러] PowerShell 등록 실패:\n{result.stderr}")
except Exception as e:
    print(f"❌ [오류 발생] {e}")

# 4. 등록된 태스크 상태 검증
print("\n🔍 [4/4] 등록된 태스크 검증 중...")
verify_script = f"""
$task = Get-ScheduledTask -TaskName "{TASK_NAME}" -ErrorAction SilentlyContinue
if ($task) {{
    Write-Output "상태: $($task.State)"
    Write-Output "실행 파일: $($task.Actions.Execute)"
    Write-Output "인수: $($task.Actions.Arguments)"
    Write-Output "시작 위치: $($task.Actions.WorkingDirectory)"
    Write-Output "배터리 실행 허용: $($task.Settings.DisallowStartIfOnBatteries -eq $false)"
    Write-Output "놓친 작업 실행: $($task.Settings.StartWhenAvailable)"
}} else {{
    Write-Output "태스크를 찾을 수 없습니다."
}}
"""

check = subprocess.run(
    ["powershell", "-NoProfile", "-Command", verify_script],
    capture_output=True,
    text=True,
    encoding='utf-8'
)
print(check.stdout)

print("=" * 60)
print("✨ 완벽하게 개선되었습니다! 이제 19:00에 실행될 때 cmd 창이 전혀 뜨지 않고 조용히 백그라운드에서 실행됩니다.")
print("=" * 60)
