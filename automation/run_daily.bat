@echo off
REM Sovereign Alpha - Daily Cycle Automation
REM This file runs automatically via Windows Task Scheduler

setlocal

REM Set working directory
cd /d "C:\Users\lokes\Downloads\project\sovereign-alpha"

REM Set log file with date
set LOGFILE="C:\Users\lokes\Downloads\project\sovereign-alpha\automation\logs\daily_log_%DATE:/=-%.txt"

echo ======================================== >> %LOGFILE%
echo Sovereign Alpha Daily Cycle >> %LOGFILE%
echo Started: %DATE% %TIME% >> %LOGFILE%
echo ======================================== >> %LOGFILE%

REM Run daily cycle
"C:\Users\lokes\AppData\Local\Programs\Python\Python311\python.exe" operations\daily_cycle.py >> %LOGFILE% 2>&1

echo. >> %LOGFILE%
echo Daily cycle completed: %TIME% >> %LOGFILE%

REM Run outcome tracker
"C:\Users\lokes\AppData\Local\Programs\Python\Python311\python.exe" automation\outcome_tracker.py >> %LOGFILE% 2>&1

echo Outcome tracking completed: %TIME% >> %LOGFILE%

REM Run email digest (if configured)
"C:\Users\lokes\AppData\Local\Programs\Python\Python311\python.exe" automation\email_digest.py >> %LOGFILE% 2>&1

echo Email digest sent: %TIME% >> %LOGFILE%

REM Git sync
cd /d "C:\Users\lokes\Downloads\project\sovereign-alpha"
git add backtesting/historical_data/ backtesting/checkpoints/ billing/fund_data.db >> %LOGFILE% 2>&1
git commit -m "Daily cycle %DATE% automated" >> %LOGFILE% 2>&1
git push origin main >> %LOGFILE% 2>&1

echo Git sync completed: %TIME% >> %LOGFILE%

echo ======================================== >> %LOGFILE%
echo All tasks completed >> %LOGFILE%
echo ======================================== >> %LOGFILE%

endlocal
