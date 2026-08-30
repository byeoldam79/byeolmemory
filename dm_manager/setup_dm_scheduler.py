"""
Windows 작업 스케줄러에 30분 주기 인스타그램 DM 모니터링 태스크 등록 (무창 백그라운드 실행)
파일명: setup_dm_scheduler.py
설명:
  - 검은색 cmd 창 깜빡임 없이 조용히 백그라운드에서 실행되도록 VBScript(run_silent_dm.vbs)를 생성하고 등록합니다.
"""
import subprocess
import sys
import os

# 콘솔 출력 한글 인코딩 설정 (UTF-8)
sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"e:\아린인스타그램에이전트"
DM_DIR = os.path.join(ROOT_DIR, "dm_manager")
BAT_PATH = os.path.join(DM_DIR, "run_dm_check.bat")
VBS_PATH = os.path.join(DM_DIR, "run_silent_dm.vbs")
TASK_NAME = "MoveCounter_Instagram_DMMonitor"

print("=" * 60)
print("📅 Windows 작업 스케줄러에 DM 모니터링 자동 등록 중 (무창 모드)...")
print("=" * 60)

# 1. run_silent_dm.vbs 무창 실행기 생성 (창 숨김 모드 '0')
vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "{BAT_PATH}" & chr(34), 0, False
Set WshShell = Nothing
'''

with open(VBS_PATH, 'w', encoding='utf-8') as f:
    f.write(vbs_content)
print(f"✅ [1/2] run_silent_dm.vbs 무창 실행 스크립트 생성 완료: {VBS_PATH}")

# 2. PowerShell을 통한 작업 스케줄러 등록 (30분 주기, wscript.exe 실행)
ps_script = f"""
$taskName = "{TASK_NAME}"
$wscriptPath = "C:\\Windows\\System32\\wscript.exe"
$vbsPath = "{VBS_PATH}"
$workDir = "{DM_DIR}"

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction -Execute $wscriptPath -Argument "`"$vbsPath`"" -WorkingDirectory $workDir

# 30분 주기 트리거 설정 (하루 종일 무한 반복)
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Minutes 30)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

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
        print(f"🎉 [2/2] Task Scheduler 무창 모드 등록 완료!")
        print(f"  - 태스크명: {TASK_NAME}")
        print(f"  - 실행 방식: wscript.exe (cmd 창 절대 안 뜸)")
        print(f"  - 실행 주기: 30분마다 조용히 백그라운드 체크")
    else:
        print(f"❌ [에러] {result.stderr}")
except Exception as e:
    print(f"❌ [오류 발생] {e}")

