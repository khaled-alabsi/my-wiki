@echo off
setlocal
set "HERE=%~dp0.."
set "PYTHONPATH=%HERE%\toolkit;%PYTHONPATH%"
"/Users/Khaled.Alabsi/.local/share/rag/my-wiki/venv/Scripts/python.exe" -m rag_toolkit.cli --rag-dir "%HERE%" %*
