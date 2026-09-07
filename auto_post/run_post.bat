@echo off
chcp 65001 > nul
cd /d "e:\아린인스타그램에이전트"
"C:\Users\qowhd\AppData\Local\Python\pythoncore-3.14-64\python.exe" "e:\아린인스타그램에이전트\auto_post\post_daily.py" >> "e:\아린인스타그램에이전트\auto_post\post_log.txt" 2>&1
