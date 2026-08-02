@echo off
setlocal
set "HERE=%~dp0.."
set "ROOT=%HERE%\.."
set "PYTHONPATH=%HERE%\toolkit;%PYTHONPATH%"
"%ROOT%\.venv\Scripts\python.exe" -m rag_toolkit.cli --rag-dir "%HERE%" %*
