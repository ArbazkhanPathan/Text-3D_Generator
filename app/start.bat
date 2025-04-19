@echo off

REM Start the Openfabric servers
call start_sh_server.bat
call start_code_server.bat

REM Run the ignite script
python ignite.py

REM Infinite loop to keep it running
:loop
timeout /t 60 >nul
goto loop
