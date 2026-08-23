@echo off
chcp 65001 > nul
echo ========================================================
echo Google Calendar 1회 인증을 진행합니다.
echo 잠시 후 브라우저가 열리면 Google 계정으로 로그인해주세요!
echo ========================================================
cd /d "e:\아린인스타그램에이전트"
python auto_post\test_google_calendar.py
echo.
pause
