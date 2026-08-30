@echo off
chcp 65001 > nul
cd /d "e:\아린인스타그램에이전트"
set INSTAGRAM_ACCOUNT_ID=37693295306982418
set INSTAGRAM_ACCESS_TOKEN=IGAAV9pOJr7jdBZAGJJemVob2lIQVBVYU4tYVFmSDVuZA0p4dTdwenFNWkp6TjhDaUI0UWpDdXBtZA3NqMkl3N055MGh5SW9JN1NWMmdPc3R5MHBnVjhpcW5iQWExeURNVXhwdVdGaU9KNWZARVmQ3X0MwMlVaUXdUeS1UaVQtdkY2QQZDZD
set GOOGLE_CALENDAR_ID=primary
"C:\Users\qowhd\AppData\Local\Python\pythoncore-3.14-64\python.exe" "e:\아린인스타그램에이전트\auto_post\post_daily.py" >> "e:\아린인스타그램에이전트\auto_post\post_log.txt" 2>&1
