"""
Windows 작업 스케줄러에 매일 오후 7시 자동 포스팅 등록 스크립트 (무창 백그라운드 실행)
파일명: setup_scheduler.py
설명: 
  1. 인스타그램 자동 포스팅 배치 파일(run_post.bat)을 생성합니다.
  2. cmd 검은 창 깜빡임을 100% 방지하는 VBScript 무창 실행기(run_silent.vbs)를 생성합니다.
  3. Windows 작업 스케줄러에 매일 19:00에 실행되도록 wscript.exe를 통해 완전 숨김 모드로 등록합니다.
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
token = env.get('INSTAGRAM_ACCESS_TOKEN', '')
account_id = env.get('INSTAGRAM_ACCOUNT_ID', '37693295306982418')

# 1. run_post.bat 생성 (실제 포스팅 동작을 수행하는 배치 파일)
# chcp 65001을 통해 한글 인코딩을 보장하고 작업 디렉토리로 이동 후 파이썬을 실행합니다.
bat_content = f"""@echo off
chcp 65001 > nul
cd /d "{ROOT_DIR}"
set INSTAGRAM_ACCOUNT_ID={account_id}
set INSTAGRAM_ACCESS_TOKEN={token}
set GOOGLE_CALENDAR_ID=primary
"{PYTHON_EXE}" "{os.path.join(AUTO_POST_DIR, 'post_daily.py')}" >> "{LOG_PATH}" 2>&1
"""

with open(BAT_PATH, 'w', encoding='utf-8') as f:
    f.write(bat_content)
print(f"✅ [1/4] run_post.bat 배치 파일 생성 완료: {BAT_PATH}")

# 2. run_silent.vbs 생성 (cmd 검은 창 깜빡임을 100% 차단하는 무창 VBScript 실행기)
# WScript.Shell의 Run 메서드 두 번째 인자 '0'은 창을 화면에 전혀 표시하지 않는 Hide Window 모드입니다.
vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "{BAT_PATH}" & chr(34), 0, False
Set WshShell = Nothing
'''

with open(VBS_PATH, 'w', encoding='utf-8') as f:
    f.write(vbs_content)
print(f"✅ [2/4] run_silent.vbs 무창(Silent) 실행 스크립트 생성 완료: {VBS_PATH}")

# 3. PowerShell 스크립트를 통한 Windows 작업 스케줄러 등록
# cmd.exe 대신 Windows 내장 wscript.exe를 통해 vbs를 실행하여 검은 창 팝업을 완전히 없앱니다.
print("\n🔄 [3/4] Windows 작업 스케줄러 등록 중 (PowerShell 연동 - 무창 모드)...")

ps_script = f"""
$taskName = "{TASK_NAME}"
$wscriptPath = "C:\\Windows\\System32\\wscript.exe"
$vbsPath = "{VBS_PATH}"
$workDir = "{AUTO_POST_DIR}"

# 1. 기존 동일한 이름의 태스크가 있다면 안전하게 삭제
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# 2. 실행 동작 정의 (wscript.exe "run_silent.vbs", 시작 위치 지정)
$action = New-ScheduledTaskAction -Execute $wscriptPath -Argument "`"$vbsPath`"" -WorkingDirectory $workDir

# 3. 매일 19:00 트리거 설정
$trigger = New-ScheduledTaskTrigger -Daily -At "19:00"

# 4. 세부 설정 구성 (배터리 모드 실행 허용, 놓친 작업 즉시 시작 등)
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -WakeToRun `
    -MultipleInstances IgnoreNew `
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
        print(f"🎉 [성공] 작업 스케줄러 무창(Silent) 모드 등록 완료!")
        print(f"  - 태스크명: {TASK_NAME}")
        print(f"  - 실행 방식: wscript.exe -> run_silent.vbs (cmd 창 절대 안 뜸)")
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
