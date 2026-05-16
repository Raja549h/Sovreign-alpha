@echo off
REM Sovereign Alpha - Master Daily Pipeline
REM Runs every weekday at 08:45 IST

setlocal

cd /d "C:\Users\lokes\Downloads\project\sovereign-alpha"

set LOGFILE="C:\Users\lokes\Downloads\project\sovereign-alpha\automation\logs\master_daily_%%DATE:/=-%%.txt"

echo ======================================== >> %LOGFILE%
echo Master Daily Pipeline >> %LOGFILE%
echo Started: %%DATE%% %%TIME%% >> %LOGFILE%
echo ======================================== >> %LOGFILE%

"C:\Users\lokes\AppData\Local\Programs\Python\Python311\python.exe" automation\master_daily.py >> %LOGFILE% 2>&1

echo. >> %LOGFILE%
echo Completed: %%TIME%% >> %LOGFILE%
echo ======================================== >> %LOGFILE%

endlocal
