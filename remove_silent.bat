@echo off

call %~dp0\venv\Scripts\activate.bat

python %~dp0\remove_silent.py %*

call %~dp0\venv\Scripts\deactivate.bat

pause