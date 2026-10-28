@echo off
rem Shortcut: cf <command>  ==  .venv python -m clipfactory <command>  (Windows cmd / PowerShell)
setlocal
pushd "%~dp0"
if exist .venv\Scripts\python.exe (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
"%PY%" -m clipfactory %*
set "RC=%ERRORLEVEL%"
popd
exit /b %RC%
