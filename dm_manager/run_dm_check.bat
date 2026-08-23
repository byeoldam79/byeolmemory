@echo off
chcp 65001 > nul
cd /d "e:\아린인스타그램에이전트"
python dm_manager\dm_monitor.py >> dm_manager\dm_monitor.log 2>&1
